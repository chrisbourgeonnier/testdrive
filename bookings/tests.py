from django.test import TestCase
from django.urls import reverse
from vehicles.models import Vehicle
from bookings.models import Booking

class BookingTests(TestCase):
    def test_booking_list_resolves_and_loads(self):
        response = self.client.get(reverse('booking_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bookings')

    def setUp(self):
        self.vehicle = Vehicle.objects.create(make="BMW", model="Z4", year=2010)

    def test_booking_form_page_loads(self):
        response = self.client.get(reverse('create_booking'))
        self.assertEqual(response.status_code, 200)

    def test_booking_submission_creates_booking(self):
        response = self.client.post(reverse('create_booking'), {
            'vehicle': self.vehicle.id,
            'guest_name': 'Test User',
            'guest_email': 'test@example.com',
            'guest_phone': '123456789',
            'requested_date': '2025-08-01',
            'requested_time': '10:30',
            'captcha_0': 'dummy-value',  # adjust based on real captcha
            'captcha_1': 'PASSED',  # or however your testing bypass works
        })
        # Redirects to the thanks page
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Booking.objects.filter(guest_name='Test User').exists())