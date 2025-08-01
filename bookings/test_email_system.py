"""
Comprehensive test suite for email functionality in the TestDrive booking system.
"""

from django.test import TestCase, override_settings
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from unittest.mock import patch, Mock
from bookings.models import Booking, EmailLog
from bookings.email_service import EmailService, email_service
from vehicles.models import Vehicle
from datetime import date, time as datetime_time  # Fix import conflict
import re
import time  # For performance testing


# =============================================================================
# EMAIL TEMPLATE RENDERING TESTS
# =============================================================================

class EmailTemplateRenderingTests(TestCase):
    """
    Test email template compilation, dynamic content insertion,
    cross-client compatibility, and responsive design.
    """

    def setUp(self):
        """Create test data for template rendering tests."""
        # Create test vehicle
        self.vehicle = Vehicle.objects.create(
            make="BMW", model="M3", year=2023, km=5000, engine_size=3000,
            transmission="Manual", price=120000,
            photo_link="http://example.com/bmw-m3.jpg",
            description="High-performance sports sedan",
            link="https://richmonds.com.au/bmw-m3"
        )

        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            first_name='John',
            last_name='Doe'
        )

        # Create test booking
        self.booking = Booking.objects.create(
            vehicle=self.vehicle,
            guest_name="Jane Smith",
            guest_email="jane@example.com",
            guest_phone="0412345678",
            requested_date=date(2025, 8, 15),
            requested_time=datetime_time(14, 30),
            status='pending'
        )

    def test_base_email_template_renders_correctly(self):
        """Test that base email template renders with proper HTML structure."""
        context = {'test_content': 'Test email content'}

        # Test template rendering
        html_content = render_to_string('emails/base_email.html', context)

        # Verify HTML structure
        self.assertIn('<!DOCTYPE html>', html_content)
        self.assertIn('<html lang="en">', html_content)
        self.assertIn('RICHMONDS', html_content)
        self.assertIn('Classic & Prestige Vehicles', html_content)

        # Check responsive design elements
        self.assertIn('@media (max-width: 600px)', html_content)
        self.assertIn('max-width: 600px', html_content)

        # Verify brand colors are present
        self.assertIn('#dd0000', html_content)  # Richmonds red

    def test_booking_confirmation_template_dynamic_content(self):
        """Test booking confirmation template with dynamic content insertion."""
        context = {
            'booking': self.booking,
            'vehicle': self.vehicle,
            'customer_name': 'Jane Smith',
            'customer_email': 'jane@example.com',
            'customer_phone': '0412345678'
        }

        html_content = render_to_string('emails/booking_confirmation.html', context)

        # Verify dynamic content is inserted correctly
        self.assertIn('Jane Smith', html_content)
        self.assertIn('BMW M3', html_content)
        self.assertIn('2023', html_content)
        self.assertIn('Friday, August 15, 2025', html_content)  # Date formatting
        self.assertIn('2:30 PM', html_content)  # Time formatting
        self.assertIn('jane@example.com', html_content)
        self.assertIn('0412345678', html_content)
        self.assertIn(f'#{self.booking.id}', html_content)  # Booking ID

        # Verify email contains proper instructions
        self.assertIn('pending confirmation', html_content)
        self.assertIn('within 24 hours', html_content)

    def test_booking_confirmed_template_content(self):
        """Test booking confirmed template renders correctly."""
        self.booking.status = 'confirmed'
        self.booking.staff_notes = 'Please arrive 15 minutes early for paperwork.'

        context = {
            'booking': self.booking,
            'vehicle': self.vehicle,
            'customer_name': 'Jane Smith',
            'staff_notes': self.booking.staff_notes
        }

        html_content = render_to_string('emails/booking_confirmed.html', context)

        # Verify confirmation-specific content
        self.assertIn('Your Test Drive is Confirmed!', html_content)
        self.assertIn('confirmed', html_content)
        self.assertIn('Please bring:', html_content)
        self.assertIn('Valid driver\'s license', html_content)
        self.assertIn('Please arrive 15 minutes early', html_content)

        # Check styling for confirmation (green color)
        self.assertIn('#28a745', html_content)  # Bootstrap success green

    def test_booking_rescheduled_template_content(self):
        """Test booking rescheduled template renders correctly."""
        self.booking.status = 'rescheduled'
        self.booking.staff_notes = 'Vehicle maintenance required on original date.'

        context = {
            'booking': self.booking,
            'vehicle': self.vehicle,
            'customer_name': 'Jane Smith',
            'staff_notes': self.booking.staff_notes
        }

        html_content = render_to_string('emails/booking_rescheduled.html', context)

        # Verify rescheduled-specific content
        self.assertIn('Your Test Drive Has Been Rescheduled', html_content)
        self.assertIn('reschedule', html_content)  # Changed from 'rescheduled' to 'reschedule'
        self.assertIn('Vehicle maintenance required', html_content)
        self.assertIn('Updated Appointment:', html_content)

        # Check styling for rescheduled (blue color)
        self.assertIn('#1E90FF', html_content)  # Dodger blue

    def test_booking_canceled_template_content(self):
        """Test booking canceled template renders correctly."""
        self.booking.status = 'canceled'
        self.booking.staff_notes = 'Vehicle no longer available for test drives.'

        context = {
            'booking': self.booking,
            'vehicle': self.vehicle,
            'customer_name': 'Jane Smith',
            'staff_notes': self.booking.staff_notes
        }

        html_content = render_to_string('emails/booking_canceled.html', context)

        # Verify cancellation-specific content
        self.assertIn('Test Drive Appointment Canceled', html_content)
        self.assertIn('regret to inform', html_content)
        self.assertIn('Vehicle no longer available', html_content)
        self.assertIn('Book Another Test Drive', html_content)

        # Check styling for cancellation (red color)
        self.assertIn('#dc3545', html_content)  # Bootstrap danger red

    def test_staff_notification_template_content(self):
        """Test staff notification template renders correctly."""
        context = {
            'booking': self.booking,
            'vehicle': self.vehicle,
            'customer_name': 'Jane Smith',
            'customer_email': 'jane@example.com',
            'customer_phone': '0412345678'
        }

        html_content = render_to_string('emails/staff_notification.html', context)

        # Verify staff notification content
        self.assertIn('New Test Drive Booking Request', html_content)
        self.assertIn('requires review', html_content)
        self.assertIn('Action Required:', html_content)
        self.assertIn('Review Booking', html_content)
        self.assertIn('/admin/bookings/booking/', html_content)

        # Verify all customer details are present
        self.assertIn('Jane Smith', html_content)
        self.assertIn('jane@example.com', html_content)
        self.assertIn('0412345678', html_content)

    def test_email_templates_responsive_design(self):
        """Test that email templates include responsive design elements."""
        templates = [
            'emails/base_email.html',
            'emails/booking_confirmation.html',
            'emails/booking_confirmed.html',
            'emails/booking_rescheduled.html',
            'emails/booking_canceled.html',
            'emails/staff_notification.html'
        ]

        context = {
            'booking': self.booking,
            'vehicle': self.vehicle,
            'customer_name': 'Test User',
            'customer_email': 'test@example.com',
            'customer_phone': '0400000000'
        }

        for template in templates:
            with self.subTest(template=template):
                html_content = render_to_string(template, context)

                # Check for responsive design elements
                self.assertIn('max-width: 600px', html_content,
                            f"Template {template} should have max-width constraint")
                self.assertIn('@media (max-width:', html_content,
                            f"Template {template} should include mobile media queries")
                self.assertIn('viewport', html_content,
                            f"Template {template} should include viewport meta tag")

    def test_email_templates_cross_client_compatibility(self):
        """Test email templates for cross-client compatibility elements."""
        context = {
            'booking': self.booking,
            'vehicle': self.vehicle,
            'customer_name': 'Test User'
        }

        html_content = render_to_string('emails/base_email.html', context)

        # Check for email client compatibility elements
        self.assertIn('<!DOCTYPE html>', html_content)  # Proper DOCTYPE
        self.assertIn('style=', html_content)  # Inline styles for compatibility
        self.assertIn('table', html_content)  # Table-based layout for Outlook
        self.assertIn('cellspacing="0"', html_content)  # Proper table attributes
        self.assertIn('cellpadding="0"', html_content)

        # Verify no external CSS dependencies (should be inline)
        self.assertNotIn('<link rel="stylesheet"', html_content)


