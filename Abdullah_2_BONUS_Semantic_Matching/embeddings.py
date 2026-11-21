"""Text embeddings for semantic matching (ADR-5: computed on our own server, never sent out).

Two embedders share one interface and the same 384-dimension pgvector column:

* "sentence-transformers" (production): paraphrase-multilingual-MiniLM-L12-v2. Arabic and English sentences with
  the same meaning land close together. Needs `pip install -r requirements-ai.txt` and a one-time model download
  (about 470 MB).
* "lexical" (default, offline): a deterministic embedding built from words, a bilingual synonym table and
  character trigrams, hashed into 384 dimensions. It needs nothing to download, so tests, laptops without the
  model, and a lab without internet all work. It understands the synonyms listed below ("display screen" ~
  "monitor", "شاشة" ~ "monitor") but not open-ended paraphrase.

Choose with EMBEDDING_BACKEND in settings / .env. The score bands in engine.py are calibrated per embedder.
"""
from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from functools import lru_cache

from django.conf import settings

DIM = 384

# ---------------------------------------------------------------- Arabic and English normalisation

_AR_DIACRITICS = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭ]")
_AR_MAP = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي", "ـ": ""})
_AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_TOKEN = re.compile(r"[^\W_]+(?:-[^\W_]+)*", re.UNICODE)


def normalise(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").lower().translate(_AR_DIGITS)
    text = _AR_DIACRITICS.sub("", text).translate(_AR_MAP)
    return text


def _strip_ar_prefix(tok: str) -> str:
    for p in ("وال", "بال", "كال", "فال", "لل", "ال"):
        if tok.startswith(p) and len(tok) - len(p) >= 2:
            return tok[len(p):]
    return tok


def _stem_en(tok: str) -> str:
    for suf in ("ies", "es", "s"):
        if tok.endswith(suf) and len(tok) - len(suf) >= 3 and not tok.endswith("ss"):
            return tok[: -len(suf)] + ("y" if suf == "ies" else "")
    return tok


def tokens(text: str) -> list[str]:
    out = []
    for raw in _TOKEN.findall(normalise(text)):
        tok = _strip_ar_prefix(raw)
        out.append(_stem_en(tok) if tok.isascii() else tok)
    return out


# ---------------------------------------------------------------- bilingual concepts

# concept: words that mean it (English and Arabic, any form; normalised on load).
CONCEPTS = {
    "monitor": "monitor screen display lcd led-screen شاشه شاشات شاشتان شاشتين",
    "projector": "projector beamer slide slides presentation بروجكتور بروجكتر عارض شرائح",
    "computer": "computer pc desktop workstation laptop notebook حاسوب حاسب كمبيوتر لابتوب",
    "dock": "dock docking hub usb-c-hub منصه موزع",
    "chair": "chair seat seating stool armchair كرسي كراسي مقعد مقاعد",
    "table": "table desk bench workbench طاوله طاولات مكتب مكاتب",
    "whiteboard": "whiteboard board flipchart سبوره لوح",
    "shelf": "shelf shelving bookshelf bookcase cabinet storage locker رف رفوف خزانه دولاب",
    "printer": "printer 3d-printer printing prototyping طابعه طابعات",
    "oscilloscope": "oscilloscope scope signal waveform راسم اوسيلوسكوب",
    "power": "power-supply psu supply bench-supply مزود طاقه",
    "microscope": "microscope مجهر",
    "camera": "camera webcam كاميرا",
    "lectern": "lectern podium منبر منصه-خطابه",
    "lab": "lab laboratory مختبر معمل",
    "classroom": "classroom lecture teaching قاعه فصل محاضره",
    "club": "club society نادي",
    "furniture": "furniture اثاث",
}
_WORD_TO_CONCEPT: dict[str, str] = {}
for concept, words in CONCEPTS.items():
    for w in words.split():
        for t in tokens(w.replace("-", " ")) + tokens(w):
            _WORD_TO_CONCEPT.setdefault(t, concept)

# Concepts that are related but not the same (used for a weaker shared feature).
FAMILIES = {
    "screens": {"monitor", "projector"},
    "workstation": {"monitor", "computer", "dock", "table", "chair"},
    "seating": {"chair", "table"},
    "teaching": {"projector", "whiteboard", "lectern", "classroom"},
    "electronics-lab": {"oscilloscope", "power", "microscope", "lab"},
    "storage": {"shelf"},
}


def concepts_in(text: str) -> set[str]:
    return {_WORD_TO_CONCEPT[t] for t in tokens(text) if t in _WORD_TO_CONCEPT}


# ---------------------------------------------------------------- embedders

def _bucket(feature: str) -> tuple[int, float]:
    h = hashlib.md5(feature.encode("utf-8")).digest()
    return int.from_bytes(h[:4], "little") % DIM, (1.0 if h[4] & 1 else -1.0)


class LexicalEmbedder:
    name = "lexical"
    model_name = "circular-campus-lexical-1"

    def embed_one(self, text: str) -> list[float]:
        v = [0.0] * DIM
        toks = tokens(text)

        def add(feature, weight):
            i, sign = _bucket(feature)
            v[i] += sign * weight

        found = set()
        for t in toks:
            c = _WORD_TO_CONCEPT.get(t)
            if c:
                found.add(c)
                add("c:" + c, 3.0)
            add("w:" + t, 1.0)
            padded = f"#{t}#"
            for k in range(len(padded) - 2):
                add("g:" + padded[k:k + 3], 0.25)
        for fam, members in FAMILIES.items():
            if found & members:
                add("f:" + fam, 0.6)
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_one(t) for t in texts]


class SentenceTransformerEmbedder:
    name = "sentence-transformers"

    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        from sentence_transformers import SentenceTransformer  # requirements-ai.txt
        self._model = SentenceTransformer(self.model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [list(map(float, row)) for row in self._model.encode(texts, normalize_embeddings=True)]


@lru_cache(maxsize=1)
def get_embedder():
    """Loaded once per process. Falls back to the lexical embedder if the real model is not installed."""
    if getattr(settings, "EMBEDDING_BACKEND", "lexical") == "sentence-transformers":
        try:
            return SentenceTransformerEmbedder()
        except Exception:  # model missing or no internet for the first download: keep matching working
            import logging
            logging.getLogger(__name__).warning("Sentence-transformers model unavailable; using the lexical embedder")
    return LexicalEmbedder()


def cosine(a, b) -> float:
    return sum(x * y for x, y in zip(a, b))
