from django.contrib import admin
from .models import Booking

# Booking model with list filters and bulk actions
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'status', 'requested_date', 'requested_time', 'user', 'guest_name']
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