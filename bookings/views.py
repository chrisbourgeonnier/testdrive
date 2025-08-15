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
from django.contrib import messages
from django.views import View
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView

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

        qs = Booking.objects.exclude(status='canceled')

        # Blocks the same user from having two reservations on the same date and time (regardless of the car).
        if user and d and t and qs.filter(user=user, requested_date=d, requested_time=t).exists():
            messages.error(self.request, "You already have a booking at that date and time.")
            return self.form_invalid(form)

        # Block the same guest from having two reservations on the same date and time
        guest_name = form.cleaned_data.get('guest_name')
        guest_email = form.cleaned_data.get('guest_email')
        if guest_name and guest_email and d and t and qs.filter(
                guest_name=guest_name, guest_email=guest_email,
                requested_date=d, requested_time=t
        ).exists():
            messages.error(self.request, "You already have a booking at that date and time.")
            return self.form_invalid(form)

        # Blocks the same car from being reserved on the same date and time by any user.
        if vehicle and d and t and qs.filter(vehicle=vehicle, requested_date=d, requested_time=t).exists():
            messages.error(self.request, "This vehicle is already booked for that time.")
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

            messages.error(self.request, "Sorry, that time just got taken. Please pick another slot.")
            return self.form_invalid(form)

        messages.success(self.request, "Booking received. We'll confirm by email shortly.")

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
        # Manda cualquier error no-campal a los flash messages
        for err in form.non_field_errors():
            # Mensaje más amable si es el de unicidad
            txt = str(err)
            if 'Booking with this Vehicle' in txt and 'Requested time' in txt:
                txt = "This vehicle is already booked for that date and time."
            messages.error(self.request, txt)
        return super().form_invalid(form)

class BookingThanksView(TemplateView):
    template_name = 'bookings/booking_thanks.html'

class BookingListView(ListView):
    model = Booking
    template_name = 'bookings/booking_list.html'
    context_object_name = 'bookings'

class CancelBookingView(LoginRequiredMixin, View):
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk, user=request.user)
        today = timezone.localdate()

        # Only allow cancellation of future or same-day cancellations not yet completed
        if booking.status in ('canceled', 'completed'):
            messages.error(request, "This booking can't be canceled.")
            return redirect('user_dashboard')

        # Mark as canceled (this 'releases' the spot)
        booking.status = 'canceled'
        booking.save()

        # Email notification
        try:
            email_service.send_booking_status_update(booking)
        except Exception:
            pass

        messages.success(request, "Your booking was canceled.")
        return redirect('user_dashboard')

class RescheduleBookingView(LoginRequiredMixin, UpdateView):
    model = Booking
    form_class = BookingForm
    template_name = 'bookings/booking_form.html'
    success_url = reverse_lazy('user_dashboard')

    def get_queryset(self):
        # Make sure you can only touch your own stash
        return Booking.objects.filter(user=self.request.user)

    def form_valid(self, form):
        user = self.request.user
        d = form.cleaned_data.get('requested_date')
        t = form.cleaned_data.get('requested_time')
        vehicle = form.cleaned_data.get('vehicle')

        # Anti-collision rules (same logic as you create, but ignoring cancels and the pk itself)
        qs = Booking.objects.exclude(status='canceled').exclude(pk=self.object.pk)

        # Blocks the same user from having two reservations on the same date and time (regardless of the car).
        if user and d and t and qs.filter(user=user, requested_date=d, requested_time=t).exists():
            messages.error(self.request, "You already have a booking at that date and time.")
            return self.form_invalid(form)

        # Block the same guest from having two reservations on the same date and time
        guest_name = form.cleaned_data.get('guest_name')
        guest_email = form.cleaned_data.get('guest_email')
        if guest_name and guest_email and d and t and qs.filter(
            guest_name=guest_name, guest_email=guest_email,
            requested_date=d, requested_time=t
        ).exists():
            messages.error(self.request, "You already have a booking at that date and time.")
            return self.form_invalid(form)

        # Blocks the same car from being reserved on the same date and time by any user.
        if vehicle and d and t and qs.filter(
            vehicle=vehicle, requested_date=d, requested_time=t
        ).exists():
            messages.error(self.request, "This vehicle is already booked for that time.")
            return self.form_invalid(form)

        # Mark as rescheduled
        form.instance.status = 'rescheduled'
        response = super().form_valid(form)

        try:
            email_service.send_booking_status_update(self.object)
        except Exception:
            pass

        messages.success(self.request, "Your booking was rescheduled.")
        return response