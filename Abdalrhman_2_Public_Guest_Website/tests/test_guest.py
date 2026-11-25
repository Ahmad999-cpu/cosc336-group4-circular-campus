"""Public guest site: pages, language, calls to action, and the contact form's delivery and spam handling."""
import time
from unittest import mock

from django.core import mail, signing
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.guest.forms import stamp
from apps.guest.models import ContactMessage, DeliveryStatus

from .factories import World

SMTP = {"EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend", "EMAIL_HOST": "smtp.example.com",
        "EMAIL_HOST_PASSWORD": "s3cret-app-password"}


def old_stamp(seconds=10):
    with mock.patch("time.time", return_value=time.time() - seconds):
        return stamp()


def valid(**kw):
    d = {"name": "Mariam Al Ali", "email": "mariam@example.edu", "organisation": "Example University", "phone": "+971 50 123 4567",
         "message": "We would like a demo for our facilities team.", "website": "", "started": old_stamp()}
    d.update(kw)
    return d


class PagesTests(TestCase):
    def test_pages_are_public_and_create_no_sign_in(self):
        for name, text in (("web:home", "Make campus reuse work"), ("guest:how", "One campus. More possibilities. Less waste."),
                           ("guest:contact", "Get in touch")):
            r = self.client.get(reverse(name))
            self.assertContains(r, text)
            self.assertContains(r, f'href="{reverse("access:login")}"')  # Sign in in the header
            self.assertNotIn("_auth_user_id", self.client.session)

    def test_signed_in_people_still_get_their_dashboard(self):
        self.client.force_login(World().requester)
        r = self.client.get(reverse("web:home"))
        self.assertContains(r, "Your work")
        self.assertNotContains(r, "Make campus reuse work")

    def test_home_content_and_the_built_in_film(self):
        r = self.client.get("/")
        self.assertContains(r, "Circular Campus helps universities find, share and reuse resources across departments")
        self.assertContains(r, '<source src="/static/video/circular-campus-film.mp4">')
        self.assertContains(r, 'poster="/static/video/circular-campus-poster.jpg"')
        self.assertContains(r, "Play the introduction video")
        self.assertContains(r, "g-btn g-btn-red")

    @override_settings(GUEST_HOME_VIDEO="")
    def test_placeholder_when_no_video_is_set(self):
        r = self.client.get("/")
        self.assertContains(r, "Introduction video")
        self.assertNotContains(r, "<video")

    @override_settings(GUEST_HOME_VIDEO="https://cdn.example.com/intro.mp4")
    def test_video_replaces_the_placeholder_from_settings(self):
        r = self.client.get("/")
        self.assertContains(r, '<source src="https://cdn.example.com/intro.mp4">')
        self.assertContains(r, "Play the introduction video")

    def test_how_it_works_steps_and_admin_section(self):
        r = self.client.get(reverse("guest:how"))
        for t in ("Somewhere on this campus, your next purchase is already gathering dust.", "Find an item", "List extra items",
                  "Claim and collect", "Explore Circular Campus with your team", "For administrators", "Demo data",
                  "img/guest/browse.png", "img/guest/step-find.png", "img/guest/admin.png"):
            self.assertContains(r, t)
        self.assertNotContains(r, "Track your impact")
        main = r.content.decode().split('<main id="main"', 1)[1].split("</main>", 1)[0]
        self.assertNotIn("Blueprint", main)   # only the menu links to it; the page itself stays about reuse

    @override_settings(BRAND_NAME="Ouro")
    def test_brand_name_comes_from_one_setting(self):
        r = self.client.get(reverse("guest:how"))
        self.assertContains(r, "Explore Ouro with your team")
        self.assertContains(r, "Ouro connects departments")

    @override_settings(GUEST_CTA_URL="/register/")
    def test_call_to_action_destination_is_configurable(self):
        self.assertContains(self.client.get("/"), 'href="/register/">Create your account')

    def test_cta_defaults_to_sign_in(self):
        self.assertContains(self.client.get("/"), f'href="{reverse("access:login")}">Create your account')

    def test_language_switch_is_full_and_remembered(self):
        r = self.client.post(reverse("set_language"), {"language": "ar", "next": "/how-it-works/"})
        self.assertIn("django_language", r.cookies)  # remembered for the next visit
        r = self.client.get(reverse("guest:how"))
        self.assertContains(r, 'dir="rtl"')
        self.assertContains(r, "حرم واحد. إمكانات أكثر. هدر أقل.")
        self.assertContains(r, 'value="ar" lang="ar" aria-pressed="true"')  # العربية (UAE flag) is the active choice
        self.assertContains(r, "img/guest/browse-ar.png")
        self.assertContains(self.client.get(reverse("guest:contact")), "ابقَ على تواصل")

    def test_contact_details_are_links(self):
        r = self.client.get(reverse("guest:contact"))
        self.assertContains(r, 'href="tel:+971505733540"')
        self.assertContains(r, 'href="mailto:circularcampus.team@gmail.com"')


