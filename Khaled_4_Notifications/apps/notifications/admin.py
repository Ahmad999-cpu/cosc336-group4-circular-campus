from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "channel", "event_type", "delivery_status", "created_at")
    list_filter = ("channel", "delivery_status", "event_type")
