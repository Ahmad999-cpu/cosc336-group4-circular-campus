"""Contact form with simple spam protection: a hidden honeypot field and a signed 'form shown at' time."""
import time

from django import forms
from django.core import signing
from django.utils.translation import gettext_lazy as _

INPUT = {"class": "input", "dir": "auto"}
MIN_SECONDS = 3          # people take longer than this to fill the form; most bots don't
MAX_AGE = 60 * 60 * 6    # the page was open at most six hours


def stamp() -> str:
    return signing.dumps(int(time.time()), salt="guest-contact")


class ContactForm(forms.Form):
    name = forms.CharField(label=_("Your name"), max_length=120, widget=forms.TextInput(attrs={**INPUT, "autocomplete": "name"}))
    email = forms.EmailField(label=_("Email address"), max_length=254,
                             widget=forms.EmailInput(attrs={"class": "input", "dir": "ltr", "autocomplete": "email"}))
    organisation = forms.CharField(label=_("Organisation name"), max_length=160,
                                   widget=forms.TextInput(attrs={**INPUT, "autocomplete": "organization"}))
    phone = forms.CharField(label=_("Phone number (optional)"), max_length=40, required=False,
                            widget=forms.TextInput(attrs={"class": "input", "dir": "ltr", "autocomplete": "tel", "inputmode": "tel"}))
    message = forms.CharField(label=_("Message"), min_length=10, max_length=4000,
                              widget=forms.Textarea(attrs={**INPUT, "rows": 6}))
    website = forms.CharField(required=False, label="Website",  # honeypot: hidden from people, filled by bots
                              widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}))
    started = forms.CharField(widget=forms.HiddenInput)

    def clean_phone(self):
        p = self.cleaned_data.get("phone", "").strip()
        if p and not all(c.isdigit() or c in "+ -()" for c in p):
            raise forms.ValidationError(_("Use digits, spaces and + - ( ) only."))
        return p

    def clean_name(self):
        return " ".join(self.cleaned_data["name"].split())

    def spam_check(self) -> str:
        """'' = looks human. 'honeypot' = a bot filled the hidden field (discarded quietly).
        'fast' / 'expired' = ask the person to send again (a real person is told, never silently dropped)."""
        if self.data.get("website"):
            return "honeypot"
        try:
            shown = signing.loads(self.data.get("started", ""), salt="guest-contact", max_age=MAX_AGE)
        except signing.SignatureExpired:
            return "expired"
        except signing.BadSignature:
            return "fast"
        return "fast" if time.time() - shown < MIN_SECONDS else ""
