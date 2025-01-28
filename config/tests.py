from django.test import TestCase
from django.urls import reverse


class TestHomePage(TestCase):
    def test_home_page_status_code(self):
        home = reverse('home')
        response = self.client.get(home)
        self.assertEqual(response.status_code, 200)

    def test_home_page_context(self):
        home = reverse('home')
        response = self.client.get(home)
        instruments = response.context.get('instruments', None)
        practice_url = response.context.get('practice_url', None)
        self.assertIsNotNone(instruments)
        self.assertIsNotNone(practice_url)
