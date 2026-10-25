"""
Comando para cargar datos de prueba (seed) del Festival de la Leyenda Vallenata.

Uso:
    python manage.py seed_festival_data
    python manage.py seed_festival_data --with-sample-votes
    python manage.py seed_festival_data --refresh-windows
    python manage.py seed_festival_data --admin-password "..." --voter-password "..."

Es idempotente: se puede ejecutar varias veces sin duplicar registros.

Contraseñas: se toman de --admin-password / --voter-password, o de las variables
de entorno SEED_ADMIN_PASSWORD / SEED_VOTER_PASSWORD. Si no existen, se genera
una aleatoria y se muestra UNA sola vez en consola al crear el usuario.

Los concursantes y sus biografías son FICTICIOS: sirven para probar el sistema
mientras la FFLV no entregue el listado oficial de inscritos (ver pregunta 6
y la pendiente "Sincronización con base de datos de inscritos" de la Entrega 1).

Estados de prueba incluidos (RF-02):
    - Votaciones ABIERTAS    -> Profesional, Canción Inédita, Piqueria, Femenino
    - Votación PRÓXIMA       -> Acordeón Juvenil (borrador con fecha futura)
    - Votación CERRADA       -> Danza de Piloneras 2027 y Rey Profesional 2026
    - Borrador con 1 opción  -> Acordeón Infantil (para probar la regla RN-05)
    - Categorías sin votación-> Aficionado y Piqueria Infantil (estado vacío)
"""
import os
from datetime import date, datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import get_random_string

from apps.voting.models import Category, Edition, Option, Vote, Voting

User = get_user_model()
Status = Voting.Status

# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------
EDITIONS = [
    {
        "year": 2027,
        "name": "60° Festival de la Leyenda Vallenata 2027",
        "slogan": "60 Años de Leyenda, Tradición y Folclor en Valledupar",
        "description": (
            "Edición conmemorativa de las seis décadas del certamen folclórico más insigne "
            "de Colombia. Valledupar rinde tributo a las dinastías de juglares y compositores "
            "que consagraron los cuatro aires autóctonos."
        ),
        "start_date": date(2027, 4, 26),
        "end_date": date(2027, 5, 2),
        "is_active": True,
    },
    {
        "year": 2026,
        "name": "59° Festival de la Leyenda Vallenata 2026",
        "slogan": "La Fuerza de las Nuevas Generaciones",
        "description": (
            "Certamen folclórico que impulsó el relevo generacional y la salvaguarda del "
            "patrimonio musical."
        ),
        "start_date": date(2026, 4, 27),
        "end_date": date(2026, 5, 1),
        # Edición pasada: inactiva, para probar el filtro de ediciones activas.
        "is_active": False,
    },
]

CATEGORIES_2027 = [
    ("Acordeón Profesional", "acordeon-profesional",
     "Máxima distinción musical que corona al Rey Vallenato en los cuatro ritmos canónicos: "
     "paseo, merengue, son y puya."),
    ("Acordeón Aficionado", "acordeon-aficionado",
     "Escalafón formativo para ejecutantes aficionados de los cuatro aires tradicionales."),
    ("Acordeón Juvenil", "acordeon-juvenil",
     "Competencia para jóvenes acordeoneros que aseguran el relevo generacional del folclor."),
    ("Acordeón Infantil", "acordeon-infantil",
     "Competencia para niños y niñas acordeoneros, semillero del vallenato tradicional."),
    ("Acordeón Femenino Mayor", "acordeon-femenino",
     "Competencia cumbre para las más virtuosas acordeoneras de Colombia y el exterior."),
    ("Canción Vallenata Inédita", "cancion-inedita",
     "Competencia poética y lírica de composiciones inéditas dedicadas a la identidad costeña."),
    ("Piqueria Mayor", "piqueria-mayor",
     "Duelo verbal en décimas y cuartetas cantadas de repentismo, rima estricta e ingenio."),
    ("Piqueria Infantil", "piqueria-infantil",
     "Duelo de repentismo e improvisación poética cantada para las nuevas voces del festival."),
    ("Danza de Piloneras", "danza-piloneras",
     "Calificación coreográfica y de vestuario de las agrupaciones de baile tradicional."),
]