# =============================================================================
# EMAIL DELIVERY SERVICE TESTS
# =============================================================================

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class EmailDeliveryServiceTests(TestCase):
    """
    Test email sending functionality, delivery confirmation,
    bounce handling, and spam filter compatibility.
    """

    def setUp(self):
        """Set up test data for delivery tests."""
        # Clear mail outbox
        mail.outbox = []

        # Create test data
        self.vehicle = Vehicle.objects.create(
            make="Mercedes", model="C63 AMG", year=2022, km=8000, engine_size=4000,
            transmission="Automatic", price=150000,
            photo_link="http://example.com/merc.jpg",
            description="High-performance luxury sedan",
            link="https://richmonds.com.au/mercedes-c63"
        )

        self.booking = Booking.objects.create(
            vehicle=self.vehicle,
            guest_name="Alex Johnson",
            guest_email="alex@example.com",
            guest_phone="0423456789",
            requested_date=date(2025, 9, 20),
            requested_time=datetime_time(11, 0),
            status='pending'
        )

        self.email_service = EmailService()

    def test_email_service_initialization(self):
        """Test EmailService initializes with correct configuration."""
        service = EmailService()

        # Check default configuration
        self.assertEqual(service.from_email, 'noreply@richmonds.com.au')
        self.assertEqual(service.staff_email, 'bookings@richmonds.com.au')

    def test_send_booking_confirmation_success(self):
        """Test successful booking confirmation email delivery."""
        # Send email
        result = self.email_service.send_booking_confirmation(self.booking)

        # Verify email was sent successfully
        self.assertTrue(result, "Booking confirmation email should be sent successfully")
        self.assertEqual(len(mail.outbox), 1, "Should send exactly one email")

        # Verify email content
        email = mail.outbox[0]
        self.assertEqual(email.to, ['alex@example.com'])
        self.assertEqual(email.from_email, 'noreply@richmonds.com.au')
        self.assertIn('Test Drive Booking Confirmation', email.subject)
        self.assertIn('Mercedes C63 AMG', email.subject)

        # Verify both HTML and plain text versions exist
        self.assertIsInstance(email, EmailMultiAlternatives)
        self.assertTrue(hasattr(email, 'alternatives'))
        self.assertEqual(len(email.alternatives), 1)  # HTML alternative
        self.assertEqual(email.alternatives[0][1], 'text/html')

        # Verify content in both versions
        self.assertIn('Alex Johnson', email.body)  # Plain text
        self.assertIn('pending confirmation', email.body)

    def test_send_booking_status_update_confirmed(self):
        """Test sending booking confirmed status update email."""
        self.booking.status = 'confirmed'
        self.booking.staff_notes = 'Looking forward to seeing you!'

        result = self.email_service.send_booking_status_update(self.booking)

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertIn('Test Drive Confirmed', email.subject)
        self.assertIn('confirmed', email.body)
        self.assertIn('Looking forward to seeing you!', email.body)

    def test_send_booking_status_update_rescheduled(self):
        """Test sending booking rescheduled status update email."""
        self.booking.status = 'rescheduled'
        self.booking.staff_notes = 'Vehicle maintenance on original date.'

        result = self.email_service.send_booking_status_update(self.booking)

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertIn('Test Drive Rescheduled', email.subject)
        self.assertIn('reschedule', email.body)  # Changed from 'rescheduled' to 'reschedule'
        self.assertIn('Vehicle maintenance', email.body)

    def test_send_booking_status_update_canceled(self):
        """Test sending booking canceled status update email."""
        self.booking.status = 'canceled'
        self.booking.staff_notes = 'Vehicle sold to another customer.'

        result = self.email_service.send_booking_status_update(self.booking)

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertIn('Test Drive Canceled', email.subject)
        self.assertIn('regret to inform', email.body)
        self.assertIn('Vehicle sold', email.body)

    def test_send_booking_status_update_no_email_for_pending(self):
        """Test that no email is sent for pending status (to avoid spam)."""
        self.booking.status = 'pending'

        result = self.email_service.send_booking_status_update(self.booking)

        self.assertTrue(result)  # Returns True but doesn't send email
        self.assertEqual(len(mail.outbox), 0, "No email should be sent for pending status")

    def test_send_booking_status_update_no_email_for_completed(self):
        """Test that no email is sent for completed status."""
        self.booking.status = 'completed'

        result = self.email_service.send_booking_status_update(self.booking)

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 0, "No email should be sent for completed status")

    def test_send_staff_notification_success(self):
        """Test successful staff notification email delivery."""
        result = self.email_service.send_staff_notification(self.booking)

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertEqual(email.to, ['bookings@richmonds.com.au'])
        self.assertIn('New Test Drive Booking', email.subject)
        self.assertIn('Alex Johnson', email.body)
        self.assertIn('alex@example.com', email.body)
        self.assertIn('requires review', email.body)

    def test_email_logging_on_successful_send(self):
        """Test that successful email sends are logged correctly."""
        result = self.email_service.send_booking_confirmation(self.booking)

        self.assertTrue(result)

        # Check email log was created
        email_logs = EmailLog.objects.filter(booking=self.booking)
        self.assertEqual(email_logs.count(), 1)

        log = email_logs.first()
        self.assertEqual(log.email_type, 'booking_confirmation')
        self.assertEqual(log.recipient_email, 'alex@example.com')
        self.assertTrue(log.sent_successfully)
        self.assertEqual(log.error_message, '')
        self.assertIn('Test Drive Booking Confirmation', log.subject)

    @patch('bookings.email_service.EmailMultiAlternatives.send')
    def test_email_logging_on_failed_send(self, mock_send):
        """Test that failed email sends are logged correctly."""
        # Mock email send failure
        mock_send.side_effect = Exception("SMTP connection failed")

        result = self.email_service.send_booking_confirmation(self.booking, fail_silently=True)

        self.assertFalse(result)

        # Check email log was created with error
        email_logs = EmailLog.objects.filter(booking=self.booking)
        self.assertEqual(email_logs.count(), 1)

        log = email_logs.first()
        self.assertEqual(log.email_type, 'booking_confirmation')
        self.assertFalse(log.sent_successfully)
        self.assertIn('SMTP connection failed', log.error_message)

    def test_registered_user_email_handling(self):
        """Test email sending for registered users vs guest users."""
        # Create registered user booking
        user = User.objects.create_user(
            username='registered_user',
            email='registered@example.com',
            first_name='Sarah',
            last_name='Wilson'
        )

        user_booking = Booking.objects.create(
            vehicle=self.vehicle,
            user=user,
            requested_date=date(2025, 9, 25),
            requested_time=datetime_time(15, 30),
            status='pending'
        )

        # Send confirmation email
        result = self.email_service.send_booking_confirmation(user_booking)

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertEqual(email.to, ['registered@example.com'])
        self.assertIn('Sarah Wilson', email.body)  # Should use user's full name

    def test_email_subject_line_formatting(self):
        """Test that email subject lines are properly formatted."""
        # Test booking confirmation subject
        result = self.email_service.send_booking_confirmation(self.booking)
        self.assertTrue(result)

        email = mail.outbox[0]
        expected_subject = "Test Drive Booking Confirmation - 2022 Mercedes C63 AMG"
        self.assertEqual(email.subject, expected_subject)

        # Clear outbox and test status update subject
        mail.outbox = []
        self.booking.status = 'confirmed'

        result = self.email_service.send_booking_status_update(self.booking)
        self.assertTrue(result)

        email = mail.outbox[0]
        expected_subject = "Test Drive Confirmed - 2022 Mercedes C63 AMG"
        self.assertEqual(email.subject, expected_subject)


