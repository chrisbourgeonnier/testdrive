from django.urls import path, reverse
from django.http import HttpResponseRedirect
from django.contrib import admin, messages
from django.core.management import call_command
from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    """
    Vehicle management admin interface with inventory import functionality.

    Features:
    - Vehicle listing with search and filtering capabilities
    - Custom "Update Inventory" action to sync with Richmonds website
    - Bulk activate/deactivate operations
    - Integration with vehicle import management command

    The import functionality scrapes vehicle data from Richmonds.com.au
    and creates/updates Vehicle records automatically.
    """
    list_display = ['id', 'make', 'model', 'year', 'price', 'is_active']
    list_display_links = ['id', 'make', 'model']
    search_fields = ['make', 'model', 'year']
    list_filter = ['make', 'year', 'is_active']
    ordering = ['make', 'model', 'year']

    change_list_template = "admin/vehicles/vehicle/change_list.html"  # ensure it matches your custom template path

    def get_urls(self):
        """
        Add custom URL patterns for vehicle import functionality.

        Extends default admin URLs with import endpoint accessible
        via the "Update Inventory" button in the admin interface.

        Returns:
            list: URL patterns including import endpoint
        """
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
        """
        Execute vehicle import from Richmonds website.

        Runs the 'import_vehicles' management command to scrape and sync
        vehicle inventory from Richmonds.com.au. Displays success or error
        messages to the admin user and redirects back to vehicle list.

        Args:
            request: HTTP request object

        Returns:
            HttpResponseRedirect: Redirect to vehicle changelist page
        """
        try:
            call_command('import_vehicles')
            self.message_user(request, "Vehicles imported successfully.", level=messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"Import failed: {e}", level=messages.ERROR)

        changelist_url = reverse('admin:vehicles_vehicle_changelist')
        return HttpResponseRedirect(changelist_url)