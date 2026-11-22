from decimal import Decimal

from django.conf import settings
from django.shortcuts import resolve_url
from django.template import Context, Template
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from .factories import World


class TemplateTagTests(TestCase):
    def render(self, src, **ctx):
        return Template("{% load ui %}" + src).render(Context(ctx))

    def test_ring_targets_the_score(self):
        html = self.render("{% ring 91 %}")
        self.assertIn(">91<", html)
        self.assertIn('data-to="', html)

    def test_weak_score_uses_warning_colour(self):
        self.assertIn("var(--warn-ring)", self.render("{% ring 60 %}"))

    def test_aed_never_shows_zero_for_missing(self):
        with translation.override("en"):
            self.assertEqual(self.render("{{ v|aed }}", v=None), "unavailable")
            self.assertEqual(self.render("{{ v|aed }}", v=Decimal("1260")), "AED 1,260")

    def test_steps_marks_current(self):
        html = self.render('{% steps 1 "Sent,Approved,On its way,Received" %}')
        self.assertEqual(html.count('class="step done"'), 1)
        self.assertEqual(html.count('class="step now"'), 1)


@override_settings(ALLOWED_HOSTS=["testserver"])
class ShellTests(TestCase):
    def setUp(self):
        self.w = World()

    def test_home_for_visitors_is_the_public_guest_page(self):
        r = self.client.get("/")
        self.assertContains(r, "Make campus reuse work")
        self.assertNotContains(r, "Your work")  # the dashboard needs a sign-in

    def test_home_renders_for_a_user(self):
        self.client.force_login(self.w.requester)
        r = self.client.get("/")
        self.assertContains(r, 'class="statement"')
        self.assertContains(r, self.w.requester.full_name)

    def test_arabic_is_right_to_left(self):
        self.client.force_login(self.w.requester)
        self.client.post("/i18n/setlang/", {"language": "ar", "next": "/"})
        self.assertContains(self.client.get("/"), 'dir="rtl"')


class HtmxEdgeTests(TestCase):
    """Found in the validation loop: partial requests at the edges (signed out, not allowed, stale page)."""

    def test_signed_out_htmx_goes_to_sign_in(self):
        r = self.client.get(reverse("resource_requests:mine"), HTTP_HX_REQUEST="true",
                            HTTP_HX_CURRENT_URL="http://127.0.0.1:8000/requests/")
        self.assertEqual(r.status_code, 204)
        self.assertTrue(r["HX-Redirect"].startswith(resolve_url(settings.LOGIN_URL)))
        self.assertIn("next=%2Frequests%2F", r["HX-Redirect"])

    def test_forbidden_htmx_is_a_toast(self):
        from .factories import World
        w = World()
        self.client.force_login(w.requester)
        r = self.client.get(reverse("transfers:queue"), HTTP_HX_REQUEST="true")
        self.assertEqual(r.status_code, 204)
        self.assertIn("cc:toast", r["HX-Trigger-After-Settle"])

    def test_stale_csrf_reloads_htmx_page(self):
        from django.test import Client
        from .factories import World
        w = World()
        c = Client(enforce_csrf_checks=True)
        c.force_login(w.requester)
        r = c.post(reverse("notifications:read_all"), HTTP_HX_REQUEST="true")
        self.assertEqual((r.status_code, r["HX-Refresh"]), (204, "true"))