# Cada opción: (candidate_name, stage_name, hometown, biography). order_num = posición + 1.
VOTINGS_2027 = [
    {
        "category": "acordeon-profesional",
        "title": "Elección Popular Rey Vallenato Profesional 2027",
        "description": (
            "Vota por el acordeonero profesional que ha demostrado la mayor destreza, "
            "cadencia y apego a los aires tradicionales en la tarima Colacho Mendoza."
        ),
        "status": Status.OPEN, "start_days": -1, "end_days": 10,
        "options": [
            ("Andrés Felipe Maestre Orozco", "El Zorzal de la Sierra", "Valledupar, Cesar",
             "Acordeonero de escuela tradicional, destacado por la limpieza de su digitación "
             "en el aire de paseo y su fraseo cadencioso."),
            ("Luis Eduardo Pimienta Cuello", "El Gavilán del Ariguaní", "Ariguaní, Magdalena",
             "Intérprete de la tradición magdalenense, reconocido por su dominio del son y la "
             "puya tras más de quince años en tarimas regionales."),
            ("Camilo Andrés Zuleta Barros", "El Juglar de Villanueva", "Villanueva, La Guajira",
             "Joven maestro de los cuatro aires, formado en festivales del sur de La Guajira; "
             "destaca por su repertorio de merengues clásicos."),
        ],
    },
    {
        "category": "cancion-inedita",
        "title": "Favorita del Público: Canción Vallenata Inédita 2027",
        "description": (
            "Elige la obra poética que mejor preserve el lirismo, metáfora y pureza del "
            "vallenato tradicional."
        ),
        "status": Status.OPEN, "start_days": -1, "end_days": 8,
        "options": [
            ("La Nostalgia del Juglar (Paseo)", "Autor: Hernando Zabaleta", "El Molino, La Guajira",
             "Paseo nostálgico que evoca las serenatas de madrugada bajo los palos de mango "
             "en el Valledupar de antaño."),
            ("Canto a la Sierra Nevada (Merengue)", "Autora: Carolina Maestre", "Valledupar, Cesar",
             "Merengue de rítmica viva y versos dedicados a la protección de las fuentes "
             "hídricas del río Guatapurí."),
            ("Puya de los Cañaguates (Puya)", "Autor: Rafael Mejía Daza", "Villanueva, La Guajira",
             "Puya de ritmo vertiginoso que celebra la floración de los cañaguates en los "
             "patios del Valle del Cacique Upar."),
        ],
    },
    {
        "category": "piqueria-mayor",
        "title": "Favorito del Público: Piqueria Mayor 2027",
        "description": (
            "Apoya al versador que mejor combine ingenio, rapidez y rima en el duelo de "
            "repentismo."
        ),
        "status": Status.OPEN, "start_days": -1, "end_days": 9,
        "options": [
            ("Ramiro Sarmiento Ovalle", "El Verso Bravo", "San Diego, Cesar",
             "Versador de décima improvisada, reconocido por su rapidez para responder en "
             "contrapunteo y su dominio de la rima consonante."),
            ("Dilia Rosa Pacheco Arzuaga", "La Décima Viva", "La Paz, Cesar",
             "Cantora y versadora de la tradición oral del Cesar, con un estilo pausado y "
             "cargado de metáforas del campo."),
            ("Eder Manjarrez Solano", "El Pregonero de la Décima", "Bosconia, Cesar",
             "Repentista de voz potente que mezcla humor y crítica social en cada cuarteta."),
        ],
    },
    {
        "category": "acordeon-femenino",
        "title": "Favorita del Público: Acordeón Femenino Mayor 2027",
        "description": "Elige a la acordeonera que más te conmovió con su técnica y sentimiento.",
        "status": Status.OPEN, "start_days": -1, "end_days": 7,
        "options": [
            ("Mariana Torres Escalona", "La Perla del Cesar", "Valledupar, Cesar",
             "Acordeonera de técnica depurada, con un repertorio que honra a los juglares "
             "clásicos del vallenato."),
            ("Valentina Cuello Mendoza", "La Sabanera del Fuelle", "Sincelejo, Sucre",
             "Intérprete sabanera de ejecución vigorosa, destacada en el aire de son."),
        ],
    },
    {
        # PRÓXIMA: borrador con fecha de inicio futura.
        "category": "acordeon-juvenil",
        "title": "Favorito del Público: Acordeón Juvenil 2027",
        "description": "Próximamente: elige a la nueva promesa del acordeón vallenato.",
        "status": Status.DRAFT, "start_days": 5, "end_days": 15,
        "options": [
            ("Santiago Daza Peñaranda", "El Aprendiz de la Sierra", "Pueblo Bello, Cesar",
             "Joven acordeonero formado en escuelas folclóricas de la Sierra Nevada."),
            ("Mateo Ríos Gutiérrez", "El Joven del Fuelle", "Montería, Córdoba",
             "Promesa del acordeón sinuano, con dominio de los cuatro aires tradicionales."),
        ],
    },
    {
        # Borrador con UNA sola opción: al intentar abrirla el admin debe rechazarla (RN-05).
        "category": "acordeon-infantil",
        "title": "Favorito del Público: Acordeón Infantil 2027",
        "description": "Próximamente: apoya al pequeño juglar de tu preferencia.",
        "status": Status.DRAFT, "start_days": 5, "end_days": 15,
        "options": [
            ("Samuel David Ortiz Pardo", "El Pequeño Juglar", "Agustín Codazzi, Cesar",
             "Niño acordeonero que aprendió el oficio en su familia y ya participa en "
             "festivales infantiles de la región."),
        ],
    },
    {
        # CERRADA.
        "category": "danza-piloneras",
        "title": "Favorita del Público: Danza de Piloneras 2027",
        "description": "Votación finalizada: comparsa favorita del público en el desfile de piloneras.",
        "status": Status.CLOSED, "start_days": -10, "end_days": -2,
        "options": [
            ("Comparsa Brisas del Guatapurí", "Dirección: Marta Lucía Orozco", "Valledupar, Cesar",
             "Agrupación tradicional reconocida por la fidelidad de su vestuario de pilonera."),
            ("Comparsa Colores de la Sierra", "Dirección: Jairo Fuentes", "Pueblo Bello, Cesar",
             "Comparsa que destaca por la coreografía colectiva y el uso de colores vivos."),
            ("Comparsa Herederas del Pilón", "Dirección: Esperanza Mejía", "Agustín Codazzi, Cesar",
             "Grupo juvenil que mantiene viva la danza del pilón en su comunidad."),
        ],
    },
]

