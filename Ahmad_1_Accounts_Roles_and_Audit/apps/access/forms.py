from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

from .models import Department, Role, User


class SignInForm(AuthenticationForm):
    username = forms.EmailField(label=_("Work e-mail"), widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email", "class": "input"}))
    password = forms.CharField(label=_("Password"), strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "current-password", "class": "input"}))

    error_messages = {
        "invalid_login": _("E-mail or password is incorrect. Check both and try again."),
        "inactive": _("This account is not active. Ask a System Administrator to reactivate it."),
    }


class PersonForm(forms.Form):
    full_name = forms.CharField(label=_("Full name"), max_length=200, widget=forms.TextInput(attrs={"class": "input", "autocomplete": "off"}))
    email = forms.EmailField(label=_("Work e-mail"), widget=forms.EmailInput(attrs={"class": "input", "autocomplete": "off"}))
    department = forms.ModelChoiceField(label=_("Unit"), queryset=Department.objects.filter(status="ACTIVE"), required=False,
                                        empty_label=_("No unit"), widget=forms.Select(attrs={"class": "input"}))


class NewPersonForm(PersonForm):
    password = forms.CharField(label=_("First password"), strip=False, help_text=_("Share it privately; they change it after signing in."),
                               widget=forms.PasswordInput(attrs={"class": "input", "autocomplete": "new-password"}))

    def clean_password(self):
        pw = self.cleaned_data["password"]
        validate_password(pw)
        return pw


class RoleForm(forms.Form):
    role = forms.ModelChoiceField(label=_("Role"), queryset=Role.objects.order_by("name"), widget=forms.Select(attrs={"class": "input"}))
    scope = forms.ModelChoiceField(label=_("For which unit"), queryset=Department.objects.filter(status="ACTIVE"), required=False,
                                   empty_label=_("The whole institution"), widget=forms.Select(attrs={"class": "input"}),
                                   help_text=_("A unit includes every unit below it."))


class PeopleFilter(forms.Form):
    q = forms.CharField(required=False, label=_("Search"), widget=forms.TextInput(attrs={"class": "input", "type": "search", "placeholder": _("Name or e-mail")}))
    status = forms.ChoiceField(required=False, label=_("Status"), choices=[("", _("All"))] + list(User._meta.get_field("account_status").choices),
                               widget=forms.Select(attrs={"class": "input"}))
