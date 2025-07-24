from django.views.generic import TemplateView
from django.views.generic.edit import CreateView
from django.views.generic import ListView
from .models import Booking
from .forms import BookingForm  # You'll create this form next
from django.urls import reverse_lazy
from vehicles.models import Vehicle

class CreateBookingView(CreateView):
    model = Booking
    form_class = BookingForm
    template_name = 'bookings/booking_form.html'
    success_url = reverse_lazy('booking_thanks')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        vehicle_pk = self.request.GET.get('vehicle')
        if vehicle_pk:
            try:
                vehicle = Vehicle.objects.get(pk=vehicle_pk)
                kwargs['vehicle'] = vehicle
            except Vehicle.DoesNotExist:
                pass
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vehicle_pk = self.request.GET.get('vehicle')
        if vehicle_pk:
            try:
                vehicle = Vehicle.objects.get(pk=vehicle_pk)
                context['selected_vehicle'] = vehicle
            except Vehicle.DoesNotExist:
                context['selected_vehicle'] = None
        else:
            context['selected_vehicle'] = None
        return context

class BookingThanksView(TemplateView):
    template_name = 'bookings/booking_thanks.html'

class BookingListView(ListView):
    model = Booking
    template_name = 'bookings/booking_list.html'
    context_object_name = 'bookings'