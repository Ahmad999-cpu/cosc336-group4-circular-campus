from django.contrib import admin

from .models import EndOfLifeProposal, InspectionRequest, LifeCycleEvent, MaintenanceRecord, MaintenanceUpdate, RepairAction


@admin.register(LifeCycleEvent)
class LifeCycleEventAdmin(admin.ModelAdmin):
    list_display = ("asset", "event_type", "previous_state", "new_state", "recorded_by", "recorded_at")
    list_filter = ("event_type",)

    def has_change_permission(self, request, obj=None):
        return False  # append-only

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register([EndOfLifeProposal, MaintenanceRecord, InspectionRequest, RepairAction, MaintenanceUpdate])
