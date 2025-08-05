from django.views.generic import TemplateView
from django.views.generic.edit import CreateView
from django.views.generic import ListView
from .models import Booking
from .forms import BookingForm
from django.urls import reverse_lazy
from vehicles.models import Vehicle
from .email_service import email_service  # Import our email service
import logging

logger = logging.getLogger(__name__)

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

    def form_valid(self, form):
        """
        Override form_valid to send emails after booking is created.

        This method is called when the booking form is successfully submitted.
        We save the booking first, then send confirmation emails.
        """
        # Save the booking first
        response = super().form_valid(form)

        # Get the newly created booking instance
        booking = self.object

        try:
            # Send confirmation email to customer
            logger.info(f"Sending booking confirmation email for booking #{booking.id}")
            customer_email_sent = email_service.send_booking_confirmation(booking)

            # Send notification email to staff
            logger.info(f"Sending staff notification email for booking #{booking.id}")
            staff_email_sent = email_service.send_staff_notification(booking)

            if customer_email_sent:
                logger.info(f"Customer confirmation email sent successfully for booking #{booking.id}")
            else:
                logger.warning(f"Failed to send customer confirmation email for booking #{booking.id}")

            if staff_email_sent:
                logger.info(f"Staff notification email sent successfully for booking #{booking.id}")
            else:
                logger.warning(f"Failed to send staff notification email for booking #{booking.id}")

        except Exception as e:
            # Log the error but don't prevent the booking from being created
            logger.error(f"Error sending emails for booking #{booking.id}: {str(e)}")

        return response

"""def form_invalid(self, form):
        print("❌ FORM INVALID ERRORS:", form.errors)
        #return super().form_invalid(form)
        return False"""

class BookingThanksView(TemplateView):
    template_name = 'bookings/booking_thanks.html'

class BookingListView(ListView):
    model = Booking
    template_name = 'bookings/booking_list.html'
    context_object_name = 'bookings'