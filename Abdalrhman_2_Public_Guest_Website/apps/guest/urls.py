from django.urls import path

from . import views

app_name = "guest"
urlpatterns = [
    path("pricing/", views.pricing_page, name="pricing"),
    path("institution-blueprint/", views.blueprint, name="blueprint"),
    path("how-it-works/", views.how_it_works, name="how"),
    path("contact/", views.contact, name="contact"),
    path("robots.txt", views.robots_txt, name="robots"),
    path("favicon.ico", views.favicon_ico, name="favicon"),
    path("sitemap.xml", views.sitemap_xml, name="sitemap"),
]
