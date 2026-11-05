from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from apps.voting.models import Edition, Category, Voting, Option, Vote

User = get_user_model()


class VotingDomainModelTests(TestCase):
    def setUp(self):
        self.edition = Edition.objects.create(
            name="60° Festival de la Leyenda Vallenata 2027",
            year=2027,
            start_date=date(2027, 4, 26),
            end_date=date(2027, 5, 2),
            is_active=True
        )
        self.category = Category.objects.create(
            edition=self.edition,
            name="Acordeón Profesional",
            code="acordeon-profesional",
            is_active=True
        )
        now = timezone.now()
        self.voting = Voting.objects.create(
            category=self.category,
            title="Elección Popular Rey Vallenato Profesional 2027",
            status=Voting.Status.OPEN,
            start_datetime=now - timedelta(days=1),
            end_datetime=now + timedelta(days=5),
            max_votes_per_user=1
        )
        self.option = Option.objects.create(
            voting=self.voting,
            candidate_name="Javier Matta Correa",
            stage_name="El Pollo de Santa Marta",
            hometown="Santa Marta",
            order_num=1
        )

    def test_edition_str_representation(self):
        self.assertEqual(str(self.edition), "60° Festival de la Leyenda Vallenata 2027 (2027)")

    def test_category_relationship(self):
        self.assertEqual(self.category.edition, self.edition)
        self.assertIn(self.category, self.edition.categories.all())

    def test_voting_is_currently_open(self):
        self.assertTrue(self.voting.is_currently_open)

    def test_option_belongs_to_voting(self):
        self.assertEqual(self.option.voting, self.voting)
        self.assertEqual(self.voting.options.count(), 1)


