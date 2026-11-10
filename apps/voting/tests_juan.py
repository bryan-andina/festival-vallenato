import json
import threading
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.db import IntegrityError, close_old_connections, connection, transaction
from django.test import Client, TestCase, TransactionTestCase, skipUnlessDBFeature
from django.urls import reverse
from django.utils import timezone

from apps.voting.models import Category, Edition, Option, Vote, Voting

User = get_user_model()


class JuanMatrixBase:
    password = "TestJuan2026!"

    def build_fixture(self):
        self.edition = Edition.objects.create(
            name="Festival Vallenato 2027 - Matriz Juan",
            year=2027,
            start_date=date(2027, 4, 26),
            end_date=date(2027, 5, 2),
            is_active=True,
        )
        self.category_a = Category.objects.create(
            edition=self.edition,
            name="Acordeon Profesional - Juan",
            code="acordeon-profesional-juan",
            is_active=True,
        )
        self.category_b = Category.objects.create(
            edition=self.edition,
            name="Cancion Inedita - Juan",
            code="cancion-inedita-juan",
            is_active=True,
        )
        now = timezone.now()
        window = {
            "start_datetime": now - timedelta(hours=1),
            "end_datetime": now + timedelta(days=2),
        }
        self.voting_a1 = Voting.objects.create(
            category=self.category_a,
            title="Primera ronda profesional - Juan",
            status=Voting.Status.OPEN,
            max_votes_per_user=1,
            **window,
        )
        self.voting_a2 = Voting.objects.create(
            category=self.category_a,
            title="Final profesional - Juan",
            status=Voting.Status.OPEN,
            max_votes_per_user=1,
            **window,
        )
        self.voting_b = Voting.objects.create(
            category=self.category_b,
            title="Cancion inedita - Juan",
            status=Voting.Status.OPEN,
            max_votes_per_user=1,
            **window,
        )
        self.option_a1 = Option.objects.create(
            voting=self.voting_a1,
            candidate_name="Candidato A1",
            order_num=1,
            is_active=True,
        )
        self.option_a2 = Option.objects.create(
            voting=self.voting_a2,
            candidate_name="Candidato A2",
            order_num=1,
            is_active=True,
        )
        self.option_b = Option.objects.create(
            voting=self.voting_b,
            candidate_name="Candidato B",
            order_num=1,
            is_active=True,
        )
        self.user = User.objects.create_user(
            username="juan_matrix_voter",
            email="juan.matrix@example.com",
            password=self.password,
        )
        self.user2 = User.objects.create_user(
            username="juan_matrix_voter2",
            email="juan.matrix2@example.com",
            password=self.password,
        )
        self.admin = User.objects.create_superuser(
            username="juan_matrix_admin",
            email="juan.admin@example.com",
            password=self.password,
        )

    def vote_url(self, voting, option):
        return reverse(
            "voting:cast_vote",
            kwargs={"voting_id": voting.id, "option_id": option.id},
        )

    @staticmethod
    def response_messages(response):
        return " ".join(str(m) for m in get_messages(response.wsgi_request))


