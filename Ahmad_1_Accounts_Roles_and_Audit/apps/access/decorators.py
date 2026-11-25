"""View guards. They decide who may open a screen; services still check each action (C1)."""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .permissions import has_any


def needs(action: str):
    """Allow the view only to signed-in people who may do `action` somewhere."""
    def deco(view):
        @login_required
        @wraps(view)
        def inner(request, *args, **kwargs):
            if not has_any(request.user, action):
                raise PermissionDenied(action)
            return view(request, *args, **kwargs)
        return inner
    return deco
