from django.urls import path, reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.contrib import admin
from .models import Booking, EmailLog
from .models import Booking
from django.utils.dateformat import format
from .email_service import email_service
import datetime
import logging

logger = logging.getLogger(__name__)

# Register EmailLog model for admin viewing
@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['booking', 'email_type', 'recipient_email', 'sent_successfully', 'sent_at']
    list_filter = ['email_type', 'sent_successfully', 'sent_at']
    search_fields = ['recipient_email', 'subject', 'booking__id']
    readonly_fields = ['booking', 'email_type', 'recipient_email', 'subject',
                       'sent_successfully', 'error_message', 'sent_at']

    def has_add_permission(self, request):
        # Email logs are created automatically, don't allow manual creation
        return False

# Booking model with list filters and bulk actions
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'vehicle', 'status', 'requested_date', 'requested_time', 'user', 'guest_name']
    list_display_links = ['id', 'vehicle']
    search_fields = ['vehicle__make', 'vehicle__model', 'guest_name', 'user__email']
    list_filter = ['status', 'requested_date', 'vehicle__make', 'vehicle__year']
    actions = ['mark_confirmed', 'mark_completed', 'mark_canceled']

    def mark_confirmed(self, request, queryset):
        """
        Bulk action to mark bookings as confirmed and send emails.
        """
        updated_count = 0
        email_success_count = 0

        for booking in queryset:
            old_status = booking.status
            booking.status = 'confirmed'
            booking.save()
            updated_count += 1

            # Send status update email if status actually changed
            if old_status != 'confirmed':
                try:
                    email_sent = email_service.send_booking_status_update(booking)
                    if email_sent:
                        email_success_count += 1
                        logger.info(f"Confirmation email sent for booking #{booking.id}")
                    else:
                        logger.warning(f"Failed to send confirmation email for booking #{booking.id}")
                except Exception as e:
                    logger.error(f"Error sending confirmation email for booking #{booking.id}: {str(e)}")

        # Show admin message with results
        message = f"Updated {updated_count} booking(s) to confirmed."
        if email_success_count > 0:
            message += f" Sent {email_success_count} confirmation email(s)."
        if email_success_count < updated_count:
            message += f" {updated_count - email_success_count} email(s) failed to send."

        self.message_user(request, message)

    mark_confirmed.short_description = 'Mark selected bookings as Confirmed (with email)'

    def mark_completed(self, request, queryset):
        """Mark bookings as completed (no email sent)."""
        updated_count = queryset.update(status='completed')
        self.message_user(request, f"Marked {updated_count} booking(s) as completed.")

    mark_completed.short_description = 'Mark selected bookings as Completed'

    def mark_canceled(self, request, queryset):
        """
        Bulk action to mark bookings as canceled and send emails.
        """
        updated_count = 0
        email_success_count = 0

        for booking in queryset:
            old_status = booking.status
            booking.status = 'canceled'
            booking.save()
            updated_count += 1

            # Send cancellation email if status actually changed
            if old_status != 'canceled':
                try:
                    email_sent = email_service.send_booking_status_update(booking)
                    if email_sent:
                        email_success_count += 1
                        logger.info(f"Cancellation email sent for booking #{booking.id}")
                    else:
                        logger.warning(f"Failed to send cancellation email for booking #{booking.id}")
                except Exception as e:
                    logger.error(f"Error sending cancellation email for booking #{booking.id}: {str(e)}")

        message = f"Canceled {updated_count} booking(s)."
        if email_success_count > 0:
            message += f" Sent {email_success_count} cancellation email(s)."
        if email_success_count < updated_count:
            message += f" {updated_count - email_success_count} email(s) failed to send."

        self.message_user(request, message)

    mark_canceled.short_description = 'Mark selected bookings as Canceled (with email)'

    def save_model(self, request, obj, form, change):
        """
        Override save_model to send emails when individual booking status changes.

        This is called when a staff member edits a booking individually.
        """
        # Get the old status if this is an update
        old_status = None
        if change and obj.pk:
            try:
                old_booking = Booking.objects.get(pk=obj.pk)
                old_status = old_booking.status
            except Booking.DoesNotExist:
                old_status = None

        # Save the booking
        super().save_model(request, obj, form, change)

        # Send email if status changed to confirmed, rescheduled, or canceled
        if change and old_status and old_status != obj.status:
            if obj.status in ['confirmed', 'rescheduled', 'canceled']:
                try:
                    email_sent = email_service.send_booking_status_update(obj)
                    if email_sent:
                        self.message_user(request, f"Booking status updated and email sent to customer.")
                        logger.info(f"Status update email sent for booking #{obj.id} (status: {obj.status})")
                    else:
                        self.message_user(request, f"Booking status updated but email failed to send.", level='WARNING')
                        logger.warning(f"Failed to send status update email for booking #{obj.id}")
                except Exception as e:
                    self.message_user(request, f"Booking status updated but email error: {str(e)}", level='ERROR')
                    logger.error(f"Error sending status update email for booking #{obj.id}: {str(e)}")

    # FullCalendar logic
    change_list_template = "admin/bookings/booking/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('calendar/', self.admin_site.admin_view(self.booking_calendar_view), name='bookings_booking_calendar'),
            path('calendar/events/', self.admin_site.admin_view(self.booking_calendar_events),
                 name='bookings_booking_calendar_events'),
        ]
        return my_urls + urls

    def booking_calendar_view(self, request):
        """
        Render the page with the FullCalendar to show bookings calendar in admin.
        """
        # Pass any extra context if needed
        context = {
            'title': 'Bookings Calendar',
            'site_header': self.admin_site.site_header,
            'site_title': self.admin_site.site_title,
            'has_permission': True,  # ensure user has permission for rendering menu
        }
        return render(request, 'admin/bookings/booking/calendar.html', context)

    def booking_calendar_events(self, request):
        """
        JSON endpoint to provide all bookings as events for FullCalendar.
        """
        status_color_map = {
            'pending': '#FFA500',  # orange
            'confirmed': '#378006',  # green
            'rescheduled': '#1E90FF',  # dodger blue
            'completed': '#6c757d',  # gray
            'canceled': '#FF0000'  # red
        }
        bookings = Booking.objects.order_by('requested_date', 'requested_time')
        events = []
        for b in bookings:
            try:
                start_dt = datetime.datetime.combine(b.requested_date, b.requested_time)
                end_dt = start_dt + datetime.timedelta(minutes=60)  # assuming 60 min slots
                color = status_color_map.get(b.status, '#000000')  # fallback to black
                events.append({
                    'title': f'{b.vehicle} - {b.guest_name or "Guest"} [{b.status.capitalize()}]',
                    'start': start_dt.isoformat(),
                    'end': end_dt.isoformat(),
                    'color': color,  # green color or customize as needed
                })
            except Exception as e:
                # Log or ignore faulty booking record
                print(f"Error processing booking {b.pk}: {e}")

        return JsonResponse(events, safe=False)

    # End FullCalendar logic