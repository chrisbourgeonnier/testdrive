from django.views.generic import ListView, DetailView
from .models import Vehicle

class VehicleListView(ListView):
    model = Vehicle
    queryset = Vehicle.objects.filter(is_active=True).order_by('make', 'model', 'year')
    template_name = 'vehicles/vehicle_list.html'
    context_object_name = 'vehicles'

class VehicleDetailView(DetailView):
    model = Vehicle
    template_name = 'vehicles/vehicle_detail.html'
    context_object_name = 'vehicle'