class JuanFunctionalMatrixTests(JuanMatrixBase, TestCase):
    def setUp(self):
        self.build_fixture()

    def test_cp01_registro_exitoso_en_base_de_datos(self):
        """CP-01: un voto valido queda persistido con usuario, edicion, categoria, votacion y opcion."""
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(self.vote_url(self.voting_a1, self.option_a1))

        self.assertEqual(response.status_code, 302)
        vote = Vote.objects.get(user=self.user, category=self.category_a, edition=self.edition)
        self.assertEqual(vote.voting, self.voting_a1)
        self.assertEqual(vote.selected_option, self.option_a1)

    def test_cp02_bloqueo_de_voto_duplicado_en_misma_categoria(self):
        """CP-02: un segundo voto en la misma categoria/edicion se bloquea incluso en otro subevento."""
        self.client.login(username=self.user.username, password=self.password)
        self.client.post(self.vote_url(self.voting_a1, self.option_a1))
        response = self.client.post(self.vote_url(self.voting_a2, self.option_a2), follow=True)

        self.assertContains(response, "Ya has emitido tu voto")
        self.assertEqual(
            Vote.objects.filter(user=self.user, category=self.category_a, edition=self.edition).count(),
            1,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Vote.objects.create(
                    user=self.user,
                    edition=self.edition,
                    category=self.category_a,
                    voting=self.voting_a2,
                    selected_option=self.option_a2,
                )

    def test_cp03_permita_votar_en_otra_categoria(self):
        """CP-03: el mismo usuario puede registrar un voto en una categoria diferente de la misma edicion."""
        self.client.login(username=self.user.username, password=self.password)
        self.client.post(self.vote_url(self.voting_a1, self.option_a1))
        response = self.client.post(self.vote_url(self.voting_b, self.option_b))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Vote.objects.filter(user=self.user, edition=self.edition).count(), 2)
        self.assertTrue(Vote.objects.filter(user=self.user, category=self.category_a).exists())
        self.assertTrue(Vote.objects.filter(user=self.user, category=self.category_b).exists())

    def test_cp04_control_de_autenticacion_en_interfaz(self):
        """CP-04: un anonimo ve la invitacion a iniciar sesion y no puede ejecutar el POST de voto."""
        detail = self.client.get(
            reverse("voting:voting_detail", kwargs={"voting_id": self.voting_a1.id})
        )
        self.assertContains(detail, "Inicia sesión para votar")

        post = self.client.post(self.vote_url(self.voting_a1, self.option_a1))
        self.assertEqual(post.status_code, 302)
        self.assertIn(reverse("accounts:login"), post.url)
        self.assertEqual(Vote.objects.count(), 0)

    def test_cp05_rechazo_de_categoria_inactiva_y_votacion_cerrada(self):
        """CP-05: no se registra voto si la categoria esta inactiva o la votacion esta cerrada."""
        self.client.login(username=self.user.username, password=self.password)

        self.category_a.is_active = False
        self.category_a.save(update_fields=["is_active"])
        response = self.client.post(self.vote_url(self.voting_a1, self.option_a1), follow=True)
        self.assertEqual(Vote.objects.count(), 0)
        self.assertContains(response, "no se encuentra habilitada")

        self.category_a.is_active = True
        self.category_a.save(update_fields=["is_active"])
        self.voting_a1.status = Voting.Status.CLOSED
        self.voting_a1.save(update_fields=["status"])
        response = self.client.post(self.vote_url(self.voting_a1, self.option_a1), follow=True)
        self.assertEqual(Vote.objects.count(), 0)
        self.assertContains(response, "no se encuentra abierta")

    def test_cp06_rechazo_de_opcion_ajena(self):
        """CP-06: una opcion que pertenece a otra votacion/categoria no puede usarse en el POST."""
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(self.vote_url(self.voting_a1, self.option_b), follow=True)

        self.assertEqual(Vote.objects.count(), 0)
        self.assertContains(response, "no pertenece")

    def test_cp07_historial_de_participacion_del_usuario(self):
        """CP-07: /my-votes/ lista fecha, categoria y opcion del usuario autenticado."""
        Vote.objects.create(
            user=self.user,
            edition=self.edition,
            category=self.category_a,
            voting=self.voting_a1,
            selected_option=self.option_a1,
        )
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.get(reverse("voting:my_votes"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mis Categorías Votadas")
        self.assertContains(response, self.category_a.name)
        self.assertContains(response, self.option_a1.candidate_name)
        self.assertContains(response, "Voto Registrado")

    def test_cp08_consulta_administrativa_y_metricas(self):
        """CP-08: VoteAdmin es solo lectura y sus metricas coinciden con los votos almacenados."""
        Vote.objects.create(
            user=self.user,
            edition=self.edition,
            category=self.category_a,
            voting=self.voting_a1,
            selected_option=self.option_a1,
        )
        Vote.objects.create(
            user=self.user2,
            edition=self.edition,
            category=self.category_b,
            voting=self.voting_b,
            selected_option=self.option_b,
        )
        self.client.login(username=self.admin.username, password=self.password)
        response = self.client.get(reverse("admin:voting_vote_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["vote_total"], Vote.objects.count())
        self.assertEqual(response.context["vote_total"], 2)
        self.assertEqual(self.client.get(reverse("admin:voting_vote_add")).status_code, 403)

    def test_cp10_api_get_categorias_devuelve_json_valido(self):
        """CP-10: GET /api/categorias/ devuelve JSON y rechaza metodos distintos de GET."""
        response = self.client.get("/api/categorias/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("application/json"))

        payload = json.loads(response.content)
        ids = {item["id"] for item in payload["categorias"]}
        self.assertIn(self.category_a.id, ids)
        self.assertIn(self.category_b.id, ids)
        self.assertEqual(self.client.post("/api/categorias/").status_code, 405)


class JuanConcurrencyTest(JuanMatrixBase, TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.build_fixture()

    def test_cp09_concurrencia_deja_un_solo_voto(self):
        """CP-09: dos transacciones simultaneas sobre la misma categoria dejan exactamente un voto."""
        if connection.vendor != "mysql":
            self.skipTest("CP-09 debe ejecutarse con MySQL para validar concurrencia real.")

        barrier = threading.Barrier(2)
        outcomes = []
        lock = threading.Lock()

        attempts = [
            (self.voting_a1.id, self.option_a1.id),
            (self.voting_a2.id, self.option_a2.id),
        ]

        def worker(voting_id, option_id):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                with transaction.atomic():
                    user = User.objects.get(pk=self.user.pk)
                    edition = Edition.objects.get(pk=self.edition.pk)
                    category = Category.objects.get(pk=self.category_a.pk)
                    voting = Voting.objects.get(pk=voting_id)
                    option = Option.objects.get(pk=option_id)
                    Vote.objects.create(
                        user=user,
                        edition=edition,
                        category=category,
                        voting=voting,
                        selected_option=option,
                    )
                result = "CREATED"
            except IntegrityError:
                result = "BLOCKED_BY_UNIQUE_CONSTRAINT"
            finally:
                close_old_connections()
            with lock:
                outcomes.append(result)

        threads = [threading.Thread(target=worker, args=args) for args in attempts]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=20)

        self.assertEqual(len(outcomes), 2)
        self.assertEqual(outcomes.count("CREATED"), 1)
        self.assertEqual(outcomes.count("BLOCKED_BY_UNIQUE_CONSTRAINT"), 1)
        self.assertEqual(
            Vote.objects.filter(
                user=self.user,
                edition=self.edition,
                category=self.category_a,
            ).count(),
            1,
        )
