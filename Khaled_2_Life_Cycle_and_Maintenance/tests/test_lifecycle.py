from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse

from apps.catalogue.models import Asset, AssetState, PublicationStatus
from apps.common.errors import Forbidden, SelfApproval, ValidationFailed
from apps.lifecycle import services
from apps.lifecycle.models import EventType, LifeCycleEvent, MaintenanceStatus

from .factories import World, role, user


class Base(TestCase):
    def setUp(self):
        self.w = World(qty=2)
        self.w.r_cus.permissions.add(*_perms("maintenance.record", "eol.propose"))
        r_rev = role("Reviewer", "eol.approve")
        self.reviewer = user("Rev", self.w.eng, (r_rev, self.w.eng))
        self.tech = user("Tech", self.w.uni, (role("Maintenance Staff", "maintenance.record"), None))

    def fresh(self):
        return Asset.objects.get(pk=self.w.asset.pk)


def _perms(*codes):
    from apps.access.models import Permission
    return [Permission.objects.get_or_create(code=c, defaults={"description": c})[0] for c in codes]


class MaintenanceTests(Base):
    def test_full_repair_cycle(self):
        rec = services.report_problem(self.w.custodian, self.w.asset, description="Flickers", severity="HIGH", condition="FAIR")
        self.assertEqual(rec.status, MaintenanceStatus.DEFECT_REPORTED)
        with self.assertRaises(ValidationFailed):  # one open record per asset
            services.report_problem(self.w.custodian, self.w.asset, description="Again", severity="LOW", condition="FAIR")
        services.start_work(self.tech, rec)
        a = self.fresh()
        self.assertEqual((a.lifecycle_state, a.publication_status), (AssetState.UNDER_MAINTENANCE, PublicationStatus.UNPUBLISHED))
        services.record_repair(self.tech, rec, description="New backlight", actions="", outcome="SUCCESSFUL", cost=Decimal("120"))
        rec.refresh_from_db()
        self.assertEqual(rec.status, MaintenanceStatus.REPAIR_COMPLETED)
        self.assertEqual(self.fresh().lifecycle_state, AssetState.UNDER_MAINTENANCE)  # FR-10.18
        with self.assertRaises(Forbidden):  # only custodians return it to service
            services.return_to_service(self.tech, rec, "GOOD")
        services.return_to_service(self.w.custodian, rec, "GOOD")
        a = self.fresh()
        self.assertEqual((a.lifecycle_state, a.condition), (AssetState.AVAILABLE, "GOOD"))
        kinds = set(LifeCycleEvent.objects.filter(asset=a).values_list("event_type", flat=True))
        self.assertTrue({EventType.MAINTENANCE, EventType.REPAIR, EventType.STATE_CHANGE} <= kinds)

    def test_unsuccessful_repair_loops(self):
        rec = services.report_problem(self.w.custodian, self.w.asset, description="Dead", severity="LOW", condition="POOR")
        services.start_work(self.tech, rec)
        services.record_repair(self.tech, rec, description="Tried", actions="", outcome="UNSUCCESSFUL", cost=Decimal("0"))
        rec.refresh_from_db()
        self.assertEqual(rec.status, MaintenanceStatus.FURTHER_REPAIR_REQUIRED)
        services.start_work(self.tech, rec)
        rec.refresh_from_db()
        self.assertEqual(rec.status, MaintenanceStatus.IN_PROGRESS)

    def test_no_maintenance_while_reserved(self):
        self.w.asset.allocate(1, self.w.approver)
        rec = services.report_problem(self.w.custodian, self.w.asset, description="Scratch", severity="LOW", condition="GOOD")
        with self.assertRaises(ValidationFailed):
            services.start_work(self.tech, rec)

    def test_requesters_cannot_report(self):
        with self.assertRaises(Forbidden):
            services.report_problem(self.w.requester, self.w.asset, description="x", severity="LOW", condition="GOOD")


