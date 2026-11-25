from django.contrib import admin

from .models import AIInferenceRecord, ModelVersion, PolicyDocument


@admin.register(ModelVersion)
class ModelVersionAdmin(admin.ModelAdmin):
    list_display = ("capability", "version", "provider", "model_name", "status", "low_confidence_threshold")


@admin.register(AIInferenceRecord)
class AIInferenceRecordAdmin(admin.ModelAdmin):
    list_display = ("capability", "outcome", "confidence", "latency_ms", "user_decision", "created_at")
    list_filter = ("capability", "outcome")


admin.site.register(PolicyDocument)
