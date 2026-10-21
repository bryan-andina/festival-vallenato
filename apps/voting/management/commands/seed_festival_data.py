"""
Management command to seed initial domain data for the Festival Vallenato 2027.
Adheres to Single Responsibility Principle and idempotent design.
"""
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.voting.models import Edition, Category, Voting, Option

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds the database with Festival Vallenato 2027 editions, categories, votings, and sample contestants."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE(">>> Starting Festival Vallenato 2027 Seed Process..."))

        # 1. Superuser Creation
        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@festivalvallenato.co",
                "first_name": "Administrador",
                "last_name": "General",
                "is_staff": True,
                "is_superuser": True,
            }
        )
        if created:
            admin_user.set_password("admin2027")
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("[+] Superuser created: admin / admin2027"))
        else:
            self.stdout.write(self.style.WARNING("[!] Superuser 'admin' already exists."))

        # 2. Sample Public Voter
        voter, created = User.objects.get_or_create(
            username="voter_bryan",
            defaults={
                "email": "bryan.voter@areandina.edu.co",
                "first_name": "Bryan",
                "last_name": "Rincón",
            }
        )
        if created:
            voter.set_password("vallenato2027")
            voter.save()
            self.stdout.write(self.style.SUCCESS("[+] Test voter user created: voter_bryan / vallenato2027"))

        # 3. Festival Editions
        edition_2027, _ = Edition.objects.get_or_create(
            year=2027,
            defaults={
                "name": "60° Festival de la Leyenda Vallenata 2027",
                "slogan": "60 Años de Leyenda, Tradición y Folclor en Valledupar",
                "description": "Edición conmemorativa de las seis décadas del certamen folclórico más insigne de Colombia. Valledupar rinde tributo a las dinastías de juglares y compositores que consagraron los cuatro aires autóctonos.",
                "start_date": date(2027, 4, 26),
                "end_date": date(2027, 5, 2),
                "is_active": True,
            }
        )
        self.stdout.write(self.style.SUCCESS(f"[+] Edition registered: {edition_2027}"))

        edition_2026, _ = Edition.objects.get_or_create(
            year=2026,
            defaults={
                "name": "59° Festival de la Leyenda Vallenata 2026",
                "slogan": "La Fuerza de las Nuevas Generaciones",
                "description": "Certamen folclórico que impulsó el relevo generacional y la salvaguarda del patrimonio musical.",
                "start_date": date(2026, 4, 27),
                "end_date": date(2026, 5, 1),
                "is_active": True,
            }
        )

        # 4. Categories for 2027
        categories_data = [
            {
                "name": "Acordeón Profesional",
                "code": "acordeon-profesional",
                "description": "Máxima distinción musical que corona al Rey Vallenato en los cuatro ritmos canónicos: paseo, merengue, son y puya.",
            },
            {
                "name": "Canción Vallenata Inédita",
                "code": "cancion-inedita",
                "description": "Competencia poética y lírica de composiciones inéditas dedicadas a la identidad costeña.",
            },
            {
                "name": "Piqueria Mayor",
                "code": "piqueria-mayor",
                "description": "Duelo verbal en décimas y cuartetas cantadas de repentismo, rima estricta e ingenio.",
            },
            {
                "name": "Acordeón Femenino Mayor",
                "code": "acordeon-femenino",
                "description": "Competencia cumbre para las más virtuosas acordeoneras de Colombia y el exterior.",
            },
        ]

        created_categories = {}
        for cat_info in categories_data:
            cat_obj, _ = Category.objects.get_or_create(
                edition=edition_2027,
                name=cat_info["name"],
                defaults={
                    "code": cat_info["code"],
                    "description": cat_info["description"],
                    "is_active": True,
                }
            )
            created_categories[cat_info["code"]] = cat_obj
            self.stdout.write(self.style.SUCCESS(f"  [+] Category: {cat_obj.name}"))

        # 5. Votings
        now = timezone.now()
        voting_profesional, _ = Voting.objects.get_or_create(
            category=created_categories["acordeon-profesional"],
            title="Elección Popular Rey Vallenato Profesional 2027",
            defaults={
                "description": "Vota por el acordeonero profesional que ha demostrado la mayor destreza, cadencia y apego a los aires tradicionales en la tarima Colacho Mendoza.",
                "status": Voting.Status.OPEN,
                "start_datetime": now - timedelta(days=1),
                "end_datetime": now + timedelta(days=10),
                "max_votes_per_user": 1,
            }
        )

        voting_inedita, _ = Voting.objects.get_or_create(
            category=created_categories["cancion-inedita"],
            title="Favorita del Público: Canción Vallenata Inédita 2027",
            defaults={
                "description": "Elige la obra poética que mejor preserve el lirismo, metáfora y pureza del vallenato tradicional.",
                "status": Voting.Status.OPEN,
                "start_datetime": now - timedelta(days=1),
                "end_datetime": now + timedelta(days=8),
                "max_votes_per_user": 1,
            }
        )

        # 6. Options / Candidates for Acordeón Profesional
        options_profesional = [
            {
                "candidate_name": "Javier Matta Correa",
                "stage_name": "El Pollo de Santa Marta",
                "biography": "Virtuoso acordeonero de la escuela tradicional samaria, rey vallenato 2023 con técnica depurada en el aire de puya.",
                "hometown": "Santa Marta, Magdalena",
                "order_num": 1,
            },
            {
                "candidate_name": "Juan David Atencia",
                "stage_name": "El Ángel del Acordeón",
                "biography": "Destacado ejecutante sabanero, heredero de la cuna folclórica con interpretaciones impecables en son y merengue.",
                "hometown": "Sincelejo, Sucre",
                "order_num": 2,
            },
            {
                "candidate_name": "Camilo Molina Luna",
                "stage_name": "El Heredero de Montería",
                "biography": "Joven maestro de los cuatro aires tradicionales, formado en los festivales regionales del Sinú.",
                "hometown": "Montería, Córdoba",
                "order_num": 3,
            },
        ]

        for opt_data in options_profesional:
            opt_obj, _ = Option.objects.get_or_create(
                voting=voting_profesional,
                candidate_name=opt_data["candidate_name"],
                defaults={
                    "stage_name": opt_data["stage_name"],
                    "biography": opt_data["biography"],
                    "hometown": opt_data["hometown"],
                    "order_num": opt_data["order_num"],
                    "is_active": True,
                }
            )
            self.stdout.write(self.style.SUCCESS(f"    [+] Candidate: {opt_obj.candidate_name}"))

        # Options for Canción Inédita
        options_inedita = [
            {
                "candidate_name": "La Nostalgia del Juglar (Paseo)",
                "stage_name": "Autor: Hernando Zabaleta",
                "biography": "Paseo nostálgico que evoca las serenatas de madrugada bajo los palos de mango en el Valledupar de antaño.",
                "hometown": "El Molino, La Guajira",
                "order_num": 1,
            },
            {
                "candidate_name": "Canto a la Sierra Nevada (Merengue)",
                "stage_name": "Autora: Carolina Maestre",
                "biography": "Merengue de rítmica viva y versos dedicados a la protección de las fuentes hídricas del río Guatapurí.",
                "hometown": "Valledupar, Cesar",
                "order_num": 2,
            },
        ]

        for opt_data in options_inedita:
            opt_obj, _ = Option.objects.get_or_create(
                voting=voting_inedita,
                candidate_name=opt_data["candidate_name"],
                defaults={
                    "stage_name": opt_data["stage_name"],
                    "biography": opt_data["biography"],
                    "hometown": opt_data["hometown"],
                    "order_num": opt_data["order_num"],
                    "is_active": True,
                }
            )
            self.stdout.write(self.style.SUCCESS(f"    [+] Song Option: {opt_obj.candidate_name}"))

        self.stdout.write(self.style.SUCCESS(">>> Festival Vallenato 2027 Seed Process successfully finished!"))
