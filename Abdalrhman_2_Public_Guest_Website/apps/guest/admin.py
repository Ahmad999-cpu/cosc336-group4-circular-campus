from django.contrib import admin

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("created_at", "name", "organisation", "email", "delivery")
    list_filter = ("delivery",)
    search_fields = ("name", "organisation", "email", "message")
    readonly_fields = [f.name for f in ContactMessage._meta.fields]
