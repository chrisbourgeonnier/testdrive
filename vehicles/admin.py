from django.urls import path, reverse
from django.http import HttpResponseRedirect
from django.contrib import admin, messages
from django.core.management import call_command
from .models import Vehicle

# Register your Vehicle model with the admin, enabling search, list filters, etc.
@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['id', 'make', 'model', 'year', 'price', 'is_active']
    list_display_links = ['id', 'make', 'model']
    search_fields = ['make', 'model', 'year']
    list_filter = ['make', 'year', 'is_active']
    ordering = ['make', 'model', 'year']

    change_list_template = "admin/vehicles/vehicle/change_list.html"  # ensure it matches your custom template path

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                'import-vehicles/',
                self.admin_site.admin_view(self.import_vehicles),
                name='vehicles_vehicle_import'
            ),
        ]
        return my_urls + urls

    def import_vehicles(self, request):
        # Run your custom management command
        try:
            call_command('import_vehicles')
            self.message_user(request, "Vehicles imported successfully.", level=messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"Import failed: {e}", level=messages.ERROR)

        # Redirect back to changelist page
        changelist_url = reverse('admin:vehicles_vehicle_changelist')
        return HttpResponseRedirect(changelist_url)