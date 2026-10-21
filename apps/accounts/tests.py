"""
Unit tests for the accounts authentication and registration workflows.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class AccountsWorkflowTests(TestCase):
    def test_user_registration_success(self):
        payload = {
            "username": "tester_valledupar",
            "first_name": "Diomedes",
            "last_name": "Diaz",
            "email": "diomedes@cantores.co",
            "password1": "Klk9928#Vallenato!",
            "password2": "Klk9928#Vallenato!",
        }
        response = self.client.post(reverse("accounts:register"), data=payload)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="tester_valledupar").exists())

    def test_user_login_and_logout(self):
        User.objects.create_user(
            username="voter_acordeon",
            password="Acordeon2027Password!",
            email="voter@festival.co"
        )
        login_response = self.client.post(reverse("accounts:login"), data={
            "username": "voter_acordeon",
            "password": "Acordeon2027Password!",
        })
        self.assertEqual(login_response.status_code, 302)

        logout_response = self.client.post(reverse("accounts:logout"))
        self.assertEqual(logout_response.status_code, 302)
