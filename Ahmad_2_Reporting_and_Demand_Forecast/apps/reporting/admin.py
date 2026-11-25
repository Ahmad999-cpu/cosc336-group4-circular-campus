from django.contrib import admin

from .models import AISummary, Report

admin.site.register([Report, AISummary])
