"""
Test suite for the bookings app in the TestDrive project.

This file contains automated tests to verify:
1. Basic navigation and page loading for booking-related views
2. FullCalendar backend integration for the admin calendar system
3. Authentication and permissions for admin-only features
4. Data integrity and JSON API endpoints

Tests use pytest with descriptive error messages and docstrings.
Run with: pytest bookings/tests.py -v
"""

import json
from datetime import date, time
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from vehicles.models import Vehicle
from bookings.models import Booking


# =============================================================================
# BASIC NAVIGATION TESTS
# =============================================================================
# These tests verify that core booking pages load correctly and contain
# expected content. They test the public-facing booking system functionality.
# =============================================================================

class BookingNavigationTests(TestCase):
    """Test basic navigation and page loading for booking-related views."""

    def setUp(self):
        """Create test data needed for navigation tests."""
        self.vehicle = Vehicle.objects.create(
            make="Audi", model="A4", year=2012, km=60000, engine_size=2000,
            transmission="Manual", price=20000, photo_link="http://example.com/audi.jpg",
            description="A nice Audi", link="https://dealer.com/audi-a4"
        )

    def test_booking_form_page_loads(self):
        """Test booking form loads (with and without vehicle preselection)."""
        # Test booking form without vehicle selected
        url = reverse('create_booking')
        response = self.client.get(url)
        self.assertEqual(
            response.status_code, 200,
            msg="❌ Booking form page did not load (no vehicle selected)."
        )
        self.assertIn(b"Book a Test Drive", response.content,
            msg="❌ Booking form title not present (no vehicle selected).")

        # Test booking form with vehicle pre-selected via URL parameter
        url_with_vehicle = f"{url}?vehicle={self.vehicle.pk}"
        response = self.client.get(url_with_vehicle)
        self.assertEqual(
            response.status_code, 200,
            msg="❌ Booking form page did not load (with vehicle selected)."
        )
        self.assertIn(b"Book a Test Drive", response.content,
            msg="❌ Booking form title not present (with vehicle selected).")
        self.assertIn(b"Audi", response.content,
            msg="❌ Vehicle make/model missing from booking form (with vehicle selected).")

    def test_booking_list_navigation(self):
        """Test booking list page loads and contains appropriate heading."""
        response = self.client.get(reverse('booking_list'))
        self.assertEqual(
            response.status_code, 200,
            msg="❌ Booking list page did not load (HTTP status != 200)."
        )
        self.assertIn(b"All Bookings", response.content,
            msg="❌ 'All Bookings' heading not found on booking list page.")

    def test_booking_thanks_navigation(self):
        """Test booking thanks page loads and displays a thank you message."""
        response = self.client.get(reverse('booking_thanks'))
        self.assertEqual(
            response.status_code, 200,
            msg="❌ Booking thank you page did not load (HTTP status != 200)."
        )
        self.assertIn(b"Thank You!", response.content,
            msg="❌ 'Thank You!' message not found on booking thanks page.")


# =============================================================================
# FULLCALENDAR BACKEND INTEGRATION TESTS
# =============================================================================
# These tests verify that the FullCalendar.js integration works correctly
# by testing the Django admin backend components that support the calendar:
# - Admin authentication for calendar pages
# - JSON API endpoints that provide booking data
# - Data formatting and status color coding
# - Datetime handling for calendar events
# =============================================================================

