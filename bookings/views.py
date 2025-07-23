from django.views.generic import TemplateView
from django.views.generic.edit import CreateView
from django.views.generic import ListView
from .models import Booking
from .forms import BookingForm  # You'll create this form next
from django.urls import reverse_lazy

class CreateBookingView(CreateView):
    model = Booking
    form_class = BookingForm
    template_name = 'bookings/booking_form.html'
    success_url = reverse_lazy('booking_thanks')

class BookingThanksView(TemplateView):
    template_name = 'bookings/booking_thanks.html'

class BookingListView(ListView):
    model = Booking
    template_name = 'bookings/booking_list.html'
    context_object_name = 'bookings'