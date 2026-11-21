from django import forms
from django.utils.translation import gettext_lazy as _

from apps.access.permissions import units_for
from apps.common.enums import Condition

from .models import Asset, AssetState, Category

INPUT = {"class": "input"}


class AssetForm(forms.ModelForm):
    tags = forms.CharField(label=_("Tags"), required=False, help_text=_("Comma-separated words people might search for."),
                           widget=forms.TextInput(attrs=INPUT))
    photo = forms.FileField(label=_("Photo or document"), required=False,
                            help_text=_("JPG, PNG, WebP or PDF, up to 10 MB."),
                            widget=forms.ClearableFileInput(attrs={"class": "input", "accept": "image/jpeg,image/png,image/webp,application/pdf"}))

    class Meta:
        model = Asset
        fields = ["name", "category", "owner_department", "quantity", "condition", "location_campus", "location_building",
                  "location_room", "purchase_date", "estimated_value", "description", "specifications", "serial_number"]
        labels = {
            "name": _("Name"), "category": _("Category"), "owner_department": _("Owning unit"), "quantity": _("Quantity"),
            "condition": _("Condition"), "location_campus": _("Campus"), "location_building": _("Building"),
            "location_room": _("Room"), "purchase_date": _("Purchase date"), "estimated_value": _("Value of one unit (AED)"),
            "description": _("Description"), "specifications": _("Specifications"), "serial_number": _("Serial number"),
        }
        help_texts = {"estimated_value": ""}
        widgets = {
            "name": forms.TextInput(attrs={**INPUT, "placeholder": _("e.g. Dell 24-inch monitor")}),
            "category": forms.Select(attrs=INPUT), "owner_department": forms.Select(attrs=INPUT),
            "quantity": forms.NumberInput(attrs={**INPUT, "min": 1}), "condition": forms.Select(attrs=INPUT),
            "location_campus": forms.TextInput(attrs={**INPUT, "list": "campus-list"}),
            "location_building": forms.TextInput(attrs=INPUT), "location_room": forms.TextInput(attrs=INPUT),
            "purchase_date": forms.DateInput(attrs={**INPUT, "type": "date"}, format="%Y-%m-%d"),
            "estimated_value": forms.NumberInput(attrs={**INPUT, "min": 0, "step": "0.01"}),
            "description": forms.Textarea(attrs={**INPUT, "rows": 3}), "specifications": forms.Textarea(attrs={**INPUT, "rows": 2}),
            "serial_number": forms.TextInput(attrs=INPUT),
        }

    def __init__(self, *args, user=None, editing=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["owner_department"].queryset = units_for(user, "asset.register")
        self.fields["category"].queryset = Category.objects.order_by("name")
        self.fields["category"].label_from_instance = lambda c: c.path()
        self.fields["category"].empty_label = _("Choose a category")
        if "owner_department" in self.fields:
            self.fields["owner_department"].empty_label = _("Choose a unit")
            units = self.fields["owner_department"].queryset
            if units.count() == 1:
                self.initial.setdefault("owner_department", units.first().pk)
        if editing:  # owner and quantity change through workflows, not the edit form
            del self.fields["owner_department"]
            del self.fields["quantity"]


class BrowseFilter(forms.Form):
    q = forms.CharField(required=False, label=_("Search"), widget=forms.TextInput(attrs={**INPUT, "type": "search", "placeholder": _("Name, tag, unit or serial number")}))
    category = forms.ModelChoiceField(required=False, label=_("Category"), queryset=Category.objects.filter(parent__isnull=True).order_by("name"),
                                      empty_label=_("All"), widget=forms.Select(attrs=INPUT))
    condition = forms.ChoiceField(required=False, label=_("Condition"), choices=[("", _("All"))] + list(Condition.choices), widget=forms.Select(attrs=INPUT))
    campus = forms.ChoiceField(required=False, label=_("Campus"), choices=[("", _("All"))], widget=forms.Select(attrs=INPUT))
    max_age_years = forms.ChoiceField(required=False, label=_("Age"), widget=forms.Select(attrs=INPUT),
                                      choices=[("", _("Any age")), ("1", _("Under 1 year")), ("3", _("Under 3 years")), ("5", _("Under 5 years"))])
    sort = forms.ChoiceField(required=False, label=_("Sort"), widget=forms.Select(attrs=INPUT),
                             choices=[("units", _("Most units")), ("newest", _("Newest")), ("value", _("Highest value")), ("name", _("Name"))])

    def __init__(self, *args, campuses=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["campus"].choices = [("", _("All"))] + [(c, c) for c in campuses]


class MineFilter(forms.Form):
    q = forms.CharField(required=False, label=_("Search"), widget=forms.TextInput(attrs={**INPUT, "type": "search", "placeholder": _("Name, tag or serial number")}))
    state = forms.ChoiceField(required=False, label=_("State"), choices=[("", _("All"))] + list(AssetState.choices), widget=forms.Select(attrs=INPUT))


class UpcomingForm(forms.Form):
    """Phase 6: when an item is expected to be free for reuse."""

    when = forms.DateField(label=_("Expected to be available from"), widget=forms.DateInput(attrs={**INPUT, "type": "date"}))
    note = forms.CharField(label=_("Note (optional)"), required=False, max_length=200,
                           widget=forms.TextInput(attrs={**INPUT, "dir": "auto", "placeholder": _("e.g. after the office refit")}))
