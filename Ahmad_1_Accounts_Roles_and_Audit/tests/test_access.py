from datetime import timedelta

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.access import services
from apps.access.models import AccountStatus, RoleAssignment, User, UserSession
from apps.audit.models import AuditLog
from apps.common.errors import Forbidden, ValidationFailed

from .factories import World, role, user


@override_settings(ALLOWED_HOSTS=["testserver"])
class SignInTests(TestCase):
    def setUp(self):
        self.w = World()

    def test_sign_in_and_audit(self):
        r = self.client.post(reverse("access:login"), {"username": self.w.requester.email, "password": "pw-123456!"})
        self.assertRedirects(r, reverse("web:home"), fetch_redirect_response=False)
        self.assertTrue(AuditLog.objects.filter(action="sign_in", actor=self.w.requester).exists())

    def test_wrong_password_is_refused_and_audited(self):
        r = self.client.post(reverse("access:login"), {"username": self.w.requester.email, "password": "nope"})
        self.assertContains(r, "incorrect")
        self.assertTrue(AuditLog.objects.filter(action="sign_in_failed", outcome="FAILED").exists())

    def test_deactivated_account_cannot_sign_in(self):
        self.w.requester.deactivate()
        r = self.client.post(reverse("access:login"), {"username": self.w.requester.email, "password": "pw-123456!"})
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    @override_settings(DEBUG=False)
    def test_demo_sign_in_is_off_in_production(self):
        self.assertEqual(self.client.post(reverse("access:demo_login"), {"email": "admin@demo.local"}).status_code, 404)

    def test_passwords_are_argon2(self):
        self.assertTrue(User.objects.get(pk=self.w.requester.pk).password.startswith("argon2"))


@override_settings(ALLOWED_HOSTS=["testserver"])
class PeopleTests(TestCase):
    def setUp(self):
        self.w = World()
        self.r_admin = role("System Administrator", "admin.users")
        self.admin = user("Ali", self.w.uni, (self.r_admin, None))

    def test_people_screen_is_for_admins_only(self):
        self.client.force_login(self.w.requester)
        self.assertEqual(self.client.get(reverse("access:people")).status_code, 403)
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse("access:people")), self.w.requester.full_name)

    def test_service_refuses_non_admins_even_without_the_screen(self):
        with self.assertRaises(Forbidden):
            services.create_user(self.w.requester, full_name="X", email="x@t.local", department=None, password="pw-123456!")

    def test_scoped_admin_is_not_enough(self):
        local = user("Local", self.w.cs, (self.r_admin, self.w.cs))
        with self.assertRaises(Forbidden):
            services.set_status(local, self.w.requester, AccountStatus.SUSPENDED)

    def test_create_assign_and_revoke(self):
        u = services.create_user(self.admin, full_name="Mona Ali", email="Mona@T.local", department=self.w.me, password="pw-123456!")
        self.assertEqual(u.email, "mona@t.local")
        ra = services.assign_role(self.admin, u, self.w.r_req, self.w.me)
        self.assertTrue(u.has_role("Requester", self.w.me))
        with self.assertRaises(ValidationFailed):
            services.assign_role(self.admin, u, self.w.r_req, self.w.me)
        services.revoke_role(self.admin, ra)
        self.assertFalse(u.has_role("Requester", self.w.me))
        self.assertEqual(AuditLog.objects.filter(actor=self.admin).count(), 3)

    def test_duplicate_email_refused(self):
        with self.assertRaises(ValidationFailed):
            services.create_user(self.admin, full_name="Dup", email=self.w.requester.email.upper(), department=None, password="pw-123456!")

    def test_last_administrator_cannot_be_locked_out(self):
        with self.assertRaises(ValidationFailed):
            services.set_status(self.admin, self.admin, AccountStatus.DEACTIVATED)
        ra = RoleAssignment.objects.get(user=self.admin, role=self.r_admin)
        with self.assertRaises(ValidationFailed):
            services.revoke_role(self.admin, ra)
        user("Second", self.w.uni, (self.r_admin, None))
        services.revoke_role(self.admin, ra)  # fine now

    def test_suspending_ends_sessions(self):
        self.client.force_login(self.w.requester)
        self.client.get("/")
        services.set_status(self.admin, self.w.requester, AccountStatus.SUSPENDED)
        self.assertEqual(self.client.get("/requests/").status_code, 302)
        self.assertContains(self.client.get("/"), "Make campus reuse work")  # signed out: the public guest page

    def test_panel_flow_over_htmx(self):
        self.client.force_login(self.admin)
        h = {"HTTP_HX_REQUEST": "true"}
        r = self.client.post(reverse("access:role_assign", args=[self.w.requester.pk]), {"role": self.w.r_cus.pk, "scope": self.w.me.pk}, **h)
        self.assertEqual(r.status_code, 200)
        self.assertIn("cc:toast", r["HX-Trigger-After-Settle"])
        self.assertTrue(self.w.requester.has_role("Custodian", self.w.me))


class IdleTimeoutTests(TestCase):
    """Found in validation: automatic refreshes must not keep an idle session alive (NFR-17)."""

    def test_background_requests_do_not_count_as_activity(self):
        w = World()
        self.client.force_login(w.requester)
        self.client.get(reverse("web:home"))
        row = UserSession.objects.get(user=w.requester)
        old = timezone.now() - timedelta(minutes=10)
        UserSession.objects.filter(pk=row.pk).update(last_activity_at=old)
        self.client.get(reverse("web:badges"), HTTP_X_BACKGROUND="1")
        row.refresh_from_db()
        self.assertEqual(row.last_activity_at, old)
        self.client.get(reverse("web:home"))
        row.refresh_from_db()
        self.assertGreater(row.last_activity_at, old)
