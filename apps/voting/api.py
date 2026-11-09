from django.http import JsonResponse
from django.views.decorators.http import require_GET

from apps.voting.models import Category, Option, Voting
from django.db.models import Prefetch


@require_GET
def categories_api(request):
    """GET /api/categorias/ -> categorías activas con sus votaciones y opciones (MySQL)."""
    categories = (
        Category.objects.filter(is_active=True, edition__is_active=True)
        .select_related("edition")
        .prefetch_related(
            Prefetch("votings", queryset=Voting.objects.order_by("start_datetime")),
            Prefetch(
                "votings__options",
                queryset=Option.objects.filter(is_active=True).order_by("order_num", "candidate_name"),
            ),
        )
        .order_by("-edition__year", "name")
    )

    data = []
    for category in categories:
        votings = list(category.votings.all())
        data.append({
            "id": category.id,
            "nombre": category.name,
            "codigo": category.code,
            "descripcion": category.description,
            "activa": category.is_active,
            "edicion": {
                "id": category.edition_id,
                "anio": category.edition.year,
                "nombre": category.edition.name,
            },
            "votaciones": [
                {
                    "id": voting.id,
                    "titulo": voting.title,
                    "estado": voting.status,
                    "abierta": voting.is_currently_open,
                }
                for voting in votings
            ],
            "opciones": [
                {
                    "id": option.id,
                    "votacion_id": voting.id,
                    "nombre": option.candidate_name,
                    "nombre_artistico": option.stage_name,
                    "municipio": option.hometown,
                    "orden": option.order_num,
                }
                for voting in votings
                for option in voting.options.all()
            ],
        })

    return JsonResponse(
        {"total": len(data), "categorias": data},
        json_dumps_params={"ensure_ascii": False},
    )