class ContactFormTests(TestCase):
    def setUp(self):
        cache.clear()

    def post(self, data, **headers):
        return self.client.post(reverse("guest:contact"), data, **headers)

    def test_without_email_configured_it_saves_and_says_so(self):
        r = self.post(valid())
        self.assertContains(r, "Your message was saved, but it was not emailed.")
        self.assertNotContains(r, "has been sent")
        self.assertEqual(ContactMessage.objects.get().delivery, DeliveryStatus.NOT_CONFIGURED)

    @override_settings(**SMTP)
    def test_with_smtp_it_sends_to_the_recipient(self):
        sent = []
        with mock.patch("django.core.mail.EmailMessage.send", lambda self, fail_silently=False: sent.append(self) or 1):
            r = self.post(valid(), HTTP_HX_REQUEST="true")
        self.assertContains(r, "Thank you, your message has been sent.")
        m = sent[0]
        self.assertEqual(m.to, ["circularcampus.team@gmail.com"])
        self.assertEqual(m.reply_to, ["mariam@example.edu"])
        self.assertIn("Example University", m.body)
        self.assertEqual(ContactMessage.objects.get().delivery, DeliveryStatus.SENT)

    @override_settings(**SMTP)
    def test_smtp_failure_is_reported_and_the_message_kept(self):
        with mock.patch("django.core.mail.EmailMessage.send", side_effect=OSError("connection refused")):
            r = self.post(valid())
        self.assertContains(r, "Sorry, we couldn't send your message.")
        msg = ContactMessage.objects.get()
        self.assertEqual((msg.delivery, msg.delivery_error), (DeliveryStatus.FAILED, "connection refused"))

    @override_settings(**SMTP)
    def test_credentials_never_reach_the_browser(self):
        for url in ("/", reverse("guest:contact"), reverse("guest:how")):
            self.assertNotContains(self.client.get(url), "s3cret-app-password")

    def test_validation(self):
        r = self.post(valid(name="", email="not-an-email", organisation="", message="", phone="call me"))
        self.assertContains(r, "Please fix the fields marked below.")
        self.assertContains(r, 'aria-invalid="true"', count=5)
        self.assertContains(r, "Use digits, spaces and + - ( ) only.")
        self.assertFalse(ContactMessage.objects.exists())

    def test_phone_is_optional(self):
        self.post(valid(phone=""))
        self.assertEqual(ContactMessage.objects.get().phone, "")

    def test_honeypot_is_discarded_quietly(self):
        r = self.post(valid(website="http://spam.example"))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(ContactMessage.objects.exists())

    def test_too_fast_or_tampered_asks_to_send_again(self):
        for started in (stamp(), "garbage"):
            r = self.post(valid(started=started))
            self.assertContains(r, "Please check your details and press Send again.")
            self.assertContains(r, "Mariam Al Ali")  # what they typed is kept
        self.assertFalse(ContactMessage.objects.exists())

    def test_expired_form_asks_to_send_again(self):
        r = self.post(valid(started=old_stamp(7 * 3600)))
        self.assertContains(r, "press Send again")

    @override_settings(CONTACT_RATE_LIMIT=2)
    def test_rate_limit(self):
        for _i in range(2):
            self.post(valid())
        r = self.post(valid())
        self.assertContains(r, "Too many messages from this connection.")
        self.assertEqual(ContactMessage.objects.count(), 2)

    def test_arabic_messages(self):
        self.client.post(reverse("set_language"), {"language": "ar", "next": "/"})
        r = self.post(valid())
        self.assertContains(r, "حُفظت رسالتك، لكنها لم تُرسل بالبريد الإلكتروني.")
        self.assertEqual(ContactMessage.objects.get().language, "ar")