class EndOfLifeTests(Base):
    def test_independent_review_and_completion(self):
        p = services.propose_end_of_life(self.w.custodian, self.w.asset, "DONATE", "Replaced by new screens")
        with self.assertRaises(ValidationFailed):  # one open proposal
            services.propose_end_of_life(self.w.custodian, self.w.asset, "RECYCLE", "x")
        self.w.custodian.role_assignments.create(role=role("Reviewer", "eol.approve"), scope_department=self.w.eng)
        with self.assertRaises(SelfApproval):
            services.decide_end_of_life(self.w.custodian, p, True)
        services.decide_end_of_life(self.reviewer, p, True, "OK to donate")
        a = services.complete_end_of_life(self.w.custodian, p)
        self.assertEqual(a.lifecycle_state, AssetState.DONATED)
        states = list(LifeCycleEvent.objects.filter(asset=a, approval_ref=p).values_list("new_state", flat=True))
        self.assertIn(AssetState.RETIRED, states)
        self.assertIn(AssetState.DONATED, states)

    def test_rejection_needs_reason_and_blocks_completion(self):
        p = services.propose_end_of_life(self.w.custodian, self.w.asset, "DISPOSE", "Old")
        with self.assertRaises(ValidationFailed):
            services.decide_end_of_life(self.reviewer, p, False, "")
        services.decide_end_of_life(self.reviewer, p, False, "Can still be donated")
        with self.assertRaises(Exception):
            services.complete_end_of_life(self.w.custodian, p)
        self.assertEqual(self.fresh().lifecycle_state, AssetState.AVAILABLE)

    def test_no_end_of_life_with_commitments(self):
        self.w.asset.allocate(1, self.w.approver)
        with self.assertRaises(ValidationFailed):
            services.propose_end_of_life(self.w.custodian, self.w.asset, "RETIRE", "x")


class HistoryTests(Base):
    def test_correction_is_a_new_row(self):
        ev = LifeCycleEvent.objects.filter(asset=self.w.asset).first()
        c = services.correct_event(self.w.custodian, ev, "Wrong room recorded")
        self.assertEqual(c.corrects, ev)
        self.assertEqual(LifeCycleEvent.objects.filter(asset=self.w.asset).count(), 3)


@override_settings(ALLOWED_HOSTS=["testserver"])
class ScreenTests(Base):
    def test_history_page_shows_allowed_moves(self):
        self.client.force_login(self.w.requester)
        r = self.client.get(reverse("lifecycle:history", args=[self.w.asset.pk]))
        self.assertContains(r, "Allowed next")
        self.assertContains(r, "Cara")

    def test_board_flow(self):
        rec = services.report_problem(self.w.custodian, self.w.asset, description="Flickers", severity="HIGH", condition="FAIR")
        self.client.force_login(self.tech)
        h = {"HTTP_HX_REQUEST": "true"}
        self.assertContains(self.client.get(reverse("lifecycle:maintenance")), "Flickers")
        self.client.post(reverse("lifecycle:start", args=[rec.pk]), **h)
        r = self.client.post(reverse("lifecycle:repair", args=[rec.pk]), {"description": "Fixed", "outcome": "SUCCESSFUL", "cost": "50"}, **h)
        self.assertContains(r, "Back in service")

    def test_requester_has_no_board(self):
        self.client.force_login(self.w.requester)
        self.assertEqual(self.client.get(reverse("lifecycle:maintenance")).status_code, 403)


class VisibilityTests(TestCase):
    """Found in validation: maintenance staff were sent to a 404 for an item under repair."""

    def test_people_who_work_with_a_unit_can_open_its_unpublished_items(self):
        w = World()
        w.asset.unpublish(w.custodian)
        tech = user("Tariq", w.uni, (role("Maintenance Staff", "maintenance.record"), w.eng))
        for who, code in [(tech, 200), (w.approver, 200), (w.requester, 404)]:
            self.client.force_login(who)
            self.assertEqual(self.client.get(reverse("catalogue:panel", args=[w.asset.pk])).status_code, code, who.full_name)
            self.assertEqual(self.client.get(reverse("lifecycle:history", args=[w.asset.pk])).status_code, code, who.full_name)
