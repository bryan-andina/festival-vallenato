from django.contrib import admin, messages
from django.db.models import Count, Q
from django.utils.html import format_html, format_html_join

from apps.voting.models import Category, Edition, Option, Vote, Voting

admin.site.site_header = "Festival de la Leyenda Vallenata · Administración"
admin.site.site_title = "Votaciones Vallenato"
admin.site.index_title = "Panel de administración de votaciones"


MIN_ACTIVE_OPTIONS = 2

AUDIT_FIELDSET = (
    "Auditoría",
    {"classes": ("collapse",), "fields": ("created_at", "updated_at")},
)


class CategoryInline(admin.TabularInline):
    model = Category
    extra = 1
    fields = ("name", "code", "is_active")
    prepopulated_fields = {"code": ("name",)}
    show_change_link = True


class VotingInline(admin.TabularInline):
    model = Voting
    extra = 0
    fields = ("title", "status", "start_datetime", "end_datetime", "max_votes_per_user")
    readonly_fields = ("status",)
    show_change_link = True


class OptionInline(admin.TabularInline):
    model = Option
    extra = 2
    fields = ("candidate_name", "stage_name", "hometown", "photo_url", "order_num", "is_active")
    ordering = ("order_num", "candidate_name")


@admin.register(Edition)
class EditionAdmin(admin.ModelAdmin):
    list_display = ("name", "year", "start_date", "end_date", "is_active", "categories_total", "created_at")
    list_editable = ("is_active",)
    list_filter = ("is_active", "year")
    search_fields = ("name", "slogan", "description")
    ordering = ("-year",)
    inlines = [CategoryInline]
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Identificación", {"fields": ("name", "year", "slogan")}),
        ("Calendario", {"fields": ("start_date", "end_date")}),
        ("Contenido", {"fields": ("description",)}),
        ("Estado", {"fields": ("is_active",)}),
        AUDIT_FIELDSET,
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _categories=Count("categories", distinct=True)
        )

    @admin.display(description="Categorías", ordering="_categories")
    def categories_total(self, obj):
        return obj._categories


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "edition", "code", "is_active", "votings_total", "created_at")
    list_editable = ("is_active",)
    list_filter = ("edition", "is_active")
    search_fields = ("name", "code", "description", "edition__name")
    list_select_related = ("edition",)
    prepopulated_fields = {"code": ("name",)}
    inlines = [VotingInline]
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Identificación", {"fields": ("edition", "name", "code")}),
        ("Contenido", {"fields": ("description",)}),
        ("Estado", {"fields": ("is_active",)}),
        AUDIT_FIELDSET,
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _votings=Count("votings", distinct=True)
        )

    @admin.display(description="Votaciones", ordering="_votings")
    def votings_total(self, obj):
        return obj._votings


