from django.test import TestCase
from django.urls import reverse

class VehicleTests(TestCase):
    def test_vehicle_list_resolves_and_loads(self):
        response = self.client.get(reverse('vehicle_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vehicles')