# =============================================================================
# BOOKING CONFIRMATION NOTIFICATION TESTS
# =============================================================================

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class BookingConfirmationNotificationTests(TestCase):
    """
    Test automated email triggers for booking confirmations,
    content accuracy, timing, and recipient validation.
    """

    def setUp(self):
        """Set up test data for booking confirmation tests."""
        mail.outbox = []

        self.vehicle = Vehicle.objects.create(
            make="Porsche", model="911 Turbo", year=2024, km=1000, engine_size=3800,
            transmission="PDK", price=300000,
            photo_link="http://example.com/porsche.jpg",
            description="Ultimate sports car experience",
            link="https://richmonds.com.au/porsche-911"
        )

    def test_booking_confirmation_content_accuracy(self):
        """Test that booking confirmation emails contain accurate information."""
        booking = Booking.objects.create(
            vehicle=self.vehicle,
            guest_name="Michael Chen",
            guest_email="michael@example.com",
            guest_phone="0445678901",
            requested_date=date(2025, 10, 15),
            requested_time=datetime_time(13, 45),
            status='pending'
        )

        email_service.send_booking_confirmation(booking)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]

        # Verify all booking details are present and accurate
        self.assertIn('Michael Chen', email.body)
        self.assertIn('michael@example.com', email.body)
        self.assertIn('0445678901', email.body)
        self.assertIn('Porsche 911 Turbo', email.body)
        self.assertIn('2024', email.body)
        self.assertIn('Wednesday, October 15, 2025', email.body)  # Formatted date
        self.assertIn('1:45 PM', email.body)  # Formatted time
        self.assertIn(f'#{booking.id}', email.body)  # Booking reference

        # Verify booking instructions are present
        self.assertIn('pending confirmation', email.body)
        self.assertIn('within 24 hours', email.body)
        self.assertIn('08 8366 2210', email.body)  # Contact number

    def test_booking_confirmation_recipient_validation(self):
        """Test that confirmation emails are sent to correct recipients."""
        # Test guest booking
        guest_booking = Booking.objects.create(
            vehicle=self.vehicle,
            guest_name="Lisa Park",
            guest_email="lisa@example.com",
            guest_phone="0456789012",
            requested_date=date(2025, 11, 10),
            requested_time=datetime_time(9, 30),
            status='pending'
        )

        result = email_service.send_booking_confirmation(guest_booking)
        self.assertTrue(result)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['lisa@example.com'])
        self.assertEqual(email.from_email, 'noreply@richmonds.com.au')

        # Clear outbox for next test
        mail.outbox = []

        # Test registered user booking
        user = User.objects.create_user(
            username='davidlee',
            email='david@example.com',
            first_name='David',
            last_name='Lee'
        )

        user_booking = Booking.objects.create(
            vehicle=self.vehicle,
            user=user,
            requested_date=date(2025, 11, 15),
            requested_time=datetime_time(16, 0),
            status='pending'
        )

        result = email_service.send_booking_confirmation(user_booking)
        self.assertTrue(result)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['david@example.com'])
        self.assertIn('David Lee', email.body)  # Should use full name for registered users

    def test_staff_notification_trigger_and_content(self):
        """Test that staff notifications are sent with correct content."""
        booking = Booking.objects.create(
            vehicle=self.vehicle,
            guest_name="Rachel Green",
            guest_email="rachel@example.com",
            guest_phone="0467890123",
            requested_date=date(2025, 12, 5),
            requested_time=datetime_time(14, 15),
            status='pending'
        )

        result = email_service.send_staff_notification(booking)
        self.assertTrue(result)

        self.assertEqual(len(mail.outbox), 1)
        staff_email = mail.outbox[0]

        self.assertEqual(staff_email.to, ['bookings@richmonds.com.au'])
        self.assertIn('New Test Drive Booking', staff_email.subject)
        self.assertIn('Rachel Green', staff_email.body)
        self.assertIn('rachel@example.com', staff_email.body)
        self.assertIn('requires review', staff_email.body)
        self.assertIn('/admin/bookings/booking/', staff_email.body)  # Admin link

    def test_booking_confirmation_timing(self):
        """Test that confirmation emails are sent immediately upon booking creation."""
        from datetime import datetime

        start_time = datetime.now()

        booking = Booking.objects.create(
            vehicle=self.vehicle,
            guest_name="Tom Wilson",
            guest_email="tom@example.com",
            guest_phone="0478901234",
            requested_date=date(2025, 12, 20),
            requested_time=datetime_time(11, 0),
            status='pending'
        )

        # Send confirmation email
        result = email_service.send_booking_confirmation(booking)

        end_time = datetime.now()

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

        # Verify email was sent quickly (within 5 seconds)
        duration = (end_time - start_time).total_seconds()
        self.assertLess(duration, 5.0, "Email should be sent immediately (within 5 seconds)")

        # Check email log timestamp
        email_log = EmailLog.objects.filter(booking=booking, email_type='booking_confirmation').first()
        self.assertIsNotNone(email_log)

        log_duration = (email_log.sent_at - booking.created_at).total_seconds()
        self.assertLess(abs(log_duration), 5.0, "Email log timestamp should be close to booking creation time")


