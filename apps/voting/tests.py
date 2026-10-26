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
