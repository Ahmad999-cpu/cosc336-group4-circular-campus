"""The main menu. Each module adds its screen here when its URL exists.

(key, label, url name, permission needed anywhere or None, optional "module.path:function" returning a badge count)
Entries whose URL is not built yet are skipped automatically, so the menu grows as modules land.
"""
from django.utils.translation import gettext_lazy as _

NAV = [
    ("find", _("Find"), "matching:find", "request.submit", None),
    ("browse", _("Browse"), "catalogue:browse", None, None),
    ("needs", _("Saved needs"), "matching:saved", "request.submit", None),
    ("requests", _("My requests"), "resource_requests:mine", "request.submit", "apps.resource_requests.services:attention_count"),
    ("assets", _("Our assets"), "catalogue:mine", "asset.register", "apps.catalogue.services:unanswered_count"),
    ("approvals", _("Approvals"), "transfers:queue", "request.approve", "apps.transfers.services:pending_count"),
    ("transfers", _("Transfers"), "transfers:board", "transfer.dispatch", "apps.transfers.services:to_dispatch_count"),
    ("maintenance", _("Maintenance"), "lifecycle:maintenance", "maintenance.record", "apps.lifecycle.services:attention_count"),
    ("impact", _("Impact"), "sustainability:dashboard", None, None),
    ("reports", _("Reports"), "reporting:index", "reports.view", None),
    ("demand", _("Demand"), "reporting:demand", "reports.view", None),
    ("people", _("People"), "access:people", "admin.users", None),
    ("setup", _("Setup"), "blueprint:index", "admin.blueprint", None),
]