class FullCalendarTests(TestCase):
    """Test FullCalendar backend integration and admin calendar functionality."""

    def setUp(self):
        """Create test data needed for FullCalendar tests."""
        # Create admin user for accessing admin calendar views
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        self.client = Client()

        # Create test vehicle for bookings
        self.vehicle = Vehicle.objects.create(
            make="Tesla", model="Model S", year=2023, km=5000, engine_size=0,
            transmission="Automatic", price=89990, photo_link="http://example.com/tesla.jpg",
            description="Electric luxury sedan", link="https://dealer.com/tesla-model-s"
        )

        # Create test bookings with different statuses for comprehensive testing
        self.confirmed_booking = Booking.objects.create(
            vehicle=self.vehicle,
            guest_name="John Doe",
            guest_email="john@test.com",
            guest_phone="0412345678",
            requested_date=date(2025, 8, 15),
            requested_time=time(10, 30),
            status='confirmed'
        )

        self.pending_booking = Booking.objects.create(
            vehicle=self.vehicle,
            guest_name="Jane Smith",
            guest_email="jane@test.com",
            guest_phone="0487654321",
            requested_date=date(2025, 8, 16),
            requested_time=time(14, 0),
            status='pending'
        )

    # -------------------------------------------------------------------------
    # AUTHENTICATION & ACCESS CONTROL TESTS
    # -------------------------------------------------------------------------
    # Test that admin calendar features are properly protected

    def test_calendar_page_requires_admin_login(self):
        """Test that calendar page requires admin authentication."""
        # Test without login - should redirect to login page
        response = self.client.get('/admin/bookings/booking/calendar/')
        self.assertEqual(
            response.status_code, 302,
            msg="❌ Calendar page should redirect unauthenticated users."
        )

        # Test with admin login - should load successfully
        self.client.login(username='admin', password='testpass123')
        response = self.client.get('/admin/bookings/booking/calendar/')
        self.assertEqual(
            response.status_code, 200,
            msg="❌ Calendar page should load for authenticated admin users."
        )

    def test_calendar_events_endpoint_requires_admin_login(self):
        """Test that events endpoint requires admin authentication."""
        # Test without login - should redirect to login page
        response = self.client.get('/admin/bookings/booking/calendar/events/')
        self.assertEqual(
            response.status_code, 302,
            msg="❌ Events endpoint should redirect unauthenticated users."
        )

    # -------------------------------------------------------------------------
    # PAGE LOADING & FRONTEND INTEGRATION TESTS
    # -------------------------------------------------------------------------
    # Test that the admin calendar page loads with FullCalendar components

    def test_calendar_page_loads_with_fullcalendar_elements(self):
        """Test that calendar page loads and contains FullCalendar elements."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get('/admin/bookings/booking/calendar/')

        self.assertEqual(
            response.status_code, 200,
            msg="❌ Calendar page did not load successfully."
        )
        self.assertIn(b"Bookings Calendar", response.content,
            msg="❌ 'Bookings Calendar' title missing from calendar page.")
        self.assertIn(b'<div id="calendar"></div>', response.content,
            msg="❌ Calendar div element missing from page.")
        self.assertIn(b"fullcalendar@6.1.8", response.content,
            msg="❌ FullCalendar JavaScript library not loaded.")

    # -------------------------------------------------------------------------
    # JSON API ENDPOINT TESTS
    # -------------------------------------------------------------------------
    # Test the backend API that provides booking data to FullCalendar

    def test_calendar_events_endpoint_returns_valid_json(self):
        """Test that events endpoint returns valid JSON data."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get('/admin/bookings/booking/calendar/events/')

        self.assertEqual(
            response.status_code, 200,
            msg="❌ Events endpoint did not return HTTP 200."
        )
        self.assertEqual(
            response['Content-Type'], 'application/json',
            msg="❌ Events endpoint should return JSON content type."
        )

        # Test that response is valid JSON
        try:
            events_data = json.loads(response.content)
            self.assertIsInstance(events_data, list,
                msg="❌ Events endpoint should return a JSON array.")
        except json.JSONDecodeError:
            self.fail("❌ Events endpoint did not return valid JSON.")

    def test_calendar_events_include_booking_data(self):
        """Test that calendar events include correct booking information."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get('/admin/bookings/booking/calendar/events/')
        events_data = json.loads(response.content)

        # Should have 2 events (confirmed + pending booking)
        self.assertEqual(
            len(events_data), 2,
            msg="❌ Events endpoint should return all bookings (2 expected)."
        )

        # Check confirmed booking data
        confirmed_event = next((e for e in events_data if 'John Doe' in e['title']), None)
        self.assertIsNotNone(confirmed_event,
            msg="❌ Confirmed booking (John Doe) not found in events data.")

        with self.subTest("✅ Confirmed booking has correct properties"):
            self.assertIn('title', confirmed_event)
            self.assertIn('start', confirmed_event)
            self.assertIn('end', confirmed_event)
            self.assertIn('color', confirmed_event)
            self.assertIn('Tesla Model S', confirmed_event['title'])
            self.assertEqual(confirmed_event['color'], '#378006')  # green for confirmed

        # Check pending booking data
        pending_event = next((e for e in events_data if 'Jane Smith' in e['title']), None)
        self.assertIsNotNone(pending_event,
            msg="❌ Pending booking (Jane Smith) not found in events data.")

        with self.subTest("✅ Pending booking has correct properties"):
            self.assertEqual(pending_event['color'], '#FFA500')  # orange for pending
            self.assertIn('Pending', pending_event['title'])

    # -------------------------------------------------------------------------
    # DATETIME FORMAT & VALIDATION TESTS
    # -------------------------------------------------------------------------
    # Test that booking times are properly formatted for FullCalendar

    def test_calendar_events_datetime_format(self):
        """Test that events use proper ISO datetime format for FullCalendar."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get('/admin/bookings/booking/calendar/events/')
        events_data = json.loads(response.content)

        for event in events_data:
            with self.subTest(f"✅ Event datetime format for {event['title']}"):
                # Check ISO format (should contain 'T' and end times)
                self.assertIn('T', event['start'],
                    msg=f"❌ Event start time not in ISO format: {event['start']}")
                self.assertIn('T', event['end'],
                    msg=f"❌ Event end time not in ISO format: {event['end']}")

                # Verify start is before end
                start_time = event['start']
                end_time = event['end']
                self.assertLess(start_time, end_time,
                    msg=f"❌ Event start time should be before end time.")

    # -------------------------------------------------------------------------
    # BOOKING STATUS & COLOR CODING TESTS
    # -------------------------------------------------------------------------
    # Test that different booking statuses are displayed with appropriate colors

    def test_calendar_events_handle_different_booking_statuses(self):
        """Test that different booking statuses get appropriate colors."""
        # Create bookings with all status types for comprehensive testing
        Booking.objects.create(
            vehicle=self.vehicle, guest_name="Test Rescheduled",
            guest_email="reschedule@test.com", requested_date=date(2025, 8, 17),
            requested_time=time(11, 0), status='rescheduled'
        )
        Booking.objects.create(
            vehicle=self.vehicle, guest_name="Test Canceled",
            guest_email="canceled@test.com", requested_date=date(2025, 8, 18),
            requested_time=time(15, 30), status='canceled'
        )
        Booking.objects.create(
            vehicle=self.vehicle, guest_name="Test Completed",
            guest_email="completed@test.com", requested_date=date(2025, 8, 19),
            requested_time=time(9, 0), status='completed'
        )

        self.client.login(username='admin', password='testpass123')
        response = self.client.get('/admin/bookings/booking/calendar/events/')
        events_data = json.loads(response.content)

        # Expected color mapping from admin.py status_color_map
        expected_colors = {
            'pending': '#FFA500',      # orange
            'confirmed': '#378006',    # green
            'rescheduled': '#1E90FF',  # dodger blue
            'canceled': '#FF0000',     # red
            'completed': '#6c757d'     # gray
        }

        # Verify each status has the correct color
        for status, expected_color in expected_colors.items():
            event = next((e for e in events_data if status.capitalize() in e['title']), None)
            self.assertIsNotNone(event,
                msg=f"❌ No event found for status '{status}'.")
            self.assertEqual(event['color'], expected_color,
                msg=f"❌ Wrong color for {status} status. Expected {expected_color}, got {event['color']}.")


# =============================================================================
# TEST EXECUTION NOTES
# =============================================================================
"""
To run these tests:

# Run all booking tests with verbose output
pytest bookings/tests.py -v

# Run only navigation tests
pytest bookings/tests.py::BookingNavigationTests -v

# Run only FullCalendar tests
pytest bookings/tests.py::FullCalendarTests -v

# Run a specific test method
pytest bookings/tests.py::FullCalendarTests::test_calendar_events_datetime_format -v

These tests verify:
✅ Basic navigation and page loading
✅ Admin authentication and access control
✅ FullCalendar backend integration
✅ JSON API endpoints and data formatting
✅ Booking status color coding
✅ DateTime format compatibility with FullCalendar.js

Note: These tests cover the Django backend. Frontend JavaScript functionality
would require additional tools like Selenium, Playwright, or Cypress.
"""
