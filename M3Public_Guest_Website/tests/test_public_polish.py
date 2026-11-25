"""Login-page savings calculator link, professional footer, and the home 'Your work' cards."""
from django.test import TestCase, override_settings
from django.urls import reverse

from .factories import World, role, user

PROTECTED = ["catalogue:browse", "catalogue:mine", "resource_requests:mine", "sustainability:dashboard",
             "matching:find", "matching:saved", "reporting:index", "reporting:demand", "lifecycle:maintenance",
             "transfers:queue", "notifications:index", "access:people", "blueprint:index"]


class PublicCalculatorTests(TestCase):
    def test_login_page_links_to_the_calculator_with_and_without_demo_buttons(self):
        for debug in (True, False):
            with self.settings(DEBUG=debug):
                r = self.client.get(reverse("access:login"))
                self.assertContains(r, "Estimate savings")
                self.assertContains(r, f'href="{reverse("sustainability:calculator")}"')

    def test_visitor_uses_the_calculator_without_signing_in(self):
        r = self.client.get(reverse("sustainability:calculator"), {"staff": 1000, "type": "asset_intensive", "part": "typical"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "58,800")              # formula unchanged (1,000 staff, typical)
        self.assertNotContains(r, "Back to sign in")    # the guest header already links to Sign in
        self.assertContains(r, 'class="g-nav"')          # shown inside the guest site, with its menu
        self.assertContains(r, 'aria-current="page">Calculator</a>')
        self.assertContains(r, "Starting assumptions")  # the estimate explanation stays
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotContains(r, 'class="nav"')        # no menu into the system

    def test_visitor_still_cannot_reach_protected_pages(self):
        self.client.get(reverse("sustainability:calculator"))
        for name in PROTECTED:
            r = self.client.get(reverse(name))
            self.assertIn(r.status_code, (302, 403), name)
            if r.status_code == 302:
                self.assertIn(reverse("access:login"), r["Location"], name)

    def test_signed_in_users_reach_it_from_impact(self):
        w = World()
        self.client.force_login(w.requester)
        self.assertContains(self.client.get(reverse("sustainability:dashboard")), reverse("sustainability:calculator"))
        r = self.client.get(reverse("sustainability:calculator"))
        self.assertContains(r, "Savings calculator")
        self.assertNotContains(r, "Back to sign in")
        self.assertNotContains(r, 'class="g-nav"')       # signed-in people keep the app layout

    def test_arabic(self):
        r = self.client.get(reverse("access:login"), HTTP_ACCEPT_LANGUAGE="ar")
        self.assertContains(r, "قدّر التوفير")
        r = self.client.get(reverse("sustainability:calculator"), HTTP_ACCEPT_LANGUAGE="ar")
        self.assertContains(r, 'dir="rtl"')
        self.assertContains(r, "مخطط المؤسسة")   # the guest menu, in Arabic


class WordingAndCardsTests(TestCase):
    def test_no_course_wording_on_customer_pages(self):
        w = World()
        self.client.force_login(w.custodian)
        for name in ("web:home", "catalogue:mine", "sustainability:dashboard"):
            t = self.client.get(reverse(name)).content.decode()
            for bad in ("COSC", "Group 4", "prototype"):
                self.assertNotIn(bad, t, name)
            self.assertIn("Circular Campus · Smarter resource reuse", t)

    @override_settings(DEBUG=True)
    def test_sample_label_kept(self):
        self.client.force_login(World().requester)
        self.assertContains(self.client.get(reverse("web:home")), "Sample data. Figures are estimates for demonstration.")

    def test_cards_for_every_role_keep_their_links(self):
        w = World()
        tech = user("Tariq", w.uni, (role("Maintenance", "maintenance.record"), None))
        cases = {w.requester: ["resource_requests:mine", "sustainability:dashboard", "catalogue:browse"],
                 w.custodian: ["catalogue:mine", "sustainability:dashboard", "catalogue:browse"],
                 w.approver: ["transfers:queue"], w.facilities: ["transfers:board"], tech: ["lifecycle:maintenance"]}
        for who, names in cases.items():
            self.client.force_login(who)
            r = self.client.get(reverse("web:home"))
            self.assertContains(r, 'class="hub-card"')
            for n in names:
                self.assertContains(r, f'class="hub-card" href="{reverse(n)}"')
        self.client.force_login(w.requester)
        self.assertNotContains(self.client.get(reverse("web:home")), reverse("catalogue:mine"))  # role rules unchanged
