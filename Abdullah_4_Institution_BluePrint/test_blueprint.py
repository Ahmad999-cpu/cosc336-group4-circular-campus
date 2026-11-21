"""Institution Blueprint (bonus): units, member types, approval routes, the route tester, templates and AI drafts."""
from decimal import Decimal
from unittest import mock

from django.test import TestCase
from django.urls import reverse

from apps.access.models import Department, Role
from apps.ai.gateway import AIGateway
from apps.ai.models import AICapability, AIOutcome, ModelVersion
from apps.ai.result import AIResult
from apps.audit.models import AuditLog as AuditEntry
from apps.blueprint import services
from apps.blueprint.models import BlueprintDraft, DraftStatus
from apps.blueprint.routing import approval_route
from apps.common.errors import Forbidden, ValidationFailed

from .factories import World, role, user


class Base(TestCase):
    def setUp(self):
        self.w = World(qty=4, value="650")
        self.admin = user("Ali", self.w.uni, (role("Admin", "admin.blueprint", "admin.users"), None))


class UnitTests(Base):
    def test_create_edit_and_tree(self):
        lab = services.save_unit(self.admin, {"name": "Robotics Lab", "unit_type": "Lab", "parent": str(self.w.me.pk)})
        names = [(u.name, d) for u, d in services.unit_tree()]
        self.assertIn(("Robotics Lab", 3), names)
        services.save_unit(self.admin, {"name": "Robotics Lab", "parent": str(self.w.cs.pk)}, unit_id=lab.pk)
        lab.refresh_from_db()
        self.assertEqual(lab.parent, self.w.cs)
        self.assertTrue(AuditEntry.objects.filter(action="blueprint_unit_update").exists())

    def test_no_loops_and_safe_deactivation(self):
        with self.assertRaises(ValidationFailed):
            services.save_unit(self.admin, {"name": "Eng", "parent": str(self.w.cs.pk)}, unit_id=self.w.eng.pk)
        with self.assertRaises(ValidationFailed):  # still has active sub-units
            services.set_unit_status(self.admin, self.w.eng.pk, False)
        with self.assertRaises(ValidationFailed):  # still owns assets
            services.set_unit_status(self.admin, self.w.cs.pk, False)
        empty = services.save_unit(self.admin, {"name": "Old annex", "parent": str(self.w.uni.pk)})
        self.assertEqual(services.set_unit_status(self.admin, empty.pk, False).status, "INACTIVE")

    def test_only_admins(self):
        with self.assertRaises(Forbidden):
            services.save_unit(self.w.requester, {"name": "X"})


class RoleTests(Base):
    def test_save_with_permissions_and_limit(self):
        r = services.save_role(self.admin, {"name": "Dean", "approval_limit": "10,000", "permissions": ["request.approve", "reports.view"]})
        self.assertEqual(r.approval_limit, Decimal("10000"))
        self.assertTrue(r.permits("request.approve"))
        with self.assertRaises(ValidationFailed):
            services.save_role(self.admin, {"name": "dean", "permissions": []})  # duplicate name
        with self.assertRaises(ValidationFailed):
            services.save_role(self.admin, {"name": "Odd", "permissions": ["launch.rockets"]})

    def test_cannot_lock_everyone_out(self):
        admin_role = Role.objects.get(name="Admin")
        with self.assertRaises(ValidationFailed):
            services.save_role(self.admin, {"name": "Admin", "permissions": ["admin.users"]}, role_id=admin_role.pk)


class RouteTests(Base):
    def test_priority_category_and_value(self):
        dean = services.save_role(self.admin, {"name": "Dean", "permissions": ["request.approve"]})
        services.save_rule(self.admin, {"name": "Everything", "priority": 100, "approver_role": dean.pk})
        services.save_rule(self.admin, {"name": "Big monitors", "priority": 10, "category": self.w.category.pk,
                                        "min_value": "1000", "approver_role": self.w.r_app.pk, "approver_scope": "PARENT_UNIT"})
        self.assertEqual(approval_route(self.w.asset, 2), (self.w.r_app, self.w.eng))  # 1,300 ≥ 1,000
        self.assertEqual(approval_route(self.w.asset, 1), (dean, self.w.asset.owner_department))  # 650: falls through

    def test_rule_checks(self):
        viewer = services.save_role(self.admin, {"name": "Viewer", "permissions": ["reports.view"]})
        with self.assertRaises(ValidationFailed):  # that role can't approve
            services.save_rule(self.admin, {"name": "Bad", "approver_role": viewer.pk})
        with self.assertRaises(ValidationFailed):
            services.save_rule(self.admin, {"name": "Bad", "approver_role": self.w.r_app.pk, "min_value": "5", "max_value": "1"})
        r = services.save_rule(self.admin, {"name": "Off soon", "approver_role": self.w.r_app.pk})
        self.assertFalse(services.toggle_rule(self.admin, r.pk).active)
        self.assertIsNone(approval_route(self.w.asset, 1))

    def test_who_approves(self):
        out = services.who_approves(self.w.asset, 2)
        self.assertIsNone(out["rule"])
        self.assertEqual(out["people"], [self.w.approver])
        out = services.who_approves(self.w.asset, 4)  # AED 2,600 > Adam's 2,000 limit
        self.assertEqual(out["people"], [])


