from django.test import TestCase
from django.urls import reverse
from vehicles.models import Vehicle
from django.core.management import call_command

class VehicleTests(TestCase):
    def test_vehicle_list_resolves_and_loads(self):
        response = self.client.get(reverse('vehicle_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vehicles')

    class VehicleViewTests(TestCase):
        # Test List View
        def setUp(self):
            Vehicle.objects.create(make="BMW", model="Z4", year=2010)

        def test_vehicle_list_displays_vehicles(self):
            response = self.client.get(reverse('vehicle_list'))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Z4")

        # Test Detail View
        def test_vehicle_detail_shows_fields(self):
            vehicle = Vehicle.objects.first()
            response = self.client.get(reverse('vehicle_detail', args=[vehicle.id]))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "BMW")
            self.assertContains(response, "Z4")

    # Test the import command
    # class ImportVehiclesCommandTests(TestCase):
    #     def test_import_vehicles_command_runs(self):
    #         # You might want to mock requests.get here for speed!
    #         call_command('import_vehicles')
    #         # Check at least one vehicle was imported, or test the logic on mock data
    #         self.assertTrue(Vehicle.objects.count() > 0)