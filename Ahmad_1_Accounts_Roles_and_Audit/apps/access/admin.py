from django.contrib import admin

from .models import Department, Permission, Role, RoleAssignment, User, UserSession


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "department", "account_status")
    search_fields = ("email", "full_name")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "approval_limit")
    filter_horizontal = ("permissions",)


admin.site.register([Department, Permission, RoleAssignment, UserSession])
