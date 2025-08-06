from django.urls import reverse
from django.contrib.auth.models import User
from django.test import TestCase


# =============================================================================
# LOGIN VIEW TESTS
# =============================================================================
# These tests verify that the login view behaves correctly, including
# handling invalid credentials and displaying appropriate error messages.
class LoginViewTests(TestCase):
    def setUp(self):
        # Create a test user
        self.username = 'demo'
        self.password = 'testpassword123'
        User.objects.create_user(username=self.username, password=self.password)

    def test_login_with_wrong_credentials_shows_error(self):
        url = reverse('login')
        response = self.client.post(url, {'username': self.username, 'password': 'wrongpass'})
        # Should return 200 (form is re-rendered with errors)
        self.assertEqual(response.status_code, 200)
        # Should show error message in response content
        self.assertContains(response, "Please enter a correct username and password. Note that both fields may be case-sensitive.", html=True)

    def test_login_with_invalid_username(self):
        url = reverse('login')
        response = self.client.post(url, {'username': 'not-a-user', 'password': 'irrelevant'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a correct username and password. Note that both fields may be case-sensitive.", html=True)

