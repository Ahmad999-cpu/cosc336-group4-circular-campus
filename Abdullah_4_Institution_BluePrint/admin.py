from django.contrib import admin

from .models import ApprovalRule, BlueprintDraft

admin.site.register([ApprovalRule, BlueprintDraft])
