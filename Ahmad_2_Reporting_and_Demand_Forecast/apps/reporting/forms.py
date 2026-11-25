from datetime import timedelta

from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.access.permissions import units_for

from .models import ReportType
from .services import Filters

INPUT = {"class": "input"}
DATE = {**INPUT, "type": "date"}
REPORT_CHOICES = [(ReportType.REQUESTS_TRANSFERS, _("Requests and transfers")), (ReportType.AVAILABLE_ASSETS, _("Available items"))]


class ReportFilter(forms.Form):
    type = forms.ChoiceField(choices=REPORT_CHOICES, required=False)
    start = forms.DateField(required=False, label=_("From"), widget=forms.DateInput(attrs=DATE, format="%Y-%m-%d"))
    end = forms.DateField(required=False, label=_("To"), widget=forms.DateInput(attrs=DATE, format="%Y-%m-%d"))
    unit = forms.ModelChoiceField(required=False, label=_("Unit"), queryset=None, empty_label=_("All my units"),
                                  widget=forms.Select(attrs=INPUT))

    def __init__(self, data=None, *, user, **kw):
        today = timezone.localdate()
        initial = {"type": ReportType.REQUESTS_TRANSFERS, "start": today - timedelta(days=29), "end": today}
        if data is not None:
            data = {**{k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in initial.items()},
                    **{k: v for k, v in data.items() if v not in (None, "")}}
        super().__init__(data, initial=initial, **kw)
        self.fields["unit"].queryset = units_for(user, "reports.view")

    def clean(self):
        d = super().clean()
        s, e = d.get("start"), d.get("end")
        if s and e and s > e:
            raise forms.ValidationError(_("The start date is after the end date."))
        if s and e and (e - s).days > 731:
            raise forms.ValidationError(_("Pick a period of two years or less."))
        return d

    def filters(self) -> Filters:
        d = self.cleaned_data if self.is_bound and self.is_valid() else {}
        f = Filters.default(d.get("type") or ReportType.REQUESTS_TRANSFERS)
        if d:
            f.start, f.end = d.get("start") or f.start, d.get("end") or f.end
            f.unit_id = str(d["unit"].pk) if d.get("unit") else ""
        return f
