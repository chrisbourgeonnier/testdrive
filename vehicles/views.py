from django.shortcuts import render
from .models import Vehicle

# Create your views here.
def vehicle_list(request):
    vehicles = Vehicle.objects.all()
    return render(request, 'vehicles/vehicle_list.html', {'vehicles': vehicles})