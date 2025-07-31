from django.db import models
from django.conf import settings
from vehicles.models import Vehicle
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

# Booking model relating to Vehicle, and supporting both guest and user bookings.
class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('rescheduled', 'Rescheduled'),
        ('canceled', 'Canceled'),
        ('completed', 'Completed')
    ]

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        help_text="Null for guest bookings"
    )
    guest_name = models.CharField(max_length=100, blank=True)
    guest_email = models.EmailField(blank=True)
    guest_phone = models.CharField(max_length=20, blank=True)
    dob = models.DateField(default=timezone.now)
    requested_date = models.DateField()
    requested_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    staff_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.vehicle} - {self.requested_date} {self.requested_time} [{self.status}]"


class EmailLog(models.Model):
    """
    Model to track email delivery for auditing and debugging purposes.

    This helps us monitor email delivery success/failure and troubleshoot issues.
    """
    EMAIL_TYPE_CHOICES = [
        ('booking_confirmation', 'Booking Confirmation'),
        ('booking_confirmed', 'Booking Confirmed'),
        ('booking_rescheduled', 'Booking Rescheduled'),
        ('booking_canceled', 'Booking Canceled'),
        ('staff_notification', 'Staff Notification'),
    ]

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='email_logs')
    email_type = models.CharField(max_length=30, choices=EMAIL_TYPE_CHOICES)
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=200)
    sent_successfully = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        status = "✓" if self.sent_successfully else "✗"
        return f"{status} {self.email_type} to {self.recipient_email} [{self.sent_at.strftime('%Y-%m-%d %H:%M')}]"
