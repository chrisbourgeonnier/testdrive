from django.urls import path, reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.contrib import admin
from .models import Booking
from django.utils.dateformat import format
import datetime

# Booking model with list filters and bulk actions
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'vehicle', 'status', 'requested_date', 'requested_time', 'user', 'guest_name']
    list_display_links = ['id', 'vehicle']
    search_fields = ['vehicle__make', 'vehicle__model', 'guest_name', 'user__email']
    list_filter = ['status', 'requested_date', 'vehicle__make', 'vehicle__year']
    actions = ['mark_confirmed', 'mark_completed', 'mark_canceled']

    def mark_confirmed(self, request, queryset):
        queryset.update(status='confirmed')
    mark_confirmed.short_description = 'Mark selected bookings as Confirmed'

    def mark_completed(self, request, queryset):
        queryset.update(status='completed')
    mark_completed.short_description = 'Mark selected bookings as Completed'

    def mark_canceled(self, request, queryset):
        queryset.update(status='canceled')
    mark_canceled.short_description = 'Mark selected bookings as Canceled'

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