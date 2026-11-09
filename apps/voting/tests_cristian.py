import json
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.voting.models import Edition, Category, Voting, Option, Vote

User = get_user_model()


class CristianServerValidationApiAdminTests(TestCase):
    """Integrante 3: CP-05, CP-06, CP-08 y CP-10."""

    def setUp(self):
        self.edition = Edition.objects.create(
            name="60° Festival de la Leyenda Vallenata 2027",
            year=2027,
            start_date=date(2027, 4, 26),
            end_date=date(2027, 5, 2),
            is_active=True
        )
        self.category_prof = Category.objects.create(
            edition=self.edition, name="Acordeón Profesional",
            code="acordeon-profesional", is_active=True
        )
        self.category_cancion = Category.objects.create(
            edition=self.edition, name="Canción Vallenata Inédita",
            code="cancion-inedita", is_active=True
        )
        self.category_inactiva = Category.objects.create(
            edition=self.edition, name="Categoría Inactiva",
            code="inactiva", is_active=False
        )
        now = timezone.now()
        window = {"start_datetime": now - timedelta(days=1), "end_datetime": now + timedelta(days=5)}
        self.voting_prof = Voting.objects.create(
            category=self.category_prof, title="Rey Profesional",
            status=Voting.Status.OPEN, **window
        )
        self.voting_prof_final = Voting.objects.create(
            category=self.category_prof, title="Final Profesional",
            status=Voting.Status.OPEN, **window
        )
        self.voting_cancion = Voting.objects.create(
            category=self.category_cancion, title="Canción Inédita",
            status=Voting.Status.OPEN, **window
        )
        self.option_prof = Option.objects.create(
            voting=self.voting_prof, candidate_name="Javier Matta", order_num=1
        )
        self.option_prof_final = Option.objects.create(
            voting=self.voting_prof_final, candidate_name="Alfonso Ponce", order_num=1
        )
        self.option_cancion = Option.objects.create(
            voting=self.voting_cancion, candidate_name="La Nostalgia del Juglar", order_num=1
        )
        self.user = User.objects.create_user(username="voter_cristian", password="testpassword123")
        self.user2 = User.objects.create_user(username="voter_cristian_2", password="testpassword123")
        self.admin_user = User.objects.create_superuser(
            username="admin_cristian", email="admin@test.co", password="testpassword123"
        )

    def _vote_url(self, voting, option):
        return reverse("voting:cast_vote", kwargs={"voting_id": voting.id, "option_id": option.id})

    def _messages(self, response):
        return [str(m) for m in get_messages(response.wsgi_request)]

    def test_cp05_rejects_vote_in_inactive_category(self):
        self.category_prof.is_active = False
        self.category_prof.save()
        self.client.login(username="voter_cristian", password="testpassword123")
        response = self.client.post(self._vote_url(self.voting_prof, self.option_prof))
        self.assertRedirects(response, reverse("voting:voting_detail", kwargs={"voting_id": self.voting_prof.id}))
        self.assertIn("no se encuentra habilitada", " ".join(self._messages(response)))
        self.assertEqual(Vote.objects.count(), 0)

    def test_cp05_rejects_vote_in_closed_voting(self):
        self.voting_prof.status = Voting.Status.CLOSED
        self.voting_prof.save()
        self.client.login(username="voter_cristian", password="testpassword123")
        response = self.client.post(self._vote_url(self.voting_prof, self.option_prof))
        self.assertIn("no se encuentra abierta", " ".join(self._messages(response)))
        self.assertEqual(Vote.objects.count(), 0)

    def test_cp05_rejects_vote_in_inactive_edition(self):
        self.edition.is_active = False
        self.edition.save()
        self.client.login(username="voter_cristian", password="testpassword123")
        response = self.client.post(self._vote_url(self.voting_prof, self.option_prof))
        self.assertIn("no se encuentra activa", " ".join(self._messages(response)))
        self.assertEqual(Vote.objects.count(), 0)

    def test_cp06_rejects_option_from_another_category(self):
        self.client.login(username="voter_cristian", password="testpassword123")
        response = self.client.post(self._vote_url(self.voting_prof, self.option_cancion))
        self.assertRedirects(response, reverse("voting:voting_detail", kwargs={"voting_id": self.voting_prof.id}))
        self.assertIn("no pertenece", " ".join(self._messages(response)))
        self.assertEqual(Vote.objects.count(), 0)

    def test_cp06_rejects_option_from_another_voting_same_category(self):
        self.client.login(username="voter_cristian", password="testpassword123")
        response = self.client.post(self._vote_url(self.voting_prof, self.option_prof_final))
        self.assertIn("no pertenece", " ".join(self._messages(response)))
        self.assertEqual(Vote.objects.count(), 0)

    def test_cp06_rejects_inactive_option(self):
        self.option_prof.is_active = False
        self.option_prof.save()
        self.client.login(username="voter_cristian", password="testpassword123")
        response = self.client.post(self._vote_url(self.voting_prof, self.option_prof))
        self.assertIn("no se encuentra habilitada", " ".join(self._messages(response)))
        self.assertEqual(Vote.objects.count(), 0)

    def _create_vote(self, user, voting, option):
        return Vote.objects.create(
            user=user, edition=self.edition, category=voting.category,
            voting=voting, selected_option=option
        )

    def test_cp08_admin_changelist_metrics_match_database(self):
        self._create_vote(self.user, self.voting_prof, self.option_prof)
        self._create_vote(self.user2, self.voting_prof, self.option_prof)
        self._create_vote(self.user, self.voting_cancion, self.option_cancion)
        self.client.login(username="admin_cristian", password="testpassword123")
        url = reverse("admin:voting_vote_changelist")

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["vote_total"], Vote.objects.count())
        self.assertEqual(response.context["vote_total"], 3)

        response = self.client.get(url, {"category__id__exact": self.category_prof.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["vote_total"],
            Vote.objects.filter(category=self.category_prof).count()
        )
        self.assertEqual(response.context["vote_total"], 2)

        response = self.client.get(url, {"edition__id__exact": self.edition.id})
        self.assertEqual(response.context["vote_total"], 3)

    def test_cp08_admin_is_read_only_and_requires_staff(self):
        self._create_vote(self.user, self.voting_prof, self.option_prof)
        self.client.login(username="voter_cristian", password="testpassword123")
        response = self.client.get(reverse("admin:voting_vote_changelist"))
        self.assertEqual(response.status_code, 302)

        self.client.login(username="admin_cristian", password="testpassword123")
        response = self.client.get(reverse("admin:voting_vote_add"))
        self.assertEqual(response.status_code, 403)

    def test_cp10_api_categories_returns_valid_json(self):
        response = self.client.get("/api/categorias/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("application/json"))
        payload = json.loads(response.content)

        active_ids = set(Category.objects.filter(is_active=True, edition__is_active=True).values_list("id", flat=True))
        self.assertEqual(payload["total"], len(active_ids))
        self.assertEqual({c["id"] for c in payload["categorias"]}, active_ids)
        self.assertNotIn(self.category_inactiva.id, {c["id"] for c in payload["categorias"]})

        prof = next(c for c in payload["categorias"] if c["id"] == self.category_prof.id)
        self.assertEqual(prof["nombre"], "Acordeón Profesional")
        self.assertEqual(prof["edicion"]["anio"], 2027)
        self.assertEqual(
            {o["id"] for o in prof["opciones"]},
            {self.option_prof.id, self.option_prof_final.id}
        )

    def test_cp10_api_rejects_non_get_methods(self):
        self.assertEqual(self.client.post("/api/categorias/").status_code, 405)