class GuestPricingTests(TestCase):
    """Pricing section on the guest home: one price table shared with the savings calculator."""

    def test_default_is_universities_without_vat(self):
        r = self.client.get(reverse("guest:pricing"))
        for text in ("Pricing", "Pick institution type", "AED 1,050", "AED 2,450", "AED 3,700",
                     "excluding VAT", "Over 10,000 employees?", "Estimate savings"):
            self.assertContains(r, text)
        self.assertContains(r, 'href="/impact/calculator/"')

    def test_type_and_vat_without_javascript(self):
        r = self.client.get(reverse("guest:pricing"), {"type": "hotel", "vat": "1"})
        for text in ("AED 577.50", "AED 1,470", "AED 2,205", "including 5% VAT", "Show prices without VAT"):
            self.assertContains(r, text)

    def test_charities_contact_for_reduced_price(self):
        r = self.client.get(reverse("guest:pricing"), {"type": "charity"})
        self.assertContains(r, "Contact for a reduced price", count=3 + 1)  # 3 cards + the data attribute
        self.assertNotContains(r, "<b>AED 1,050</b>")

    def test_unknown_type_falls_back(self):
        self.assertContains(self.client.get(reverse("guest:pricing"), {"type": "<script>"}), "AED 1,050")

    def test_pricing_is_its_own_page_not_a_home_section(self):
        home = self.client.get(reverse("web:home"))
        self.assertNotContains(home, 'id="pricing"')
        self.assertNotContains(home, "Over 10,000 employees?")
        self.assertContains(home, f'href="{reverse("guest:pricing")}"')
        self.assertContains(self.client.get(reverse("guest:pricing")), 'aria-current="page">Pricing</a>')

    def test_prices_match_the_calculator(self):
        from apps.guest import pricing
        from apps.sustainability.calculator import MONTHLY_PRICE
        for key, _label, group in pricing.TYPES:
            if group:
                self.assertEqual([r["ex"] for r in pricing.table()[key]], [f"AED {p:,}" for _u, p in MONTHLY_PRICE[group]])


class GuestBlueprintTests(TestCase):
    """Institution Blueprint preview on the guest home, built from the real templates."""

    def test_section_and_default_template(self):
        r = self.client.get(reverse("guest:blueprint"))
        for text in ("Institution Blueprint", "Start from a template", "College of Engineering", "High-value items go to the Dean",
                     "up to AED 5,000", "AI drafts the setup", "Create your account", "Talk to us"):
            self.assertContains(r, text)
        self.assertContains(r, 'data-bp-panel="school" hidden')

    def test_pick_hospital_without_javascript(self):
        r = self.client.get(reverse("guest:blueprint"), {"bp": "hospital"})
        self.assertContains(r, 'data-bp-panel="university" hidden')
        self.assertNotContains(r, 'data-bp-panel="hospital" hidden')
        self.assertContains(r, "Medical equipment over AED 10,000: Supply Chain")

    def test_preview_matches_the_real_templates(self):
        from apps.blueprint.services import TEMPLATES
        from apps.guest import blueprint_demo
        for t in blueprint_demo.templates():
            names, stack = [], list(t["tree"])
            while stack:
                n = stack.pop(0); names.append(n["name"]); stack[0:0] = n["children"]
            self.assertEqual(sorted(names), sorted(u["name"] for u in TEMPLATES[t["key"]]["units"]))
            self.assertEqual(len(t["roles"]), len(TEMPLATES[t["key"]]["roles"]))

    def test_blueprint_has_its_own_page_not_a_home_section(self):
        home = self.client.get(reverse("web:home")).content.decode()
        self.assertNotIn('id="blueprint"', home)
        self.assertIn('id="why"', home)
        self.assertContains(self.client.get(reverse("guest:blueprint")), 'aria-current="page">Blueprint</a>')

    def test_menu_order(self):
        import re
        html = self.client.get(reverse("web:home")).content.decode()
        nav = re.search(r'<nav class="g-nav".*?</nav>', html, re.S).group(0)
        self.assertEqual(re.findall(r">([^<]+)</a>", nav),
                         ["Home", "How it works", "Blueprint", "Calculator", "Pricing", "Contact"])
