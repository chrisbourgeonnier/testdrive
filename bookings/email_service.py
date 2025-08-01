"""
Enhanced email service with proper error handling.
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from typing import Dict, Any, Optional
import logging

# Set up logging for email operations
logger = logging.getLogger(__name__)

class EmailService:
    """Central service for handling all email operations with logging."""

    def __init__(self):
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@richmonds.com.au')
        self.staff_email = getattr(settings, 'STAFF_NOTIFICATION_EMAIL', 'bookings@richmonds.com.au')

    def _log_email(self, booking, email_type: str, recipient_email: str,
                   subject: str, success: bool, error_message: str = '') -> None:
        """
        Log email sending attempts to database for audit trail.

        Args:
            booking: Booking instance
            email_type: Type of email being sent
            recipient_email: Email recipient
            subject: Email subject
            success: Whether email was sent successfully
            error_message: Error message if sending failed
        """
        try:
            # Import here to avoid circular imports
            from .models import EmailLog

            EmailLog.objects.create(
                booking=booking,
                email_type=email_type,
                recipient_email=recipient_email,
                subject=subject,
                sent_successfully=success,
                error_message=error_message
            )
        except Exception as e:
            logger.error(f"Failed to log email: {str(e)}")

    def _send_html_email(self, subject: str, template_name: str, context: Dict[str, Any],
                        recipient_email: str, booking=None, email_type: str = '',
                        fail_silently: bool = False) -> bool:
        """
        Internal method to send HTML emails with logging.

        Args:
            subject: Email subject line
            template_name: Name of the HTML template (without .html extension)
            context: Dictionary of variables to pass to the template
            recipient_email: Email address to send to
            booking: Booking instance for logging
            email_type: Type of email for logging
            fail_silently: Whether to suppress email sending errors

        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        error_message = ''
        html_content = None
        text_content = None

        try:
            # Step 1: Render HTML template - this is where template errors would occur
            html_content = render_to_string(f'emails/{template_name}.html', context)

        except Exception as e:
            error_message = f"Template rendering failed: {str(e)}"
            logger.error(f"Template rendering error for {template_name}: {error_message}")

            # Log the error if we have booking info
            if booking and email_type:
                self._log_email(booking, email_type, recipient_email, subject, False, error_message)

            # Return False on template error
            if not fail_silently:
                raise
            return False

        try:
            # Step 2: Create plain text version
            text_content = strip_tags(html_content)

            # Step 3: Create multipart email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                to=[recipient_email]
            )
            email.attach_alternative(html_content, "text/html")

            # Step 4: Send the email
            result = email.send()

            if result:
                logger.info(f"Email sent successfully to {recipient_email}: {subject}")
                if booking and email_type:
                    self._log_email(booking, email_type, recipient_email, subject, True)
                return True
            else:
                error_message = "Email send returned 0 (failed to send)"
                logger.error(f"Failed to send email to {recipient_email}: {subject}")
                if booking and email_type:
                    self._log_email(booking, email_type, recipient_email, subject, False, error_message)
                return False

        except Exception as e:
            error_message = f"Email sending failed: {str(e)}"
            logger.error(f"Error sending email to {recipient_email}: {error_message}")

            # Log the error
            if booking and email_type:
                self._log_email(booking, email_type, recipient_email, subject, False, error_message)

            # Re-raise if not failing silently
            if not fail_silently:
                raise
            return False

    def send_booking_confirmation(self, booking, fail_silently: bool = True) -> bool:
        """Send initial booking confirmation email to customer."""
        # Determine customer details
        if booking.user:
            customer_name = booking.user.get_full_name() or booking.user.username
            customer_email = booking.user.email
            customer_phone = getattr(booking.user, 'phone', 'Not provided')
        else:
            customer_name = booking.guest_name
            customer_email = booking.guest_email
            customer_phone = booking.guest_phone

        context = {
            'booking': booking,
            'vehicle': booking.vehicle,
            'customer_name': customer_name,
            'customer_email': customer_email,
            'customer_phone': customer_phone,
        }

        subject = f"Test Drive Booking Confirmation - {booking.vehicle.year} {booking.vehicle.make} {booking.vehicle.model}"

        return self._send_html_email(
            subject=subject,
            template_name='booking_confirmation',
            context=context,
            recipient_email=customer_email,
            booking=booking,
            email_type='booking_confirmation',
            fail_silently=fail_silently
        )

    def send_booking_status_update(self, booking, fail_silently: bool = True) -> bool:
        """Send status update email when booking status changes."""
        # Determine customer details
        if booking.user:
            customer_name = booking.user.get_full_name() or booking.user.username
            customer_email = booking.user.email
        else:
            customer_name = booking.guest_name
            customer_email = booking.guest_email

        context = {
            'booking': booking,
            'vehicle': booking.vehicle,
            'customer_name': customer_name,
            'staff_notes': booking.staff_notes,
        }

        # Choose template based on status
        if booking.status == 'confirmed':
            template_name = 'booking_confirmed'
            email_type = 'booking_confirmed'
            subject = f"Test Drive Confirmed - {booking.vehicle.year} {booking.vehicle.make} {booking.vehicle.model}"
        elif booking.status == 'rescheduled':
            template_name = 'booking_rescheduled'
            email_type = 'booking_rescheduled'
            subject = f"Test Drive Rescheduled - {booking.vehicle.year} {booking.vehicle.make} {booking.vehicle.model}"
        elif booking.status == 'canceled':
            template_name = 'booking_canceled'
            email_type = 'booking_canceled'
            subject = f"Test Drive Canceled - {booking.vehicle.year} {booking.vehicle.make} {booking.vehicle.model}"
        else:
            logger.info(f"No email template for status '{booking.status}' - skipping email")
            return True

        return self._send_html_email(
            subject=subject,
            template_name=template_name,
            context=context,
            recipient_email=customer_email,
            booking=booking,
            email_type=email_type,
            fail_silently=fail_silently
        )

    def send_staff_notification(self, booking, fail_silently: bool = True) -> bool:
        """Send notification email to staff when new booking is created."""
        # Determine customer details
        if booking.user:
            customer_name = booking.user.get_full_name() or booking.user.username
            customer_email = booking.user.email
            customer_phone = getattr(booking.user, 'phone', 'Not provided')
        else:
            customer_name = booking.guest_name
            customer_email = booking.guest_email
            customer_phone = booking.guest_phone

        context = {
            'booking': booking,
            'vehicle': booking.vehicle,
            'customer_name': customer_name,
            'customer_email': customer_email,
            'customer_phone': customer_phone,
        }

        subject = f"New Test Drive Booking - {booking.vehicle.year} {booking.vehicle.make} {booking.vehicle.model}"

        return self._send_html_email(
            subject=subject,
            template_name='staff_notification',
            context=context,
            recipient_email=self.staff_email,
            booking=booking,
            email_type='staff_notification',
            fail_silently=fail_silently
        )

# Global instance
email_service = EmailService()
