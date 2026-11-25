from django.contrib import admin

from .models import EmissionFactor, SustainabilityImpact, SustainabilityRecommendation

admin.site.register([EmissionFactor, SustainabilityImpact, SustainabilityRecommendation])
