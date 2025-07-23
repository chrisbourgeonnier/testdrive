from django.contrib import admin
from .models import Vehicle

# Register your Vehicle model with the admin, enabling search, list filters, etc.
@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['id', 'make', 'model', 'year', 'price', 'is_active']
    list_display_links = ['id', 'make', 'model']
    search_fields = ['make', 'model', 'year']
    list_filter = ['make', 'year', 'is_active']
    ordering = ['make', 'model', 'year']