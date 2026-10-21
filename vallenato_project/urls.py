"""
Main URL Configuration for the Vallenato Legend Festival Project.
"""
from django.contrib import admin
from django.urls import path, include

admin.site.site_header = "Festival Vallenato 2027 — Administrative Portal"
admin.site.site_title = "Vallenato Voting Admin"
admin.site.index_title = "Electoral & Festival Management"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),
    path("", include("apps.voting.urls", namespace="voting")),
]
