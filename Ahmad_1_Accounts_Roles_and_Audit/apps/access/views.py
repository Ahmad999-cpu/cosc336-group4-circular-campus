"""Screens of the Users & Access module: sign in, demo sign-in, people and roles, password."""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, views as auth_views
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.common.errors import ValidationFailed
from apps.web.htmx import is_htmx, with_toast

from . import services
from .decorators import needs
from .forms import NewPersonForm, PeopleFilter, PersonForm, RoleForm, SignInForm
from .models import AccountStatus, RoleAssignment, User

DEMO_ACCOUNTS = [  # created by `manage.py seed_demo`; offered on the sign-in page only when DEBUG is on
    ("club@demo.local", "Requester, Student Clubs"), ("requester@demo.local", "Requester, Mechanical Eng."),
    ("custodian@demo.local", "Custodian, Engineering"), ("lina@demo.local", "Custodian, Library and Science"),
    ("approver@demo.local", "Approver, Engineering"), ("dean@demo.local", "Approver, whole university"),
    ("facilities@demo.local", "Facilities"), ("tech@demo.local", "Maintenance Staff"),
    ("sustain@demo.local", "Sustainability Officer"), ("admin@demo.local", "System Administrator"),
]


class SignInView(auth_views.LoginView):
    template_name = "access/login.html"
    authentication_form = SignInForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if settings.DEBUG:
            found = {u.email: u for u in User.objects.filter(email__in=[e for e, _r in DEMO_ACCOUNTS])}
            ctx["demo_accounts"] = [(found[e], label) for e, label in DEMO_ACCOUNTS if e in found and found[e].is_active]
        return ctx


@require_POST
def demo_sign_in(request):
    """One-click sign-in as a demo user. Exists only while DEBUG is on (development and the lab demo)."""
    if not settings.DEBUG:
        raise Http404()
    email = request.POST.get("email", "")
    if email not in {e for e, _r in DEMO_ACCOUNTS}:
        raise Http404()
    user = get_object_or_404(User, email=email)
    if not user.is_active:
        raise Http404()
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    nxt = request.POST.get("next") or ""
    # A QR label sends people here with ?next=<asset page>; only ever follow addresses on this site.
    if not url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        nxt = ""
    return redirect(nxt or "web:home")


@needs("admin.users")
def people(request):
    """UC-44: everyone with an account, their unit, status and roles."""
    f = PeopleFilter(request.GET or None)
    qs = User.objects.select_related("department").prefetch_related(
        Prefetch("role_assignments", queryset=RoleAssignment.objects.filter(active=True).select_related("role", "scope_department"), to_attr="active_roles")
    ).order_by("full_name")
    if f.is_valid():
        if f.cleaned_data["q"]:
            q = f.cleaned_data["q"]
            qs = qs.filter(Q(full_name__icontains=q) | Q(email__icontains=q))
        if f.cleaned_data["status"]:
            qs = qs.filter(account_status=f.cleaned_data["status"])
    ctx = {"people": qs[:200], "filter": f, "statuses": AccountStatus}
    if is_htmx(request) and request.GET.get("partial"):
        return render(request, "access/_people_rows.html", ctx)
    return render(request, "access/people.html", ctx)


@needs("admin.users")
def person_new(request):
    form = NewPersonForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            u = services.create_user(request.user, **form.cleaned_data)
        except ValidationFailed as e:
            form.add_error("email", str(e))
        else:
            messages.success(request, _("Account created for %(name)s. Now give them a role.") % {"name": u.full_name})
            return _back_to(request, reverse("access:person", args=[u.pk]))
    return render(request, "access/_person_form.html", {"form": form, "new": True})


@needs("admin.users")
def person(request, pk):
    """Side panel: edit details, change status, add and remove roles."""
    u = get_object_or_404(User.objects.select_related("department"), pk=pk)
    form = PersonForm(request.POST or None, initial={"full_name": u.full_name, "email": u.email, "department": u.department})
    if request.method == "POST" and form.is_valid():
        try:
            services.update_user(request.user, u, **form.cleaned_data)
        except ValidationFailed as e:
            form.add_error("email", str(e))
        else:
            return _refresh_people(request, _("Saved %(name)s.") % {"name": u.full_name})
    return render(request, "access/_person_panel.html", _panel_ctx(u, form))


def _panel_ctx(u, form=None, role_form=None):
    return {
        "person": u, "form": form or PersonForm(initial={"full_name": u.full_name, "email": u.email, "department": u.department}),
        "role_form": role_form or RoleForm(),
        "assignments": u.role_assignments.filter(active=True).select_related("role", "scope_department"),
        "statuses": AccountStatus,
    }


@needs("admin.users")
@require_POST
def person_status(request, pk):
    u = get_object_or_404(User, pk=pk)
    services.set_status(request.user, u, request.POST.get("status", ""))
    label = dict(AccountStatus.choices)[u.account_status]
    return _refresh_people(request, _("%(name)s is now %(status)s.") % {"name": u.full_name, "status": str(label).lower()}, keep_panel=u)


@needs("admin.users")
@require_POST
def role_assign(request, pk):
    u = get_object_or_404(User, pk=pk)
    rf = RoleForm(request.POST)
    if rf.is_valid():
        try:
            ra = services.assign_role(request.user, u, rf.cleaned_data["role"], rf.cleaned_data["scope"])
        except ValidationFailed as e:
            rf.add_error("role", str(e))
        else:
            where = ra.scope_department.name if ra.scope_department else _("the whole institution")
            return _refresh_people(request, _("%(name)s is now %(role)s for %(where)s.") % {"name": u.full_name, "role": ra.role.name, "where": where}, keep_panel=u)
    return render(request, "access/_person_panel.html", _panel_ctx(u, role_form=rf))


@needs("admin.users")
@require_POST
def role_revoke(request, pk, assignment_pk):
    ra = get_object_or_404(RoleAssignment, pk=assignment_pk, user_id=pk)
    services.revoke_role(request.user, ra)
    return _refresh_people(request, _("Removed %(role)s from %(name)s.") % {"role": ra.role.name, "name": ra.user.full_name}, keep_panel=ra.user)


def _back_to(request, panel_url):
    if is_htmx(request):
        resp = HttpResponse(status=204)
        resp["HX-Redirect"] = reverse("access:people") + "?open=" + panel_url
        return resp
    return redirect("access:people")


def _refresh_people(request, text, keep_panel=None):
    """After a change: re-render the panel (if open) and tell the list to reload its rows."""
    if not is_htmx(request):
        messages.success(request, text)
        return redirect("access:people")
    if keep_panel is not None:
        resp = render(request, "access/_person_panel.html", _panel_ctx(keep_panel))
    else:
        resp = HttpResponse(status=204)
        resp["HX-Reswap"] = "none"
    resp = with_toast(resp, text, ok=True, close_drawer=keep_panel is None)
    resp["HX-Trigger"] = "people-changed"
    return resp


class PasswordChange(auth_views.PasswordChangeView):
    template_name = "access/password.html"
    success_url = reverse_lazy("web:home")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for f in form.fields.values():
            f.widget.attrs["class"] = "input"
        return form

    def form_valid(self, form):
        messages.success(self.request, _("Password changed."))
        return super().form_valid(form)


password_change = login_required(PasswordChange.as_view())