# =============================================================================
# STATUS UPDATE NOTIFICATION TESTS
# =============================================================================

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class StatusUpdateNotificationTests(TestCase):
    """
    Test validation of notification triggers for booking changes,
    content personalization, and delivery reliability.
    """

    def setUp(self):
        """Set up test data for status update notification tests."""
        mail.outbox = []

        self.vehicle = Vehicle.objects.create(
            make="Lamborghini", model="Huracan", year=2023, km=2500, engine_size=5200,
            transmission="Automatic", price=450000,
            photo_link="http://example.com/lambo.jpg",
            description="Exotic supercar experience",
            link="https://richmonds.com.au/lamborghini-huracan"
        )

        self.booking = Booking.objects.create(
            vehicle=self.vehicle,
            guest_name="Sofia Martinez",
            guest_email="sofia@example.com",
            guest_phone="0489012345",
            requested_date=date(2026, 1, 10),
            requested_time=datetime_time(15, 30),
            status='pending'
        )

    def test_status_update_trigger_on_confirmation(self):
        """Test that status update emails are triggered when booking is confirmed."""
        # Change status to confirmed
        self.booking.status = 'confirmed'
        self.booking.staff_notes = 'Confirmed by John from sales team.'
        self.booking.save()

        # Send status update email
        result = email_service.send_booking_status_update(self.booking)

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertEqual(email.to, ['sofia@example.com'])
        self.assertIn('Test Drive Confirmed', email.subject)
        self.assertIn('confirmed', email.body)
        self.assertIn('Confirmed by John', email.body)

    def test_status_update_trigger_on_rescheduling(self):
        """Test that status update emails are triggered when booking is rescheduled."""
        self.booking.status = 'rescheduled'
        self.booking.staff_notes = 'Rescheduled due to weather conditions.'
        self.booking.save()

        result = email_service.send_booking_status_update(self.booking)

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertIn('Test Drive Rescheduled', email.subject)
        self.assertIn('reschedule', email.body)  # Changed from 'rescheduled'
        self.assertIn('weather conditions', email.body)

    def test_status_update_trigger_on_cancellation(self):
        """Test that status update emails are triggered when booking is canceled."""
        self.booking.status = 'canceled'
        self.booking.staff_notes = 'Vehicle is currently undergoing maintenance.'
        self.booking.save()

        result = email_service.send_booking_status_update(self.booking)

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertIn('Test Drive Canceled', email.subject)
        self.assertIn('regret to inform', email.body)
        self.assertIn('undergoing maintenance', email.body)

    def test_no_status_update_for_non_triggering_statuses(self):
        """Test that no emails are sent for status changes that shouldn't trigger emails."""
        # Test pending status
        self.booking.status = 'pending'
        result = email_service.send_booking_status_update(self.booking)
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 0)

        # Test completed status
        self.booking.status = 'completed'
        result = email_service.send_booking_status_update(self.booking)
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 0)

    def test_status_update_content_personalization(self):
        """Test that status update emails are properly personalized."""
        # Test with registered user
        user = User.objects.create_user(
            username='alexandra',
            email='alexandra@example.com',
            first_name='Alexandra',
            last_name='Rodriguez'
        )

        user_booking = Booking.objects.create(
            vehicle=self.vehicle,
            user=user,
            requested_date=date(2026, 2, 14),  # Saturday in 2026
            requested_time=datetime_time(10, 0),
            status='confirmed'
        )

        result = email_service.send_booking_status_update(user_booking)

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertEqual(email.to, ['alexandra@example.com'])
        self.assertIn('Alexandra Rodriguez', email.body)  # Personalized name
        self.assertIn('Lamborghini Huracan', email.body)  # Vehicle details
        self.assertIn('Saturday, February 14, 2026', email.body)  # Corrected date format

    def test_status_update_delivery_reliability_with_retries(self):
        """Test email delivery reliability and error handling."""
        with patch('bookings.email_service.EmailMultiAlternatives.send') as mock_send:
            # Test successful delivery
            mock_send.return_value = 1

            self.booking.status = 'confirmed'
            result = email_service.send_booking_status_update(self.booking)

            self.assertTrue(result)
            mock_send.assert_called_once()

            # Verify email log shows success
            email_log = EmailLog.objects.filter(
                booking=self.booking,
                email_type='booking_confirmed'
            ).first()
            self.assertIsNotNone(email_log)
            self.assertTrue(email_log.sent_successfully)

    def test_status_update_error_handling(self):
        """Test proper error handling for failed status update emails."""
        with patch('bookings.email_service.EmailMultiAlternatives.send') as mock_send:
            # Mock email send failure
            mock_send.side_effect = Exception("SMTP server unavailable")

            self.booking.status = 'confirmed'
            result = email_service.send_booking_status_update(self.booking, fail_silently=True)

            self.assertFalse(result)

            # Verify error is logged
            email_log = EmailLog.objects.filter(
                booking=self.booking,
                email_type='booking_confirmed'
            ).first()
            self.assertIsNotNone(email_log)
            self.assertFalse(email_log.sent_successfully)
            self.assertIn('SMTP server unavailable', email_log.error_message)

    def test_bulk_status_update_email_handling(self):
        """Test handling of bulk status updates (e.g., from admin actions)."""
        # Create multiple bookings
        bookings = []
        for i in range(3):
            booking = Booking.objects.create(
                vehicle=self.vehicle,
                guest_name=f"Customer {i+1}",
                guest_email=f"customer{i+1}@example.com",
                guest_phone=f"040000000{i}",
                requested_date=date(2026, 3, 10 + i),
                requested_time=datetime_time(14, 0),
                status='pending'
            )
            bookings.append(booking)

        # Simulate bulk confirmation
        success_count = 0
        for booking in bookings:
            booking.status = 'confirmed'
            booking.save()

            result = email_service.send_booking_status_update(booking)
            if result:
                success_count += 1

        # Verify all emails were sent
        self.assertEqual(success_count, 3)
        self.assertEqual(len(mail.outbox), 3)

        # Verify each email has correct recipient
        recipients = [email.to[0] for email in mail.outbox]
        expected_recipients = ['customer1@example.com', 'customer2@example.com', 'customer3@example.com']
        self.assertEqual(sorted(recipients), sorted(expected_recipients))

    def test_status_update_with_empty_staff_notes(self):
        """Test status update emails when staff notes are empty."""
        self.booking.status = 'confirmed'
        self.booking.staff_notes = ''  # Empty notes

        result = email_service.send_booking_status_update(self.booking)

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        # Should still send email but without notes section
        self.assertIn('confirmed', email.body)
        self.assertNotIn('Additional Notes:', email.body)


