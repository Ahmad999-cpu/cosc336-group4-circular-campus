"""Template context on every page: the menu, the signed-in person, and the notification bell."""
from django.urls import NoReverseMatch, reverse
from django.utils.module_loading import import_string

from apps.access.permissions import has_any

from .navigation import NAV


OWNED_PATHS = [("/assets/import/", "assets"), ("/assets/questions/", "assets")]


def _count(path, user):
    if not path:
        return 0
    try:
        return import_string(path.replace(":", "."))(user)
    except Exception:  # a module that is not built yet, or a failing count, never breaks the page
        return 0


def navigation(request):
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {}
    items = []
    for key, label, url_name, perm, count_path in NAV:
        try:
            url = reverse(url_name)
        except NoReverseMatch:
            continue
        if perm and not has_any(user, perm):
            continue
        items.append({"key": key, "label": label, "url": url, "count": _count(count_path, user), "active": False})
    # Only the longest matching menu address is current (/assets/ours/ must not also light up /assets/).
    matches = [i for i in items if request.path.startswith(i["url"]) and i["url"] != "/"]
    owner = next((k for prefix, k in OWNED_PATHS if request.path.startswith(prefix)), None)  # pages under another item's address
    if owner and any(i["key"] == owner for i in items):
        matches = [i for i in items if i["key"] == owner]
    if matches:
        max(matches, key=lambda i: len(i["url"]))["active"] = True

    from apps.notifications.models import Channel, Notification

    mine = Notification.objects.filter(recipient=user, channel=Channel.IN_APP)
    roles = [ra.role.display_name for ra in user.role_assignments.filter(active=True).select_related("role")]
    try:
        all_notes_url = reverse("notifications:index")
    except NoReverseMatch:
        all_notes_url = ""
    return {
        "nav_items": items,
        "recent_notifications": list(mine[:6]),
        "unread_notifications": mine.filter(read_at__isnull=True).count(),
        "all_notes_url": all_notes_url,
        "my_roles": roles,
    }