@admin.register(Voting)
class VotingAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "status",
        "start_datetime",
        "end_datetime",
        "active_options",
        "votes_total",
        "is_open_now",
        "max_votes_per_user",
    )
    list_filter = ("status", "category__edition", "category")
    search_fields = ("title", "description", "category__name")
    list_select_related = ("category", "category__edition")
    date_hierarchy = "start_datetime"
    inlines = [OptionInline]
    actions = ["open_votings", "suspend_votings", "close_votings"]
    readonly_fields = ("is_open_now", "results_summary", "created_at", "updated_at")
    fieldsets = (
        ("Datos de la votación", {"fields": ("category", "title", "description")}),
        (
            "Ventana de votación",
            {"fields": ("status", "start_datetime", "end_datetime", "max_votes_per_user", "is_open_now")},
        ),
        ("Resultados parciales (solo administración)", {"fields": ("results_summary",)}),
        AUDIT_FIELDSET,
    )


    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _active_options=Count("options", filter=Q(options__is_active=True), distinct=True),
            _votes=Count("cast_votes", distinct=True),
        )

    @admin.display(description="Opciones activas", ordering="_active_options")
    def active_options(self, obj):
        return obj._active_options

    @admin.display(description="Votos", ordering="_votes")
    def votes_total(self, obj):
        return obj._votes

    @admin.display(boolean=True, description="Abierta ahora")
    def is_open_now(self, obj):
        return bool(obj.pk) and obj.is_currently_open

    @admin.display(description="Votos por opción")
    def results_summary(self, obj):
        if not obj.pk:
            return "—"
        rows = list(
            obj.options.annotate(total=Count("received_votes")).order_by("-total", "order_num")
        )
        if not rows:
            return "Sin opciones registradas."
        grand_total = sum(row.total for row in rows)
        items = format_html_join(
            "",
            "<li>{} — <strong>{}</strong> voto(s) ({}%)</li>",
            (
                (
                    row.candidate_name,
                    row.total,
                    round(100 * row.total / grand_total, 1) if grand_total else 0,
                )
                for row in rows
            ),
        )
        return format_html(
            "<ul style='margin:0;padding-left:1.2em'>{}</ul>"
            "<p style='margin:.4em 0 0'>Total de votos: {}</p>",
            items,
            grand_total,
        )


    @staticmethod
    def _activation_problem(voting):
        if not voting.category.edition.is_active:
            return "la edición del festival no está activa (RN-04)."
        active = voting.options.filter(is_active=True).count()
        if active < MIN_ACTIVE_OPTIONS:
            return (
                f"tiene {active} opción(es) activa(s) y necesita al menos "
                f"{MIN_ACTIVE_OPTIONS} (RN-05)."
            )
        return None

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        voting = form.instance
        if voting.status == Voting.Status.OPEN:
            problem = self._activation_problem(voting)
            if problem:
                voting.status = Voting.Status.DRAFT
                voting.save(update_fields=["status", "updated_at"])
                self.message_user(
                    request,
                    f"«{voting.title}» se guardó como Borrador porque {problem}",
                    messages.WARNING,
                )


    @admin.action(description="Abrir votaciones seleccionadas")
    def open_votings(self, request, queryset):
        opened = 0
        for voting in queryset.select_related("category__edition"):
            if voting.status != Voting.Status.DRAFT:
                self.message_user(
                    request,
                    f"«{voting.title}» está en estado «{voting.get_status_display()}»; "
                    "solo se pueden abrir votaciones en borrador.",
                    messages.WARNING,
                )
                continue
            problem = self._activation_problem(voting)
            if problem:
                self.message_user(
                    request, f"«{voting.title}» no se abrió: {problem}", messages.ERROR
                )
                continue
            voting.status = Voting.Status.OPEN
            voting.save(update_fields=["status", "updated_at"])
            opened += 1
        if opened:
            self.message_user(request, f"{opened} votación(es) abierta(s).", messages.SUCCESS)

    @admin.action(description="Suspender votaciones abiertas (volver a borrador)")
    def suspend_votings(self, request, queryset):
        suspended = 0
        for voting in queryset:
            if voting.status != Voting.Status.OPEN:
                self.message_user(
                    request,
                    f"«{voting.title}» no está abierta; no se puede suspender.",
                    messages.WARNING,
                )
                continue
            voting.status = Voting.Status.DRAFT
            voting.save(update_fields=["status", "updated_at"])
            suspended += 1
        if suspended:
            self.message_user(request, f"{suspended} votación(es) suspendida(s).", messages.SUCCESS)

    @admin.action(description="Cerrar votaciones abiertas")
    def close_votings(self, request, queryset):
        closed = 0
        for voting in queryset:
            if voting.status != Voting.Status.OPEN:
                self.message_user(
                    request,
                    f"«{voting.title}» no está abierta; solo se cierran votaciones abiertas.",
                    messages.WARNING,
                )
                continue
            voting.status = Voting.Status.CLOSED
            voting.save(update_fields=["status", "updated_at"])
            closed += 1
        if closed:
            self.message_user(request, f"{closed} votación(es) cerrada(s).", messages.SUCCESS)


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = (
        "candidate_name",
        "stage_name",
        "voting",
        "hometown",
        "order_num",
        "is_active",
        "votes_total",
    )
    list_editable = ("order_num", "is_active")
    list_filter = ("voting__category__edition", "voting__category", "is_active")
    search_fields = ("candidate_name", "stage_name", "hometown", "biography", "voting__title")
    list_select_related = ("voting", "voting__category")
    ordering = ("voting", "order_num", "candidate_name")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Candidato", {"fields": ("voting", "candidate_name", "stage_name", "hometown", "photo_url")}),
        ("Biografía", {"fields": ("biography",)}),
        ("Papeleta", {"fields": ("order_num", "is_active")}),
        AUDIT_FIELDSET,
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_votes=Count("received_votes", distinct=True))

    @admin.display(description="Votos recibidos", ordering="_votes")
    def votes_total(self, obj):
        return obj._votes


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("user", "voting", "selected_option", "ip_address", "created_at")
    list_filter = ("voting__category__edition", "voting", "created_at")
    search_fields = (
        "user__username",
        "user__email",
        "voting__title",
        "selected_option__candidate_name",
    )
    list_select_related = ("user", "voting", "selected_option__voting__category")
    date_hierarchy = "created_at"
    readonly_fields = ("user", "voting", "selected_option", "ip_address", "created_at", "updated_at")


    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
