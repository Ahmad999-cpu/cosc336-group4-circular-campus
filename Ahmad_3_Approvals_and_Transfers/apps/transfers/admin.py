from django.contrib import admin

from .models import ApprovalDecision, DeliveryEvent, Transfer


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ("asset", "quantity", "source_department", "destination_department", "status")
    list_filter = ("status",)
    readonly_fields = ("status",)


admin.site.register([ApprovalDecision, DeliveryEvent])
