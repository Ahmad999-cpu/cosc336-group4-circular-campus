"""Forms of the Matching module (Feature 3: check before buying)."""
from django import forms
from django.utils.translation import gettext_lazy as _

from apps.catalogue.models import Category
from apps.common.enums import PreferredCondition

INPUT = {"class": "input", "dir": "auto"}  # dir=auto: English typed on an Arabic page stays readable


class ProcurementForm(forms.Form):
    description = forms.CharField(label=_("What do you plan to buy?"), min_length=2, max_length=500,
                                  widget=forms.Textarea(attrs={**INPUT, "rows": 2, "placeholder": _("e.g. Two 24-inch monitors for the robotics lab")}))
    category = forms.ModelChoiceField(label=_("Category"), queryset=Category.objects.all().order_by("name"), required=False,
                                      empty_label=_("Any category"), widget=forms.Select(attrs=INPUT))
    quantity = forms.IntegerField(label=_("How many"), min_value=1, max_value=999, initial=1,
                                  widget=forms.NumberInput(attrs={**INPUT, "inputmode": "numeric"}))
    specifications = forms.CharField(label=_("Must-have specifications"), required=False, max_length=500,
                                     widget=forms.TextInput(attrs={**INPUT, "placeholder": _("e.g. 24 inch, HDMI")}))
    condition = forms.ChoiceField(label=_("Lowest acceptable condition"), choices=PreferredCondition.choices, initial=PreferredCondition.ANY, required=False,
                                  widget=forms.Select(attrs=INPUT))
    campus = forms.CharField(label=_("Deliver to campus"), required=False, max_length=100, widget=forms.TextInput(attrs=INPUT))
    needed_by = forms.DateField(label=_("Needed by"), required=False, widget=forms.DateInput(attrs={**INPUT, "type": "date"}))
    unit_price = forms.DecimalField(label=_("Estimated purchase price per unit (AED)"), required=False, min_value=0, max_digits=12,
                                    decimal_places=2, widget=forms.NumberInput(attrs={**INPUT, "step": "1", "inputmode": "decimal"}),
                                    help_text=_("Optional. Empty = each item's estimated value is used as the new price."))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].label_from_instance = lambda c: c.path()


class SavedNeedForm(forms.Form):
    """Phase 5: a need to keep watching for."""

    description = forms.CharField(label=_("What do you need, and what for?"), min_length=3, max_length=300,
                                  widget=forms.Textarea(attrs={**INPUT, "rows": 2, "placeholder": _("e.g. Two monitors, at least 24 inches, for the robotics lab")}))
    category = forms.ModelChoiceField(label=_("Category"), queryset=Category.objects.all().order_by("name"), required=False,
                                      empty_label=_("Any category"), widget=forms.Select(attrs=INPUT))
    quantity = forms.IntegerField(label=_("How many"), min_value=1, max_value=999, initial=1, widget=forms.NumberInput(attrs={**INPUT, "inputmode": "numeric"}))
    specifications = forms.CharField(label=_("Desired specifications"), required=False, max_length=300,
                                     widget=forms.TextInput(attrs={**INPUT, "placeholder": _("e.g. 24 inch or larger, HDMI")}))
    preferred_condition = forms.ChoiceField(label=_("Lowest acceptable condition"), choices=PreferredCondition.choices, required=False,
                                            initial=PreferredCondition.ANY, widget=forms.Select(attrs=INPUT))
    campus = forms.CharField(label=_("Preferred campus"), required=False, max_length=100, widget=forms.TextInput(attrs=INPUT))
    needed_by = forms.DateField(label=_("Needed by (optional)"), required=False, widget=forms.DateInput(attrs={**INPUT, "type": "date"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].label_from_instance = lambda c: c.path()
