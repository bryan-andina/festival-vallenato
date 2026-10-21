"""
Django Admin customization for the Vallenato Legend Festival voting domain.
Implements inlines, filters, and structured fields for intuitive administration.
"""
from django.contrib import admin
from apps.voting.models import Edition, Category, Voting, Option, Vote


class CategoryInline(admin.TabularInline):
    """Allows managing categories directly within the Edition admin interface."""
    model = Category
    extra = 1
    fields = ("name", "code", "is_active")
    prepopulated_fields = {"code": ("name",)}


class OptionInline(admin.TabularInline):
    """Allows managing ballot candidate options directly within the Voting interface."""
    model = Option
    extra = 2
    fields = ("candidate_name", "stage_name", "hometown", "order_num", "is_active")


@admin.register(Edition)
class EditionAdmin(admin.ModelAdmin):
    list_display = ("name", "year", "start_date", "end_date", "is_active", "created_at")
    list_filter = ("is_active", "year")
    search_fields = ("name", "slogan", "description")
    inlines = [CategoryInline]
    ordering = ("-year",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "edition", "code", "is_active", "created_at")
    list_filter = ("edition", "is_active")
    search_fields = ("name", "code", "description")
    prepopulated_fields = {"code": ("name",)}


@admin.register(Voting)
class VotingAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "status",
        "start_datetime",
        "end_datetime",
        "max_votes_per_user",
        "is_currently_open"
    )
    list_filter = ("status", "category__edition", "category")
    search_fields = ("title", "description")
    inlines = [OptionInline]
    date_hierarchy = "start_datetime"


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = (
        "candidate_name",
        "stage_name",
        "voting",
        "hometown",
        "order_num",
        "is_active"
    )
    list_filter = ("voting__category__edition", "voting__category", "is_active")
    search_fields = ("candidate_name", "stage_name", "hometown", "biography")
    ordering = ("voting", "order_num", "candidate_name")


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("user", "voting", "selected_option", "ip_address", "created_at")
    list_filter = ("voting__category__edition", "voting", "created_at")
    search_fields = ("user__username", "user__email", "voting__title", "selected_option__candidate_name")
    readonly_fields = ("user", "voting", "selected_option", "ip_address", "created_at", "updated_at")

    def has_add_permission(self, request):
        # Ballots should only be created via voter interface, not manually added
        return False