class VotingPublicViewsTests(TestCase):
    def setUp(self):
        self.edition = Edition.objects.create(
            name="60° Festival de la Leyenda Vallenata 2027",
            year=2027,
            start_date=date(2027, 4, 26),
            end_date=date(2027, 5, 2),
            is_active=True
        )
        self.category = Category.objects.create(
            edition=self.edition,
            name="Acordeón Profesional",
            code="acordeon-profesional",
            is_active=True
        )
        now = timezone.now()
        self.voting = Voting.objects.create(
            category=self.category,
            title="Elección Popular Rey Vallenato Profesional 2027",
            status=Voting.Status.OPEN,
            start_datetime=now - timedelta(days=1),
            end_datetime=now + timedelta(days=5),
            max_votes_per_user=1
        )
        self.option = Option.objects.create(
            voting=self.voting,
            candidate_name="Javier Matta Correa",
            stage_name="El Pollo de Santa Marta",
            order_num=1
        )
        self.user = User.objects.create_user(
            username="voter_test",
            password="testpassword123"
        )

    def test_edition_list_view_status_code(self):
        response = self.client.get(reverse("voting:edition_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "60° Festival de la Leyenda Vallenata 2027")

    def test_category_list_view_status_code(self):
        response = self.client.get(reverse("voting:category_list", kwargs={"year": 2027}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Acordeón Profesional")

    def test_voting_detail_view_status_code(self):
        response = self.client.get(reverse("voting:voting_detail", kwargs={"voting_id": self.voting.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Elección Popular Rey Vallenato")

    def test_cast_vote_successful(self):
        self.client.login(username="voter_test", password="testpassword123")
        url = reverse("voting:cast_vote", kwargs={"voting_id": self.voting.id, "option_id": self.option.id})
        response = self.client.post(url)
        self.assertRedirects(response, reverse("voting:voting_detail", kwargs={"voting_id": self.voting.id}))
        self.assertEqual(Vote.objects.filter(user=self.user, voting=self.voting).count(), 1)

    def test_cast_vote_duplicate_prevented(self):
        self.client.login(username="voter_test", password="testpassword123")
        url = reverse("voting:cast_vote", kwargs={"voting_id": self.voting.id, "option_id": self.option.id})
        self.client.post(url)
        response = self.client.post(url)
        self.assertRedirects(response, reverse("voting:voting_detail", kwargs={"voting_id": self.voting.id}))
        self.assertEqual(Vote.objects.filter(user=self.user, voting=self.voting).count(), 1)
import threading
from django.db import connection, IntegrityError, transaction
from django.test import TransactionTestCase
class BryanVoteIntegrityTests(TestCase):
    def setUp(self):
        self.edition = Edition.objects.create(
            name="60° Festival de la Leyenda Vallenata 2027",
            year=2027,
            start_date=date(2027, 4, 26),
            end_date=date(2027, 5, 2),
            is_active=True
        )
        self.category_profesional = Category.objects.create(
            edition=self.edition,
            name="Acordeón Profesional",
            code="acordeon-profesional",
            is_active=True
        )
        self.category_cancion = Category.objects.create(
            edition=self.edition,
            name="Canción Vallenata Inédita",
            code="cancion-inedita",
            is_active=True
        )
        now = timezone.now()
        self.voting_subevent_1 = Voting.objects.create(
            category=self.category_profesional,
            title="Primera Ronda Acordeón Profesional",
            status=Voting.Status.OPEN,
            start_datetime=now - timedelta(days=1),
            end_datetime=now + timedelta(days=5),
            max_votes_per_user=1
        )
        self.voting_subevent_2 = Voting.objects.create(
            category=self.category_profesional,
            title="Final Acordeón Profesional",
            status=Voting.Status.OPEN,
            start_datetime=now - timedelta(days=1),
            end_datetime=now + timedelta(days=5),
            max_votes_per_user=1
        )
        self.voting_cancion = Voting.objects.create(
            category=self.category_cancion,
            title="Final Canción Inédita",
            status=Voting.Status.OPEN,
            start_datetime=now - timedelta(days=1),
            end_datetime=now + timedelta(days=5),
            max_votes_per_user=1
        )
        self.option_1 = Option.objects.create(
            voting=self.voting_subevent_1,
            candidate_name="Javier Matta",
            order_num=1
        )
        self.option_2 = Option.objects.create(
            voting=self.voting_subevent_2,
            candidate_name="Alfonso Ponce",
            order_num=1
        )
        self.option_cancion = Option.objects.create(
            voting=self.voting_cancion,
            candidate_name="La Nostalgia del Juglar",
            order_num=1
        )
        self.user = User.objects.create_user(
            username="voter_bryan_test",
            password="testpassword123"
        )

    def test_cp01_cast_valid_vote_persists_in_database(self):
        """CP-01: Usuario autenticado selecciona una opción válida -> Se registra un voto en la base de datos."""
        self.client.login(username="voter_bryan_test", password="testpassword123")
        url = reverse("voting:cast_vote", kwargs={"voting_id": self.voting_subevent_1.id, "option_id": self.option_1.id})
        response = self.client.post(url)
        self.assertRedirects(response, reverse("voting:voting_detail", kwargs={"voting_id": self.voting_subevent_1.id}))

        vote = Vote.objects.filter(user=self.user, category=self.category_profesional).first()
        self.assertIsNotNone(vote)
        self.assertEqual(vote.edition, self.edition)
        self.assertEqual(vote.category, self.category_profesional)
        self.assertEqual(vote.voting, self.voting_subevent_1)
        self.assertEqual(vote.selected_option, self.option_1)

    def test_cp02_reject_second_vote_same_category_different_subevent(self):
        """CP-02: Intenta votar otra vez en la misma categoría, por otra opción o subevento -> Se rechaza."""
        self.client.login(username="voter_bryan_test", password="testpassword123")
        url_1 = reverse("voting:cast_vote", kwargs={"voting_id": self.voting_subevent_1.id, "option_id": self.option_1.id})
        self.client.post(url_1)

        url_2 = reverse("voting:cast_vote", kwargs={"voting_id": self.voting_subevent_2.id, "option_id": self.option_2.id})
        response = self.client.post(url_2, follow=True)

        self.assertContains(response, "Ya has emitido tu voto en la categoría")
        self.assertEqual(Vote.objects.filter(user=self.user, category=self.category_profesional).count(), 1)

    def test_cp02_database_unique_constraint_enforcement(self):
        """CP-02 (DB Level): La restricción UniqueConstraint en MySQL/BD rechaza duplicados a nivel de motor."""
        Vote.objects.create(
            user=self.user,
            edition=self.edition,
            category=self.category_profesional,
            voting=self.voting_subevent_1,
            selected_option=self.option_1
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Vote.objects.create(
                    user=self.user,
                    edition=self.edition,
                    category=self.category_profesional,
                    voting=self.voting_subevent_2,
                    selected_option=self.option_2
                )

    def test_cp09_concurrent_requests_handled_by_view(self):
        """CP-09: Dos solicitudes simultáneas a la misma categoría -> La DB frena la segunda con IntegrityError y solo queda 1 voto."""
        self.client.login(username="voter_bryan_test", password="testpassword123")
        url = reverse("voting:cast_vote", kwargs={"voting_id": self.voting_subevent_1.id, "option_id": self.option_1.id})

        # Primera solicitud se registra exitosamente
        response1 = self.client.post(url, follow=True)
        self.assertContains(response1, "ha sido registrado exitosamente")
        self.assertEqual(Vote.objects.filter(user=self.user, category=self.category_profesional).count(), 1)

        # Segunda solicitud concurrente: CastVoteView captura IntegrityError y no duplica
        from unittest.mock import patch
        with patch.object(Vote.objects, "create", side_effect=IntegrityError("Duplicate entry")):
            response2 = self.client.post(url, follow=True)
            self.assertContains(response2, "Ya has emitido tu voto")

        # En la base de datos se mantiene exactamente un voto
        self.assertEqual(Vote.objects.filter(user=self.user, category=self.category_profesional).count(), 1)
