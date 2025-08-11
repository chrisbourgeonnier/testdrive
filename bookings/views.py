from django.views.generic import TemplateView
from django.views.generic.edit import CreateView
from django.views.generic import ListView
from .models import Booking
from .forms import BookingForm
from django.urls import reverse_lazy
from vehicles.models import Vehicle
from .email_service import email_service
from accounts.models import UserProfile
import logging
from django.db import IntegrityError

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

        # Add initial data for logged-in user to pre-fill booking form
        if self.request.user.is_authenticated:
            user = self.request.user
            initial = kwargs.get('initial', {}).copy()
            initial.update({
                'guest_name': f"{user.first_name} {user.last_name}".strip(),
                'guest_email': user.email,
            })

            # Try to get phone and dob from profile
            try:
                initial['guest_phone'] = user.profile.phone_number
            except (AttributeError, UserProfile.DoesNotExist):
                initial['guest_phone'] = ''

            try:
                initial['dob'] = user.profile.dob
            except (AttributeError, UserProfile.DoesNotExist):
                initial['dob'] = None

            kwargs['initial'] = initial

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

        # ---- PRECHECKS
        user = self.request.user if self.request.user.is_authenticated else None
        d = form.cleaned_data.get('requested_date')
        t = form.cleaned_data.get('requested_time')
        vehicle = form.cleaned_data.get('vehicle')

        # Blocks the same user from having two reservations on the same date and time (regardless of the car).
        if user and d and t and Booking.objects.filter(
                user=user, requested_date=d, requested_time=t
        ).exists():
            form.add_error(None, "You already have a booking at that date and time.")
            return self.form_invalid(form)

        # Block the same guest from having two reservations on the same date and time
        guest_email = form.cleaned_data.get('guest_email')
        if not user and guest_email and d and t and Booking.objects.filter(
                user__isnull=True, guest_email=guest_email, requested_date=d, requested_time=t
        ).exists():
            form.add_error(None, "You already have a booking at that date and time.")
            return self.form_invalid(form)

        # Blocks the same car from being reserved on the same date and time by any user.
        if vehicle and d and t and Booking.objects.filter(
                vehicle=vehicle, requested_date=d, requested_time=t
        ).exists():
            form.add_error(None, "This vehicle is already booked for that time.")
            return self.form_invalid(form)

        # Assign the user BEFORE saving (if applicable)
        if user and not form.instance.user_id:
            form.instance.user = user

        # We'll keep your reservation. If someone else takes the same shift at the same time, we'll let you know and request a different time.
        try:
            # Save the booking first
            response = super().form_valid(form)
        except IntegrityError:
            # We check that the time slot is available, but if someone else has booked it right away, we'll let them know and request a different time slot.
            form.add_error(None, "Sorry, that time just got taken. Please pick another slot.")
            return self.form_invalid(form)

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

    def form_invalid(self, form):
        print("❌ FORM INVALID ERRORS:", form.errors)
        return super().form_invalid(form)
        return False

class BookingThanksView(TemplateView):
    template_name = 'bookings/booking_thanks.html'

class BookingListView(ListView):
    model = Booking
    template_name = 'bookings/booking_list.html'
    context_object_name = 'bookings'