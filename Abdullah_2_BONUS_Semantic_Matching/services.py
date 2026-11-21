"""Public interface of the Matching Orchestration module (AI feature 2, required). OWNER: matching.

Flow (Section 9.2 and Figure 7.14):
1. hard rules in SQL: published, eligible state, unreserved >= requested, same category subtree, not the
   requester's own unit
2. similarity from EmbeddingIndex (pgvector cosine) for the remaining assets
3. compute f1..f8, MatchingEngine.rank -> top results with score and one-line reason
4. supersede the previous MatchResultSet and save the new one with the input snapshot hash
Fallback when the index or model is unavailable: keyword search results labelled 'not ranked' (UC-26 E1).
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.utils.translation import gettext_lazy as _l
from pgvector.django import CosineDistance

from apps.access.models import User
from apps.access.permissions import users_who_can
from apps.audit.services import record
from apps.ai.models import AICapability, AIInferenceRecord, AIOutcome, ModelStatus, ModelVersion
from apps.catalogue.models import Asset, Category
from apps.catalogue.services import published, search
from apps.common.enums import UserDecision
from apps.common.errors import Forbidden, ValidationFailed
from apps.notifications.models import NotificationType
from apps.notifications.services import Msg, enqueue
from apps.resource_requests.models import RequestStatus, ResourceRequest

from .embeddings import get_embedder
from .engine import DEFAULT_WEIGHTS, HIGH_URGENCY_WEIGHTS, MatchingEngine, Need, Ranked
from .models import (SUITABLE_SCORE, WEAK_SCORE, EmbeddedKind, EmbeddingIndex, MatchRecommendation,
                     MatchResultSet, ResultSetStatus)

log = logging.getLogger(__name__)
MAX_RESULTS = 8          # suitable + weak kept per result set
MAX_CANDIDATES = 200     # nearest assets considered after the hard rules
NOT_SUITABLE_REASONS = ["wrong size or specs", "too far away", "condition too poor", "not what I meant", "already found one"]


# ----------------------------------------------------------------------------- model versions

def _active(capability: str, model_name: str, version: str, config: dict) -> ModelVersion:
    """The active ModelVersion for this capability; a new row is created when the model or config changes,
    so every stored score can be traced to the exact settings that produced it (Section 9.4)."""
    mv = ModelVersion.objects.filter(capability=capability, status=ModelStatus.ACTIVE).first()
    if mv and mv.model_name == model_name and mv.config == config:
        return mv
    mv = ModelVersion.objects.create(capability=capability, provider="local", model_name=model_name, version=version,
                                     confidence_scale="0-1", config=config)
    mv.activate()
    return mv


def embed_model() -> ModelVersion:
    e = get_embedder()
    return _active(AICapability.EMBED, e.model_name, f"emb-{e.name}", {"backend": e.name, "dim": 384})


def rank_model() -> ModelVersion:
    e = get_embedder()
    return _active(AICapability.RANK, "circular-campus-ranker", "rank-1.0",
                   {"weights": DEFAULT_WEIGHTS, "high_urgency_weights": HIGH_URGENCY_WEIGHTS, "embedder": e.name,
                    "suitable": SUITABLE_SCORE, "weak": WEAK_SCORE})


# ----------------------------------------------------------------------------- embeddings

def asset_text(a: Asset) -> str:
    tags = " ".join(t.tag_text for t in a.tags.all()) if hasattr(a, "tags") else ""
    return " ".join(filter(None, [a.name, a.category.name, a.category.name_ar, a.description, a.specifications, tags]))


def request_text(r: ResourceRequest) -> str:
    return " ".join(filter(None, [r.purpose, r.specifications, r.category.name, r.category.name_ar]))


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ensure_asset_embeddings(assets, mv: ModelVersion | None = None) -> int:
    """Embed the assets whose text changed or that were embedded by another model. Returns how many."""
    mv = mv or embed_model()
    assets = list(assets)
    have = {e.object_id: e for e in EmbeddingIndex.objects.filter(kind=EmbeddedKind.ASSET, object_id__in=[a.pk for a in assets])}
    todo = []
    for a in assets:
        text = asset_text(a)
        h = _hash(text)
        e = have.get(a.pk)
        if e is None or e.text_hash != h or e.model_version_id != mv.pk:
            todo.append((a, text, h))
    if not todo:
        return 0
    vectors = get_embedder().embed([t for _, t, _ in todo])
    for (a, _, h), vec in zip(todo, vectors):
        EmbeddingIndex.objects.update_or_create(kind=EmbeddedKind.ASSET, object_id=a.pk,
                                                defaults={"embedding": vec, "text_hash": h, "model_version": mv})
    return len(todo)


def embed_pending(limit: int = 50) -> int:
    """Worker job: (re)compute embeddings for published assets whose text changed. Returns how many."""
    qs = published().select_related("category").prefetch_related("tags").order_by("-updated_at")[:limit * 4]
    return ensure_asset_embeddings(qs)


# ----------------------------------------------------------------------------- the main flow

def need_from_request(r: ResourceRequest) -> Need:
    return Need(text=request_text(r), specs=r.specifications, quantity=r.quantity, preferred_condition=r.preferred_condition,
                urgency=r.urgency, campus=r.destination_campus, building=r.destination_building, required_date=r.required_date)


def need_from_text(text: str, user: User, quantity: int = 1) -> Need:
    d = user.department
    return Need(text=text, quantity=max(1, quantity), campus=(d.campus if d else "") or "", building=(d.building if d else "") or "")


def _hard_rules(need: Need, category: Category | None, exclude_unit_id, allow_partial: bool = False):
    """Section 9.2 step 1. Everything that does not pass these never gets a score.
    `allow_partial` (procurement check only): items with at least one free unit pass, and f8 + a note say how short."""
    qs = (published().filter(available_quantity__gte=F("reserved_quantity") + (1 if allow_partial else need.quantity))
          .select_related("category", "owner_department").prefetch_related("tags"))
    if category is not None:
        qs = qs.filter(category_id__in=category.descendant_ids())
    if exclude_unit_id:
        qs = qs.exclude(owner_department_id=exclude_unit_id)
    return qs


def _emission_kg(category: Category) -> Decimal | None:
    """Most specific locally selected carbon factor for this category or a parent (BR-15). None if none."""
    from apps.sustainability.services import factor_for  # one lookup rule for matching and the dashboard
    f = factor_for(category)
    return f.kg_co2e_per_unit if f else None


def _turned_down(user, request, query_text: str) -> list:
    """Items this person already marked 'Not for me' for the same request or the same words: not shown again."""
    rejected = MatchRecommendation.objects.filter(user_decision=UserDecision.REJECTED)
    if request is not None:
        rejected = rejected.filter(result_set__request=request)
    elif getattr(user, "pk", None):
        rejected = rejected.filter(result_set__request__isnull=True, result_set__generated_by=user,
                                   result_set__query_text__iexact=query_text.strip())
    else:
        return []
    return list(rejected.values_list("asset_id", flat=True).distinct())


def _snapshot(need: Need, assets, mv_rank: ModelVersion) -> str:
    data = {"need": need.__dict__, "assets": sorted(f"{a.pk}:{a.row_version}" for a in assets), "model": str(mv_rank.pk)}
    return "sha256:" + hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()[:40]


@dataclass
class Outcome:
    """What the screens get back. `ranked` is False when the keyword fallback was used (UC-26 E1)."""

    result_set: MatchResultSet | None
    suitable: list = field(default_factory=list)
    weak: list = field(default_factory=list)
    ranked: bool = True
    fallback: list = field(default_factory=list)
    considered: int = 0


def _run(need: Need, *, category, exclude_unit_id, user, request: ResourceRequest | None, query_text: str,
         allow_partial: bool = False) -> Outcome:
    started = time.monotonic()
    try:
        mv_embed, mv_rank = embed_model(), rank_model()
        candidates_qs = (_hard_rules(need, category, exclude_unit_id, allow_partial)
                         .exclude(pk__in=_turned_down(user, request, query_text)))
        assets = list(candidates_qs[:MAX_CANDIDATES * 2])
        ensure_asset_embeddings(assets, mv_embed)
        query_vec = get_embedder().embed([need.text + " " + need.specs])[0]
        # pgvector: cosine distance in SQL, nearest first (HNSW index in production-sized data).
        dist = dict(EmbeddingIndex.objects.filter(kind=EmbeddedKind.ASSET, object_id__in=[a.pk for a in assets])
                    .annotate(d=CosineDistance("embedding", query_vec)).order_by("d")
                    .values_list("object_id", "d")[:MAX_CANDIDATES])
    except Exception as exc:  # index or model unavailable -> keyword fallback, clearly labelled
        log.warning("Matching unavailable, keyword fallback: %s", exc)
        _log_inference(None, user, need, AIOutcome.UNAVAILABLE, started, "fallback: keyword search")
        words = " ".join((need.text or "").split()[:6])
        fb = list(search(q=words, category=category)[:MAX_RESULTS]) if words else []
        return Outcome(None, ranked=False, fallback=fb)

    engine = MatchingEngine(get_embedder().name)
    cands = []
    for a in assets:
        if a.pk not in dist:
            continue
        c = engine.factors(need, a, 1 - float(dist[a.pk]), _emission_kg(a.category))
        if c is not None:
            cands.append(c)
    ranked: list[Ranked] = engine.rank(cands, need.urgency, keep_below=WEAK_SCORE)[:MAX_RESULTS]

    with transaction.atomic():
        if request is not None:
            MatchResultSet.objects.filter(request=request, status=ResultSetStatus.CURRENT).update(status=ResultSetStatus.SUPERSEDED)
        rs = MatchResultSet.objects.create(request=request, query_text=query_text[:1000], model_version=mv_rank,
                                           generated_by=user if getattr(user, "pk", None) else None,
                                           input_snapshot_ref=_snapshot(need, assets, mv_rank))
        recs = [MatchRecommendation(result_set=rs, asset=r.asset, rank=i + 1, compatibility_score=Decimal(str(r.score)),
                                    confidence=Decimal(str(r.confidence)) if r.confidence is not None else None,
                                    factor_scores={"factors": r.factors, "points": r.contributions, "notes": r.notes},
                                    explanation=r.explanation, estimate_notes=r.estimate_notes)
                for i, r in enumerate(ranked)]
        MatchRecommendation.objects.bulk_create(recs)
    top = ranked[0] if ranked else None
    _log_inference(mv_rank, user, need, AIOutcome.OK if ranked else AIOutcome.NO_EVIDENCE, started,
                   f"{len(ranked)} results; top {top.asset.name} {top.score:.0f}" if top else "no match",
                   Decimal(str(top.confidence)) if top and top.confidence is not None else None)
    recs = list(rs.recommendations.select_related("asset", "asset__category", "asset__owner_department"))
    return Outcome(rs, [r for r in recs if not r.is_weak()], [r for r in recs if r.is_weak()], True, [], len(assets))


def _log_inference(mv, user, need: Need, outcome, started, summary, confidence=None):
    ref = "sha256:" + hashlib.sha256(json.dumps(need.__dict__, sort_keys=True, default=str).encode()).hexdigest()[:32]
    AIInferenceRecord.objects.create(model_version=mv, user=user if getattr(user, "pk", None) else None,
                                     capability=AICapability.RANK, input_ref=ref, output_summary=summary[:500],
                                     confidence=confidence, latency_ms=int((time.monotonic() - started) * 1000), outcome=outcome)


def generate_matches(request_id, user=None) -> Outcome:
    """UC-26 for a saved request: hard rules use its category and exclude its own unit."""
    req = ResourceRequest.objects.select_related("category", "department").get(pk=request_id)
    return _run(need_from_request(req), category=req.category, exclude_unit_id=req.department_id, user=user,
                request=req, query_text=request_text(req))


def find(text: str, user: User, quantity: int = 1, category: Category | None = None) -> Outcome:
    """The Find page: free text in English or Arabic, before any request exists."""
    text = (text or "").strip()
    if len(text) < 2:
        raise ValidationFailed("Describe what you need in a few words")
    return _run(need_from_text(text, user, quantity), category=category, exclude_unit_id=user.department_id, user=user,
                request=None, query_text=text)


def current_for(req: ResourceRequest) -> MatchResultSet | None:
    """The latest result set for a request if nothing it depends on has changed; otherwise None (re-run)."""
    rs = req.match_sets.filter(status=ResultSetStatus.CURRENT).first()
    if rs is None:
        return None
    assets = list(_hard_rules(need_from_request(req), req.category, req.department_id)
                  .exclude(pk__in=_turned_down(req.requester, req, ""))[:MAX_CANDIDATES * 2])
    return rs if rs.is_current(_snapshot(need_from_request(req), assets, rank_model())) else None


def suggestions_for(req: ResourceRequest, user=None) -> Outcome:
    """Suggestions shown on a pending request: reuse a current result set, or generate a new one."""
    rs = current_for(req)
    if rs is None:
        return generate_matches(req.pk, user)
    recs = list(rs.recommendations.select_related("asset", "asset__category", "asset__owner_department"))
    return Outcome(rs, [r for r in recs if not r.is_weak()], [r for r in recs if r.is_weak()], True)


# ----------------------------------------------------------------------------- decisions

def _owned(rec: MatchRecommendation, user: User) -> None:
    rs = rec.result_set
    owner = rs.request.requester_id if rs.request_id else rs.generated_by_id
    if owner != user.pk:
        raise Forbidden("Only the person who asked can decide on these suggestions")


@transaction.atomic
def record_decision(match_id, user, decision: str, reason: str = "") -> MatchRecommendation:
    """Requester selects / marks 'not suitable' (reason required); also writes the AIInferenceRecord decision."""
    rec = MatchRecommendation.objects.select_related("result_set__request").select_for_update(of=("self",)).get(pk=match_id)
    _owned(rec, user)
    if decision == UserDecision.REJECTED and not reason.strip():
        raise ValidationFailed("Pick a reason so we can improve the suggestions")
    if decision not in UserDecision.values:
        raise ValidationFailed("Unknown decision")
    rec.record_decision(decision, reason.strip()[:300])
    inf = (AIInferenceRecord.objects.filter(capability=AICapability.RANK, user=user, created_at__gte=rec.result_set.generated_at)
           .order_by("created_at").first())
    if inf is not None and not inf.user_decision:
        inf.record_decision(decision, reason)
    return rec


@transaction.atomic
def choose_for_request(match_id, user) -> ResourceRequest:
    """A category-only request picks one of its suggested items, which makes it approvable (approval needs an item)."""
    rec = MatchRecommendation.objects.select_related("result_set__request", "asset").get(pk=match_id)
    req = rec.result_set.request
    if req is None:
        raise ValidationFailed("This suggestion is not linked to a request")
    _owned(rec, user)
    req = ResourceRequest.objects.select_for_update().get(pk=req.pk)
    if req.status != RequestStatus.PENDING_APPROVAL:
        raise ValidationFailed("Only pending requests can change the selected item")
    a = published().select_related("owner_department").filter(pk=rec.asset_id).first()
    if a is None or a.unreserved_quantity < req.quantity:
        raise ValidationFailed("That item is no longer free in the quantity you asked for")
    req.select_asset(a.pk)
    record_decision(rec.pk, user, UserDecision.ACCEPTED)
    record(user, "select_match", "ResourceRequest", req.pk, after={"asset": str(a.pk), "score": str(rec.compatibility_score)})
    what = f"{req.quantity} × {a.name}"
    for approver in users_who_can("request.approve", a.owner_department):
        if approver.pk != user.pk:
            enqueue(approver, NotificationType.REQUEST_SUBMITTED,
                    Msg(_l("%(who)s (%(unit)s) asks for %(what)s."), who=user.full_name, unit=req.department, what=what),
                    f"ResourceRequest:{req.pk}")
    return req


def note_request_from_match(match_id, user) -> None:
    """Called after a request was sent from a Find result, so the suggestion counts as accepted."""
    try:
        rec = MatchRecommendation.objects.select_related("result_set").get(pk=match_id)
        if rec.result_set.generated_by_id == user.pk and not rec.user_decision:
            rec.record_decision(UserDecision.ACCEPTED)
    except Exception:  # unknown or malformed id: never break the request flow for a log line
        pass
