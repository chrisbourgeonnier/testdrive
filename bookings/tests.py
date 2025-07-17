from django.test import TestCase
from django.urls import reverse

class BookingTests(TestCase):
    def test_booking_list_resolves_and_loads(self):
        response = self.client.get(reverse('booking_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bookings')
