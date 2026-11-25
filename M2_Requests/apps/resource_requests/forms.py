from datetime import date

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.catalogue.models import Category
from apps.common.enums import PreferredCondition, Urgency

INPUT = {"class": "input"}


class RequestForm(forms.Form):
    department = forms.ModelChoiceField(label=_("For which unit"), queryset=None, widget=forms.Select(attrs=INPUT))
    category = forms.ModelChoiceField(label=_("Category"), queryset=Category.objects.order_by("name"), required=False,
                                      empty_label=_("Choose a category"), widget=forms.Select(attrs=INPUT))
    quantity = forms.IntegerField(label=_("Quantity"), min_value=1, max_value=999, initial=1,
                                  widget=forms.NumberInput(attrs={"inputmode": "numeric", "aria-label": _("Quantity")}))
    purpose = forms.CharField(label=_("What it's for"), max_length=500, widget=forms.Textarea(attrs={**INPUT, "rows": 3}),
                              help_text=_("One or two sentences. The approver decides from this."))
    specifications = forms.CharField(label=_("Must-have specifications"), required=False, max_length=500,
                                     widget=forms.Textarea(attrs={**INPUT, "rows": 2, "placeholder": _("e.g. HDMI input, at least 24 inches")}))
    preferred_condition = forms.ChoiceField(label=_("Lowest acceptable condition"), choices=PreferredCondition.choices,
                                            initial=PreferredCondition.ANY, widget=forms.Select(attrs=INPUT))
    urgency = forms.ChoiceField(label=_("Urgency"), choices=Urgency.choices, initial=Urgency.MEDIUM, widget=forms.Select(attrs=INPUT))
    required_date = forms.DateField(label=_("Needed by"), required=False, widget=forms.DateInput(attrs={**INPUT, "type": "date"}, format="%Y-%m-%d"))
    destination_campus = forms.CharField(label=_("Deliver to campus"), max_length=100, widget=forms.TextInput(attrs=INPUT))
    destination_building = forms.CharField(label=_("Building"), max_length=100, required=False, widget=forms.TextInput(attrs=INPUT))
    destination_room = forms.CharField(label=_("Room"), max_length=50, required=False, widget=forms.TextInput(attrs=INPUT))
    idempotency_key = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, *args, units=None, asset=None, editing=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.asset = asset
        self.fields["department"].queryset = units
        self.fields["required_date"].widget.attrs["min"] = date.today().isoformat()
        if asset is not None:
            del self.fields["category"]
        if editing:
            for name in ("department", "idempotency_key"):
                del self.fields[name]

    def clean_required_date(self):
        d = self.cleaned_data.get("required_date")
        if d and d < date.today():
            raise forms.ValidationError(_("Pick today or a later date."))
        return d

    def clean_quantity(self):
        q = self.cleaned_data["quantity"]
        if self.asset is not None and q > self.asset.unreserved_quantity:
            raise forms.ValidationError(_("Only %(n)s free.") % {"n": self.asset.unreserved_quantity})
        return q

    def clean(self):
        data = super().clean()
        if self.asset is None and "category" in self.fields and not data.get("category"):
            self.add_error("category", _("Choose a category, or start from an item in Browse."))
        return data


class CancelForm(forms.Form):
    reason = forms.CharField(label=_("Why are you cancelling?"), max_length=300, widget=forms.Textarea(attrs={**INPUT, "rows": 2}))
