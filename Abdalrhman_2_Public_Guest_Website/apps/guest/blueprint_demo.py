"""The interactive Institution Blueprint preview on the guest home.

Built from the real templates in apps.blueprint.services.TEMPLATES, so the preview shows exactly what an
institution gets when it starts from that template. Only display strings are added here (for translation).
"""
from django.utils.formats import number_format
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from apps.blueprint.services import TEMPLATES

CHOICES = [("university", _("University")), ("school", _("School")), ("hospital", _("Hospital"))]
DEFAULT = "university"

# Every name used by the three templates, marked so makemessages picks them up for Arabic.
_STRINGS = [
    _("University"), _("College of Engineering"), _("College of Science"), _("Library"), _("Facilities"),
    _("Student Clubs"), _("College"), _("Service"), _("Student life"),
    _("School"), _("Primary"), _("Secondary"), _("Science labs"), _("Operations"), _("Section"), _("Department"),
    _("Hospital"), _("Clinical services"), _("Outpatients"), _("Radiology"), _("Biomedical engineering"),
    _("Administration"), _("Division"), _("Ward"),
    _("Requester"), _("Asset Custodian"), _("Head of Department"), _("Dean"), _("Facilities Coordinator"),
    _("Sustainability Officer"), _("Teacher"), _("Lab Technician"), _("Section Head"), _("Principal"),
    _("Operations Officer"), _("Staff Member"), _("Equipment Custodian"), _("Biomedical Engineer"),
    _("Department Manager"), _("Supply Chain"),
    _("High-value items go to the Dean"), _("Everything else: Head of Department"),
    _("Over AED 2,000 goes to the Principal"), _("Section heads approve the rest"),
    _("Medical equipment over AED 10,000: Supply Chain"), _("Department managers approve the rest"),
]


def _tree(units, parent=None):
    return [{"name": gettext(u["name"]), "kind": gettext(u["unit_type"]), "children": _tree(units, u["name"])}
            for u in units if u["parent"] == parent]


def templates():
    out = []
    for key, label in CHOICES:
        t = TEMPLATES[key]
        out.append({
            "key": key, "label": label,
            "tree": _tree(t["units"]),
            "roles": [{"name": gettext(r["name"]),
                       "limit": number_format(r["approval_limit"], 0, force_grouping=True) if r["approval_limit"] else None}
                      for r in t["roles"]],
            "rules": [gettext(r["name"]) for r in sorted(t["rules"], key=lambda r: r["priority"])],
        })
    return out


def context(key: str | None):
    key = key if key in dict(CHOICES) else DEFAULT
    return {"choices": CHOICES, "active": key, "templates": templates()}