CATEGORY_2026 = (
    "Acordeón Profesional", "acordeon-profesional",
    "Máxima distinción musical que corona al Rey Vallenato.",
)
VOTING_2026 = {
    "title": "Elección Popular Rey Vallenato Profesional 2026",
    "description": "Votación histórica de la edición 2026 (cerrada).",
    "status": Status.CLOSED,
    "start": (2026, 4, 27, 8, 0),
    "end": (2026, 5, 1, 22, 0),
    "options": [
        ("Ever José Baquero Ariza", "El Cóndor del Cesar", "Valledupar, Cesar",
         "Acordeonero consagrado en la edición 2026 del festival."),
        ("Nelson Darío Fuentes Mejía", "El Tigre del Fuelle", "Fundación, Magdalena",
         "Subcampeón de la edición 2026, reconocido por su interpretación de la puya."),
    ],
}


class Command(BaseCommand):
    help = "Carga datos de prueba del Festival de la Leyenda Vallenata 2027 (idempotente)."

    def add_arguments(self, parser):
        parser.add_argument("--admin-password", help="Contraseña del usuario 'admin' (si se crea).")
        parser.add_argument("--voter-password", help="Contraseña del usuario 'voter_bryan' (si se crea).")
        parser.add_argument(
            "--with-sample-votes",
            action="store_true",
            help="Crea 5 votantes de prueba y votos de ejemplo en votaciones abiertas/cerradas.",
        )
        parser.add_argument(
            "--refresh-windows",
            action="store_true",
            help="Reinicia las fechas de las votaciones de 2027 relativas a hoy.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE(">>> Cargando datos del Festival Vallenato..."))

        self._seed_users(options)
        editions = self._seed_editions()
        votings = self._seed_votings_2027(editions[2027], options["refresh_windows"])
        votings.append(self._seed_voting_2026(editions[2026]))

        if options["with_sample_votes"]:
            self._seed_votes(votings)

        self.stdout.write(self.style.SUCCESS(">>> Carga finalizada correctamente."))

    # -- usuarios ---------------------------------------------------------------
    def _password(self, cli_value, env_name):
        value = cli_value or os.environ.get(env_name)
        if value:
            return value, False
        return get_random_string(14), True

    def _ensure_user(self, username, defaults, password_info):
        user, created = User.objects.get_or_create(username=username, defaults=defaults)
        if not created:
            self.stdout.write(self.style.WARNING(f"[!] El usuario '{username}' ya existe."))
            return user
        password, generated = password_info
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Usuario creado: {username}"))
        if generated:
            self.stdout.write(
                self.style.WARNING(
                    f"    Contraseña generada para '{username}': {password}  "
                    "(guárdala ahora; no se vuelve a mostrar)"
                )
            )
        return user

    def _seed_users(self, options):
        self._ensure_user(
            "admin",
            {
                "email": "admin@festivalvallenato.co",
                "first_name": "Administrador",
                "last_name": "General",
                "is_staff": True,
                "is_superuser": True,
            },
            self._password(options["admin_password"], "SEED_ADMIN_PASSWORD"),
        )
        self._ensure_user(
            "voter_bryan",
            {
                "email": "bryan.voter@areandina.edu.co",
                "first_name": "Bryan",
                "last_name": "Rincón",
            },
            self._password(options["voter_password"], "SEED_VOTER_PASSWORD"),
        )

    # -- ediciones y categorías ---------------------------------------------------
    def _seed_editions(self):
        editions = {}
        for data in EDITIONS:
            fields = {k: v for k, v in data.items() if k != "year"}
            edition, created = Edition.objects.get_or_create(year=data["year"], defaults=fields)
            editions[data["year"]] = edition
            self.stdout.write(
                self.style.SUCCESS(f"[{'+' if created else '='}] Edición: {edition.name}")
            )
        return editions

    def _ensure_category(self, edition, name, code, description):
        category, created = Category.objects.get_or_create(
            edition=edition,
            name=name,
            defaults={"code": code, "description": description, "is_active": True},
        )
        self.stdout.write(
            self.style.SUCCESS(f"  [{'+' if created else '='}] Categoría ({edition.year}): {name}")
        )
        return category

    # -- votaciones --------------------------------------------------------------
    def _ensure_options(self, voting, options):
        for position, (candidate, stage, hometown, biography) in enumerate(options, start=1):
            Option.objects.get_or_create(
                voting=voting,
                candidate_name=candidate,
                defaults={
                    "stage_name": stage,
                    "hometown": hometown,
                    "biography": biography,
                    "order_num": position,
                    "is_active": True,
                },
            )

    def _seed_votings_2027(self, edition, refresh_windows):
        categories = {
            code: self._ensure_category(edition, name, code, description)
            for name, code, description in CATEGORIES_2027
        }
        now = timezone.now()
        votings = []
        for data in VOTINGS_2027:
            start = now + timedelta(days=data["start_days"])
            end = now + timedelta(days=data["end_days"])
            voting, created = Voting.objects.get_or_create(
                category=categories[data["category"]],
                title=data["title"],
                defaults={
                    "description": data["description"],
                    "status": data["status"],
                    "start_datetime": start,
                    "end_datetime": end,
                    "max_votes_per_user": 1,
                },
            )
            if not created and refresh_windows:
                voting.start_datetime = start
                voting.end_datetime = end
                voting.save(update_fields=["start_datetime", "end_datetime", "updated_at"])
            self._ensure_options(voting, data["options"])
            votings.append(voting)
            self.stdout.write(
                self.style.SUCCESS(
                    f"    [{'+' if created else '='}] Votación [{voting.get_status_display()}]: "
                    f"{voting.title} ({len(data['options'])} opciones)"
                )
            )
        return votings

    def _seed_voting_2026(self, edition):
        name, code, description = CATEGORY_2026
        category = self._ensure_category(edition, name, code, description)
        aware = lambda parts: timezone.make_aware(datetime(*parts))  # noqa: E731
        voting, created = Voting.objects.get_or_create(
            category=category,
            title=VOTING_2026["title"],
            defaults={
                "description": VOTING_2026["description"],
                "status": VOTING_2026["status"],
                "start_datetime": aware(VOTING_2026["start"]),
                "end_datetime": aware(VOTING_2026["end"]),
                "max_votes_per_user": 1,
            },
        )
        self._ensure_options(voting, VOTING_2026["options"])
        self.stdout.write(
            self.style.SUCCESS(
                f"    [{'+' if created else '='}] Votación [{voting.get_status_display()}]: {voting.title}"
            )
        )
        return voting

    # -- votos de ejemplo (opcional) -----------------------------------------------
    def _seed_votes(self, votings):
        voters = []
        for i in range(1, 6):
            user, created = User.objects.get_or_create(
                username=f"voter_{i:02d}",
                defaults={
                    "email": f"voter{i:02d}@example.com",
                    "first_name": "Votante",
                    "last_name": f"Prueba {i}",
                },
            )
            if created:
                user.set_unusable_password()  # solo sirven como datos; no inician sesión
                user.save()
            voters.append(user)

        created_total = 0
        for j, voting in enumerate(votings):
            if voting.status not in (Status.OPEN, Status.CLOSED):
                continue
            options = list(voting.options.filter(is_active=True).order_by("order_num"))
            if not options:
                continue
            for i, user in enumerate(voters):
                _, created = Vote.objects.get_or_create(
                    user=user,
                    voting=voting,
                    defaults={
                        "selected_option": options[(i + j) % len(options)],
                        "ip_address": f"203.0.113.{10 + i}",  # rango reservado para documentación
                    },
                )
                created_total += int(created)
        self.stdout.write(self.style.SUCCESS(f"[+] Votos de ejemplo creados: {created_total}"))
