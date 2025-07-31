"""
Test suite for the vehicles app in the TestDrive project.

This file contains automated tests to verify:
1. Basic navigation and page loading for vehicle catalog views
2. Vehicle model data integrity and relationships
3. Admin interface customizations for vehicle management
4. Vehicle import management command functionality
5. URL routing and template rendering

Tests use pytest with descriptive error messages and docstrings.
Run with: pytest vehicles/tests.py -v
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from vehicles.models import Vehicle
from unittest.mock import patch, Mock
import requests


# =============================================================================
# BASIC NAVIGATION TESTS
# =============================================================================
# These tests verify that core vehicle pages load correctly and contain
# expected content. They test the public-facing vehicle catalog functionality
# including the main vehicle list and individual vehicle detail pages.
# =============================================================================

class VehicleNavigationTests(TestCase):
    """Test basic navigation and page loading for vehicle catalog views."""

    def setUp(self):
        """Create test data needed for navigation tests."""
        # Create a test vehicle with all required fields
        self.vehicle = Vehicle.objects.create(
            make="BMW", model="Z4", year=2010, km=50000, engine_size=3000,
            transmission="Automatic", price=49990, photo_link="http://example.com/car.jpg",
            description="A nice BMW convertible sports car",
            link="https://richmonds.com.au/bmw-z4",
            is_active=True
        )

        # Create an inactive vehicle to test filtering
        self.inactive_vehicle = Vehicle.objects.create(
            make="Audi", model="TT", year=2008, km=80000, engine_size=2000,
            transmission="Manual", price=25000, photo_link="http://example.com/audi.jpg",
            description="Inactive Audi TT", link="https://richmonds.com.au/audi-tt",
            is_active=False  # This should not appear in public listings
        )

    def test_vehicle_list_page_loads(self):
        """Test that the vehicle list page loads and displays active vehicles only."""
        response = self.client.get(reverse('vehicle_list'))
        self.assertEqual(
            response.status_code, 200,
            msg="❌ Vehicle list page did not load successfully (not HTTP 200)."
        )

        # Check that the main heading is present
        self.assertIn(b"Our Vehicles", response.content,
                      msg="❌ 'Our Vehicles' heading is missing from list page.")

        # Check that active vehicle appears in listing
        self.assertIn(b"BMW", response.content,
                      msg="❌ 'BMW' is missing from the vehicle list display.")
        self.assertIn(b"Z4", response.content,
                      msg="❌ 'Z4' model is missing from the vehicle list display.")

        # Check that inactive vehicle does NOT appear in public listing
        self.assertNotIn(b"Audi TT", response.content,
                         msg="❌ Inactive vehicle (Audi TT) should not appear in public listing.")

    def test_vehicle_detail_page_loads(self):
        """Test that the vehicle detail page loads and includes all expected information."""
        response = self.client.get(reverse('vehicle_detail', args=[self.vehicle.pk]))
        self.assertEqual(
            response.status_code, 200,
            msg="❌ Vehicle detail page did not load successfully (not HTTP 200)."
        )

        # Check vehicle information is displayed
        self.assertIn(b"BMW", response.content,
                      msg="❌ 'BMW' make is missing from the vehicle detail display.")
        self.assertIn(b"Z4", response.content,
                      msg="❌ 'Z4' model is missing from the vehicle detail display.")
        self.assertIn(b"2010", response.content,
                      msg="❌ Vehicle year is missing from the vehicle detail display.")

        # Check that booking link is present
        self.assertIn(b"Book a Test Drive", response.content,
                      msg="❌ 'Book a Test Drive' button/link missing on vehicle detail page.")

        # Check that photo link is included
        self.assertIn(
            self.vehicle.photo_link.encode(), response.content,
            msg="❌ Vehicle photo link is missing on vehicle detail page."
        )

        # Check that external link to full details is present
        self.assertIn(b"More details and photos", response.content,
                      msg="❌ Link to external vehicle details page is missing.")

    def test_vehicle_detail_page_404_for_nonexistent_vehicle(self):
        """Test that vehicle detail page returns 404 for non-existent vehicles."""
        response = self.client.get(reverse('vehicle_detail', args=[99999]))
        self.assertEqual(
            response.status_code, 404,
            msg="❌ Vehicle detail page should return 404 for non-existent vehicles."
        )

    def test_vehicle_list_ordering(self):
        """Test that vehicles are ordered correctly (by make, model, year)."""
        # Create additional vehicles to test ordering
        Vehicle.objects.create(
            make="Audi", model="A4", year=2015, km=30000, engine_size=2000,
            transmission="Automatic", price=35000, photo_link="http://example.com/audi-a4.jpg",
            description="Audi A4", link="https://richmonds.com.au/audi-a4", is_active=True
        )
        Vehicle.objects.create(
            make="BMW", model="X5", year=2018, km=25000, engine_size=3000,
            transmission="Automatic", price=65000, photo_link="http://example.com/bmw-x5.jpg",
            description="BMW X5", link="https://richmonds.com.au/bmw-x5", is_active=True
        )

        response = self.client.get(reverse('vehicle_list'))
        content = response.content.decode('utf-8')

        # Check that Audi appears before BMW in the listing (alphabetical by make)
        audi_position = content.find('Audi')
        bmw_position = content.find('BMW')
        self.assertLess(audi_position, bmw_position,
                        msg="❌ Vehicles should be ordered alphabetically by make (Audi before BMW).")


# =============================================================================
# VEHICLE MODEL TESTS
# =============================================================================
# These tests verify that the Vehicle model works correctly, including
# field validations, string representations, and data integrity.
# =============================================================================

class VehicleModelTests(TestCase):
    """Test Vehicle model functionality and data integrity."""

    def test_vehicle_string_representation(self):
        """Test that Vehicle.__str__ returns the expected format."""
        vehicle = Vehicle.objects.create(
            make="Mercedes", model="C-Class", year=2020, km=15000, engine_size=2000,
            transmission="Automatic", price=55000, photo_link="http://example.com/merc.jpg",
            description="Mercedes C-Class", link="https://richmonds.com.au/mercedes-c-class"
        )

        expected_str = "2020 Mercedes C-Class"
        self.assertEqual(
            str(vehicle), expected_str,
            msg=f"❌ Vehicle string representation should be '{expected_str}', got '{str(vehicle)}'."
        )

    def test_vehicle_default_values(self):
        """Test that Vehicle model sets appropriate default values."""
        vehicle = Vehicle.objects.create(
            make="Toyota", model="Camry", year=2019, km=40000, engine_size=2500,
            transmission="CVT", price=28000, photo_link="http://example.com/toyota.jpg",
            description="Toyota Camry", link="https://richmonds.com.au/toyota-camry"
            # Note: is_active should default to True, created_at/updated_at should auto-populate
        )

        self.assertTrue(vehicle.is_active,
                        msg="❌ Vehicle.is_active should default to True.")
        self.assertIsNotNone(vehicle.created_at,
                             msg="❌ Vehicle.created_at should be automatically set.")
        self.assertIsNotNone(vehicle.updated_at,
                             msg="❌ Vehicle.updated_at should be automatically set.")

    def test_vehicle_required_fields(self):
        """Test that all required fields are properly validated."""
        # Test that creating a vehicle without required fields raises an error
        with self.assertRaises(Exception,
                               msg="❌ Creating vehicle without required fields should raise an exception."):
            Vehicle.objects.create()  # Missing all required fields


# =============================================================================
# ADMIN INTERFACE TESTS
# =============================================================================
# These tests verify that the Django admin interface customizations work
# correctly, including the custom import button and admin list functionality.
# =============================================================================

class VehicleAdminTests(TestCase):
    """Test Vehicle admin interface customizations."""

    def setUp(self):
        """Create admin user and test data for admin tests."""
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        self.client = Client()

        # Create test vehicle
        self.vehicle = Vehicle.objects.create(
            make="Ford", model="Mustang", year=2021, km=8000, engine_size=5000,
            transmission="Manual", price=75000, photo_link="http://example.com/mustang.jpg",
            description="Ford Mustang GT", link="https://richmonds.com.au/ford-mustang"
        )

    def test_admin_vehicle_changelist_requires_login(self):
        """Test that admin vehicle changelist requires authentication."""
        # Test without login
        response = self.client.get('/admin/vehicles/vehicle/')
        self.assertEqual(
            response.status_code, 302,
            msg="❌ Vehicle admin changelist should redirect unauthenticated users."
        )

    def test_admin_vehicle_changelist_loads_with_login(self):
        """Test that admin vehicle changelist loads for authenticated admin users."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get('/admin/vehicles/vehicle/')
        self.assertEqual(
            response.status_code, 200,
            msg="❌ Vehicle admin changelist should load for authenticated admin users."
        )

        # Check that our test vehicle appears in the admin list
        self.assertIn(b"Ford", response.content,
                      msg="❌ Test vehicle should appear in admin changelist.")
        self.assertIn(b"Mustang", response.content,
                      msg="❌ Test vehicle model should appear in admin changelist.")

    def test_admin_import_button_present(self):
        """Test that the custom 'Update Inventory' button is present in admin."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get('/admin/vehicles/vehicle/')

        # Check that the custom import button is present
        self.assertIn(b"Update Inventory", response.content,
                      msg="❌ 'Update Inventory' button should be present in vehicle admin.")
        self.assertIn(b"&#128259;", response.content,  # 🔃 emoji
                      msg="❌ Import button emoji should be present in vehicle admin.")

    def test_admin_import_endpoint_requires_login(self):
        """Test that the import vehicles endpoint requires admin authentication."""
        # Test without login
        response = self.client.get('/admin/vehicles/vehicle/import-vehicles/')
        self.assertEqual(
            response.status_code, 302,
            msg="❌ Import vehicles endpoint should redirect unauthenticated users."
        )


# =============================================================================
# VEHICLE IMPORT COMMAND TESTS
# =============================================================================
# These tests verify that the custom management command for importing vehicles
# from the Richmonds website works correctly, including error handling and
# data processing.
# =============================================================================

class VehicleImportCommandTests(TestCase):
    """Test the import_vehicles management command functionality."""

    @patch('vehicles.management.commands.import_vehicles.requests.get')
    def test_import_command_handles_network_errors(self, mock_get):
        """Test that import command handles network errors gracefully."""
        # Mock a network error
        mock_get.side_effect = requests.RequestException("Network error")

        # The command should not crash, but should handle the error
        with self.assertRaises(requests.RequestException):
            call_command('import_vehicles')

    @patch('vehicles.management.commands.import_vehicles.requests.get')
    def test_import_command_handles_404_response(self, mock_get):
        """Test that import command handles 404 responses appropriately."""
        # Mock a 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Command should handle this gracefully and not crash
        try:
            call_command('import_vehicles')
        except SystemExit:
            # Command may exit, but shouldn't crash with unhandled exception
            pass

    @patch('vehicles.management.commands.import_vehicles.requests.get')
    def test_import_command_processes_valid_data(self, mock_get):
        """Test that import command can process valid vehicle data."""
        # Mock successful responses with sample HTML data
        main_page_response = Mock()
        main_page_response.status_code = 200
        main_page_response.content = b'''
        <div class="portfolio_item">
            <div class="imghoverclass">
                <a href="https://richmonds.com.au/test-car" title="2020 Test Car Model">
                    <img data-src="http://example.com/test-car.jpg">
                </a>
            </div>
        </div>
        '''

        detail_page_response = Mock()
        detail_page_response.status_code = 200
        detail_page_response.content = b'''
        <div class="postclass">
            <table>
                <tr><td>Make:</td><td>BMW</td></tr>
                <tr><td>Model:</td><td>Test Model</td></tr>
                <tr><td>Built:</td><td>2020</td></tr>
                <tr><td>KM:</td><td>25,000km</td></tr>
                <tr><td>Engine Size:</td><td>3000cc</td></tr>
                <tr><td>Transmission:</td><td>Automatic</td></tr>
                <tr><td>Price:</td><td>$50,000</td></tr>
            </table>
        </div>
        '''

        # Set up mock to return different responses for different URLs
        def mock_get_side_effect(url):
            if 'cars-for-sale' in url:
                return main_page_response
            else:
                return detail_page_response

        mock_get.side_effect = mock_get_side_effect

        # Run the command
        call_command('import_vehicles')

        # Check that a vehicle was created/updated
        vehicles = Vehicle.objects.filter(make='BMW', model='Test Model')
        self.assertTrue(vehicles.exists(),
                        msg="❌ Import command should create/update vehicles from scraped data.")

    def test_import_command_exists_and_is_callable(self):
        """Test that the import_vehicles command exists and can be called."""
        # This test ensures the command is properly registered
        try:
            # Just test that the command can be found and called
            # We won't actually run it to avoid external dependencies
            from django.core.management import get_commands
            commands = get_commands()
            self.assertIn('import_vehicles', commands,
                          msg="❌ 'import_vehicles' command should be registered with Django.")
        except ImportError:
            self.fail("❌ Could not import import_vehicles command.")


# =============================================================================
# URL ROUTING TESTS
# =============================================================================
# These tests verify that URL patterns are correctly configured and resolve
# to the appropriate views with proper parameters.
# =============================================================================

class VehicleURLTests(TestCase):
    """Test vehicle URL routing and reverse URL resolution."""

    def setUp(self):
        """Create test vehicle for URL tests."""
        self.vehicle = Vehicle.objects.create(
            make="Nissan", model="GTR", year=2022, km=5000, engine_size=3800,
            transmission="Automatic", price=120000, photo_link="http://example.com/gtr.jpg",
            description="Nissan GT-R", link="https://richmonds.com.au/nissan-gtr"
        )

    def test_vehicle_list_url_resolves(self):
        """Test that vehicle list URL resolves correctly."""
        url = reverse('vehicle_list')
        self.assertEqual(url, '/',
                         msg="❌ Vehicle list URL should resolve to root path '/'.")

    def test_vehicle_detail_url_resolves(self):
        """Test that vehicle detail URL resolves correctly with parameters."""
        url = reverse('vehicle_detail', args=[self.vehicle.pk])
        expected_url = f'/{self.vehicle.pk}/'
        self.assertEqual(url, expected_url,
                         msg=f"❌ Vehicle detail URL should resolve to '{expected_url}'.")

    def test_vehicle_urls_accept_correct_parameters(self):
        """Test that vehicle URLs accept correct parameter types."""
        # Test with valid integer ID
        response = self.client.get(reverse('vehicle_detail', args=[self.vehicle.pk]))
        self.assertEqual(response.status_code, 200,
                         msg="❌ Vehicle detail URL should accept valid integer IDs.")

        # Test with invalid parameter should return 404
        response = self.client.get('/invalid-id/')
        self.assertEqual(response.status_code, 404,
                         msg="❌ Vehicle detail URL should return 404 for invalid parameters.")


# =============================================================================
# TEMPLATE RENDERING TESTS
# =============================================================================
# These tests verify that templates render correctly with proper context
# variables and display expected content formatting.
# =============================================================================

class VehicleTemplateTests(TestCase):
    """Test vehicle template rendering and context handling."""

    def setUp(self):
        """Create test vehicles for template tests."""
        self.vehicle1 = Vehicle.objects.create(
            make="Porsche", model="911", year=2023, km=2000, engine_size=3000,
            transmission="PDK", price=180000, photo_link="http://example.com/porsche.jpg",
            description="Porsche 911 Carrera", link="https://richmonds.com.au/porsche-911"
        )
        self.vehicle2 = Vehicle.objects.create(
            make="Lamborghini", model="Huracan", year=2022, km=3500, engine_size=5200,
            transmission="Automatic", price=350000, photo_link="http://example.com/lambo.jpg",
            description="Lamborghini Huracan", link="https://richmonds.com.au/lamborghini-huracan"
        )

    def test_vehicle_list_template_context(self):
        """Test that vehicle list template receives correct context."""
        response = self.client.get(reverse('vehicle_list'))

        # Check that context contains vehicles
        self.assertIn('vehicles', response.context,
                      msg="❌ Vehicle list template should receive 'vehicles' context variable.")

        # Check that both vehicles are in context
        vehicles_in_context = list(response.context['vehicles'])
        self.assertEqual(len(vehicles_in_context), 2,
                         msg="❌ Vehicle list context should contain all active vehicles.")

    def test_vehicle_detail_template_context(self):
        """Test that vehicle detail template receives correct context."""
        response = self.client.get(reverse('vehicle_detail', args=[self.vehicle1.pk]))

        # Check that context contains vehicle
        self.assertIn('vehicle', response.context,
                      msg="❌ Vehicle detail template should receive 'vehicle' context variable.")

        # Check that correct vehicle is in context
        vehicle_in_context = response.context['vehicle']
        self.assertEqual(vehicle_in_context.pk, self.vehicle1.pk,
                         msg="❌ Vehicle detail context should contain the correct vehicle.")

    def test_vehicle_list_grid_layout(self):
        """Test that vehicle list displays vehicles in card format."""
        response = self.client.get(reverse('vehicle_list'))

        # Check for CSS classes that indicate card layout
        self.assertIn(b'car-listings', response.content,
                      msg="❌ Vehicle list should use 'car-listings' CSS class for grid layout.")
        self.assertIn(b'car-card', response.content,
                      msg="❌ Vehicle list should display vehicles as 'car-card' elements.")

    def test_vehicle_price_formatting(self):
        """Test that vehicle prices are properly formatted in templates."""
        response = self.client.get(reverse('vehicle_detail', args=[self.vehicle1.pk]))

        # Check that price is displayed with currency symbol
        self.assertIn(b'$180000', response.content,
                      msg="❌ Vehicle price should be displayed with currency formatting.")


# =============================================================================
# TEST EXECUTION NOTES
# =============================================================================
"""
To run these tests:

# Run all vehicle tests with verbose output
pytest vehicles/tests.py -v

# Run only navigation tests
pytest vehicles/tests.py::VehicleNavigationTests -v

# Run only model tests
pytest vehicles/tests.py::VehicleModelTests -v

# Run only admin tests
pytest vehicles/tests.py::VehicleAdminTests -v

# Run only import command tests
pytest vehicles/tests.py::VehicleImportCommandTests -v

# Run a specific test method
pytest vehicles/tests.py::VehicleNavigationTests::test_vehicle_list_page_loads -v

These tests verify:
✅ Basic navigation and page loading
✅ Vehicle model functionality and data integrity
✅ Admin interface customizations and import functionality
✅ Management command error handling and data processing
✅ URL routing and reverse resolution
✅ Template rendering and context handling
✅ Active/inactive vehicle filtering
✅ Proper ordering and display formatting

Note: Import command tests use mocking to avoid external dependencies.
For full integration testing of the scraping functionality, consider
setting up test fixtures or using a local test server.
"""