class DraftTests(Base):
    def setUp(self):
        super().setUp()
        ModelVersion.objects.create(capability=AICapability.BLUEPRINT, provider="fake", model_name="fake", version="b1").activate()

    def test_template_review_and_publish_is_additive(self):
        Department.objects.create(name="Library")  # already exists: kept as it is
        d = services.draft_from_template(self.admin, "university")
        rv = services.review(d)
        self.assertEqual(rv["problems"], 0)
        self.assertTrue(next(u for u in rv["units"] if u["name"] == "Library")["exists"])
        made = services.publish_draft(d.pk, self.admin)
        self.assertEqual(made, {"units": 5, "roles": 5, "rules": 2})  # "Requester" already exists
        self.assertEqual(Department.objects.filter(name="Library").count(), 1)
        self.assertEqual(Department.objects.get(name="College of Science").parent.name, "University")
        self.assertEqual(Role.objects.get(name="Head of Department").approval_limit, Decimal("5000"))
        d.refresh_from_db()
        self.assertEqual(d.status, DraftStatus.PUBLISHED)
        with self.assertRaises(ValidationFailed):
            services.publish_draft(d.pk, self.admin)

    def test_problems_block_publishing_and_nothing_is_written(self):
        d = BlueprintDraft.objects.create(created_by=self.admin, description="x", draft={
            "units": [{"name": "Ward 9", "parent": "Nowhere"}],
            "roles": [{"name": "Nurse", "permissions": ["request.submit", "fly"]}],
            "rules": [{"name": "R", "approver_role": "Nurse"}]})
        rv = services.review(d)
        self.assertEqual(rv["problems"], 3)
        with self.assertRaises(ValidationFailed):
            services.publish_draft(d.pk, self.admin)
        self.assertFalse(Department.objects.filter(name="Ward 9").exists())
        self.assertFalse(Role.objects.filter(name="Nurse").exists())

    def test_untick_items(self):
        d = services.draft_from_template(self.admin, "school")
        made = services.publish_draft(d.pk, self.admin, {"units": {0, 1}, "roles": set(), "rules": set()})
        self.assertEqual(made, {"units": 2, "roles": 0, "rules": 0})

    def test_route_needs_its_member_type(self):
        d = services.draft_from_template(self.admin, "school")
        with self.assertRaises(ValidationFailed):
            services.publish_draft(d.pk, self.admin, {"units": set(), "roles": set(), "rules": {0}})

    def test_ai_draft_is_normalised_and_offline_fallback_works(self):
        d, msg = services.draft_from_description(self.admin, "A small hospital with radiology and outpatients wards.")
        self.assertEqual(msg, "")
        self.assertIn("Radiology", [u["name"] for u in d.draft["units"]])  # fake provider: hospital template
        gw = mock.Mock(spec=AIGateway)
        gw.draft_blueprint.return_value = AIResult(AIOutcome.OK, value={"units": [{"name": "  HQ ", "parent": None}, "junk"],
                                                                         "roles": [{"name": "Boss", "permissions": ["request.approve"], "approval_limit": "abc"}],
                                                                         "rules": [{"name": "All", "approver_role": "Boss", "priority": "7"}]})
        d, _ = services.draft_from_description(self.admin, "Our company has one office and a boss who approves.", gateway=gw)
        self.assertEqual(d.draft["units"], [{"name": "HQ", "unit_type": "", "parent": None}])
        self.assertIsNone(d.draft["roles"][0]["approval_limit"])
        self.assertEqual(d.draft["rules"][0]["priority"], 7)
        gw.draft_blueprint.return_value = AIResult(AIOutcome.TIMEOUT)
        d, msg = services.draft_from_description(self.admin, "Our company has one office and a boss who approves.", gateway=gw)
        self.assertIsNone(d)
        self.assertIn("template", msg)


class ScreenTests(Base):
    def test_tabs_drawers_and_publish(self):
        ModelVersion.objects.create(capability=AICapability.BLUEPRINT, provider="fake", model_name="fake", version="b1").activate()
        self.client.force_login(self.admin)
        for tab, text in [("units", "Engineering"), ("roles", "Approves up to"), ("routes", "Who would approve?"), ("start", "Start from a template")]:
            self.assertContains(self.client.get(reverse("blueprint:index"), {"tab": tab}), text)
        self.assertContains(self.client.get(reverse("blueprint:unit_new")), "Save unit")
        r = self.client.post(reverse("blueprint:unit_new"), {"name": "Annex", "parent": self.w.uni.pk}, HTTP_HX_REQUEST="true")
        self.assertIn("HX-Redirect", r.headers)
        r = self.client.get(reverse("blueprint:try"), {"asset": self.w.asset.pk, "qty": 1})
        self.assertContains(r, "Adam")
        r = self.client.post(reverse("blueprint:from_template", args=["hospital"]), HTTP_HX_REQUEST="true")
        draft_url = r.headers["HX-Redirect"]
        self.assertContains(self.client.get(draft_url), "Publish ticked items")
        d = BlueprintDraft.objects.get()
        self.client.post(reverse("blueprint:publish", args=[d.pk]), {"units": ["0", "1"]})
        self.assertTrue(Department.objects.filter(name="Clinical services").exists())

    def test_non_admins_get_403(self):
        self.client.force_login(self.w.approver)
        self.assertEqual(self.client.get(reverse("blueprint:index")).status_code, 403)
