from django.contrib import admin

from .models import AssistantDraft, Reservation, ReservationEvent, ResourceRequest


@admin.register(ResourceRequest)
class ResourceRequestAdmin(admin.ModelAdmin):
    list_display = ("__str__", "requester", "status", "urgency", "submitted_at")
    list_filter = ("status", "urgency")
    readonly_fields = ("status", "row_version")


admin.site.register([Reservation, ReservationEvent, AssistantDraft])
