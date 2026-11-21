from django.contrib import admin

from .models import MatchRecommendation, MatchResultSet

admin.site.register([MatchResultSet, MatchRecommendation])
