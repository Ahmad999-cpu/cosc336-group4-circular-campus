from django.contrib import admin

from .models import Asset, AssetAttachment, AssetTag, Category


class TagInline(admin.TabularInline):
    model = AssetTag
    extra = 0


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "owner_department", "quantity", "available_quantity", "reserved_quantity",
                    "lifecycle_state", "publication_status")
    list_filter = ("lifecycle_state", "publication_status", "category")
    search_fields = ("name", "description", "serial_number")
    readonly_fields = ("lifecycle_state", "publication_status", "row_version")
    inlines = [TagInline]


admin.site.register([Category, AssetAttachment])
