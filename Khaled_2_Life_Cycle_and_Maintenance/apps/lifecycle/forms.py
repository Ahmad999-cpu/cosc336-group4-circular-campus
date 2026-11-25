from django import forms
from django.utils.translation import gettext_lazy as _

from apps.common.enums import Condition, Urgency

from .models import EOL_ACTIONS, RepairOutcome, Severity

INPUT = {"class": "input"}


class ProblemForm(forms.Form):
    kind = forms.ChoiceField(label=_("What do you need?"), choices=[("defect", _("Report a defect")), ("inspection", _("Ask for an inspection"))],
                             widget=forms.Select(attrs=INPUT))
    description = forms.CharField(label=_("What's wrong?"), max_length=1000, widget=forms.Textarea(attrs={**INPUT, "rows": 3}))
    severity = forms.ChoiceField(label=_("Severity"), choices=Severity.choices, initial=Severity.MEDIUM, widget=forms.Select(attrs=INPUT))
    condition = forms.ChoiceField(label=_("Condition now"), choices=Condition.choices, widget=forms.Select(attrs=INPUT))
    urgency = forms.ChoiceField(label=_("Urgency"), choices=Urgency.choices, initial=Urgency.MEDIUM, widget=forms.Select(attrs=INPUT))
    preferred_date = forms.DateField(label=_("Inspect by"), required=False, widget=forms.DateInput(attrs={**INPUT, "type": "date"}))


class RepairForm(forms.Form):
    description = forms.CharField(label=_("What was repaired"), max_length=300, widget=forms.TextInput(attrs=INPUT))
    actions = forms.CharField(label=_("Work done"), required=False, max_length=1000, widget=forms.Textarea(attrs={**INPUT, "rows": 2}))
    outcome = forms.ChoiceField(label=_("Result"), choices=RepairOutcome.choices, widget=forms.Select(attrs=INPUT))
    cost = forms.DecimalField(label=_("Cost (AED)"), min_value=0, max_digits=12, decimal_places=2, initial=0,
                              widget=forms.NumberInput(attrs={**INPUT, "step": "0.01"}))


class ReturnForm(forms.Form):
    condition = forms.ChoiceField(label=_("Condition after repair"), choices=Condition.choices, widget=forms.Select(attrs=INPUT))


class EolForm(forms.Form):
    action = forms.ChoiceField(label=_("Action"), choices=[(a.value, a.label) for a in EOL_ACTIONS], widget=forms.Select(attrs=INPUT),
                               help_text=_("Dispose only when it can't be reused, donated or recycled."))
    reason = forms.CharField(label=_("Why"), max_length=1000, widget=forms.Textarea(attrs={**INPUT, "rows": 3}))
