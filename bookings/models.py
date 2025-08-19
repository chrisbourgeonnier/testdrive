from django.db import models
from django.conf import settings
from vehicles.models import Vehicle
from django.utils import timezone
from django.db.models import UniqueConstraint, Q
from django.contrib.contenttypes.models import ContentType


class Booking(models.Model):
    """
    Represents a test drive booking for a vehicle.

    Supports both authenticated users (via user field) and guest bookings
    (via guest_* fields). Includes validation constraints to prevent double
    bookings and ensure data integrity.

    Business Rules:
    - Users cannot have multiple bookings at same date/time
    - Vehicles cannot be double-booked for same time slot
    - Guest bookings are identified by email + name combination
    - Only active (non-canceled) bookings count for conflicts

    Status Flow: pending -> confirmed -> completed
                        -> rescheduled -> completed
                        -> canceled (terminal)
    """
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

    class Meta:
        """
        Database constraints and metadata for Booking model.

        Implements business rule constraints to prevent:
        - User double-booking (same user, date, time)
        - Guest double-booking (same name/email, date, time)
        - Vehicle conflicts (same vehicle, date, time)

        All constraints exclude canceled bookings to allow rebooking.
        """
        constraints = [
            # A user cannot have two reservations on the same day and time.
            models.UniqueConstraint(
                fields=['user', 'requested_date', 'requested_time'],
                condition=~Q(status='canceled'),
                name='uniq_user_timeslot_active',
            ),
            # A vehicle cannot be booked twice in the same slot.
            models.UniqueConstraint(
                fields=['guest_name', 'guest_email', 'requested_date', 'requested_time'],
                condition=~Q(status='canceled'),
                name='uniq_guest_timeslot_active',
            ),
            # A guest with the same email address and same date/time cannot have two reservations on the same day and time.
            models.UniqueConstraint(
                fields=['vehicle', 'requested_date', 'requested_time'],
                condition=~Q(status='canceled'),
                name='uniq_vehicle_timeslot_active',
            ),
        ]

    def __str__(self):
        return f"{self.vehicle} - {self.requested_date} {self.requested_time} [{self.status}]"


class EmailLog(models.Model):
    """
    Tracks email delivery attempts for audit and debugging purposes.

    Records all email sending attempts with success/failure status and
    error details. Helps monitor email delivery reliability and troubleshoot
    issues with customer communications.

    Email Types:
    - booking_confirmation: Initial booking received notification
    - booking_confirmed: Staff confirmed the booking
    - booking_rescheduled: Booking date/time changed
    - booking_canceled: Booking was canceled
    - staff_notification: New booking notification to staff
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