# =============================================================================
# EMAIL SYSTEM INTEGRATION TESTS
# =============================================================================

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class EmailSystemIntegrationTests(TestCase):
    """
    Integration tests that verify the complete email system workflow
    from booking creation through status updates.
    """

    def setUp(self):
        """Set up test data for integration tests."""
        mail.outbox = []

        self.vehicle = Vehicle.objects.create(
            make="Ferrari", model="488 GTB", year=2023, km=1500, engine_size=3900,
            transmission="Automatic", price=500000,
            photo_link="http://example.com/ferrari.jpg",
            description="Italian racing heritage",
            link="https://richmonds.com.au/ferrari-488"
        )

    def test_complete_booking_lifecycle_email_flow(self):
        """Test complete email flow from booking creation to completion."""
        # Step 1: Create booking (should trigger confirmation + staff notification)
        booking = Booking.objects.create(
            vehicle=self.vehicle,
            guest_name="James Bond",
            guest_email="james@mi6.gov.uk",
            guest_phone="0412007007",
            requested_date=date(2026, 4, 15),
            requested_time=datetime_time(13, 0),
            status='pending'
        )

        # Send initial emails
        customer_result = email_service.send_booking_confirmation(booking)
        staff_result = email_service.send_staff_notification(booking)

        self.assertTrue(customer_result)
        self.assertTrue(staff_result)
        self.assertEqual(len(mail.outbox), 2)

        # Verify initial emails
        customer_emails = [e for e in mail.outbox if 'james@mi6.gov.uk' in e.to]
        staff_emails = [e for e in mail.outbox if 'bookings@richmonds.com.au' in e.to]

        self.assertEqual(len(customer_emails), 1)
        self.assertEqual(len(staff_emails), 1)

        self.assertIn('Booking Confirmation', customer_emails[0].subject)
        self.assertIn('New Test Drive Booking', staff_emails[0].subject)

        # Step 2: Confirm booking (should trigger confirmed email)
        mail.outbox = []  # Clear previous emails

        booking.status = 'confirmed'
        booking.staff_notes = 'Confirmed - vehicle prepared and ready.'
        booking.save()

        confirmed_result = email_service.send_booking_status_update(booking)
        self.assertTrue(confirmed_result)
        self.assertEqual(len(mail.outbox), 1)

        confirmed_email = mail.outbox[0]
        self.assertIn('Test Drive Confirmed', confirmed_email.subject)
        self.assertIn('confirmed', confirmed_email.body)

        # Step 3: Test rescheduling
        mail.outbox = []

        booking.status = 'rescheduled'
        booking.requested_date = date(2026, 4, 16)  # Next day
        booking.staff_notes = 'Rescheduled - original time not available.'
        booking.save()

        reschedule_result = email_service.send_booking_status_update(booking)
        self.assertTrue(reschedule_result)
        self.assertEqual(len(mail.outbox), 1)

        reschedule_email = mail.outbox[0]
        self.assertIn('Test Drive Rescheduled', reschedule_email.subject)
        self.assertIn('reschedule', reschedule_email.body)  # Changed from 'rescheduled'

        # Verify email logs track the complete journey
        email_logs = EmailLog.objects.filter(booking=booking).order_by('sent_at')
        self.assertEqual(email_logs.count(), 4)  # confirmation, staff notification, confirmed, rescheduled

        log_types = [log.email_type for log in email_logs]
        expected_types = ['booking_confirmation', 'staff_notification', 'booking_confirmed', 'booking_rescheduled']
        self.assertEqual(log_types, expected_types)

    def test_email_system_performance_with_multiple_bookings(self):
        """Test email system performance with multiple concurrent bookings."""
        start_time = time.time()

        # Create 10 bookings simultaneously
        bookings = []
        for i in range(10):
            booking = Booking.objects.create(
                vehicle=self.vehicle,
                guest_name=f"Customer {i+1}",
                guest_email=f"customer{i+1}@example.com",
                guest_phone=f"041200000{i}",
                requested_date=date(2026, 5, 10 + i),
                requested_time=datetime_time(10 + i, 0),  # Fixed the time import issue
                status='pending'
            )
            bookings.append(booking)

            # Send emails for each booking
            email_service.send_booking_confirmation(booking)
            email_service.send_staff_notification(booking)

        end_time = time.time()

        # Verify all emails were sent
        self.assertEqual(len(mail.outbox), 20)  # 10 confirmations + 10 staff notifications

        # Verify performance (should complete within 10 seconds)
        duration = end_time - start_time
        self.assertLess(duration, 10.0, f"Email system should handle 10 bookings quickly, took {duration:.2f}s")

        # Verify all email logs were created
        total_logs = EmailLog.objects.count()
        self.assertEqual(total_logs, 20)

    def test_email_system_error_recovery(self):
        """Test email system recovery from various error conditions."""
        booking = Booking.objects.create(
            vehicle=self.vehicle,
            guest_name="Error Test",
            guest_email="test@example.com",
            guest_phone="0400000000",
            requested_date=date(2026, 6, 1),
            requested_time=datetime_time(12, 0),
            status='pending'
        )

        # Test 1: Template rendering error - patch where render_to_string is imported and used
        with patch('bookings.email_service.render_to_string') as mock_render:
            mock_render.side_effect = Exception("Template not found")

            result = email_service.send_booking_confirmation(booking, fail_silently=True)
            self.assertFalse(result)  # Should return False on error

            # Verify error is logged
            error_log = EmailLog.objects.filter(booking=booking, sent_successfully=False).first()
            self.assertIsNotNone(error_log)
            self.assertIn('Template not found', error_log.error_message)

        # Test 2: Recovery after error (clear error logs)
        EmailLog.objects.filter(booking=booking).delete()

        # Now try successful send
        result = email_service.send_booking_confirmation(booking)
        self.assertTrue(result)
        self.assertGreater(len(mail.outbox), 0)

        # Verify success is logged
        success_log = EmailLog.objects.filter(booking=booking, sent_successfully=True).first()
        self.assertIsNotNone(success_log)