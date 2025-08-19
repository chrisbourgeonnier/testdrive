from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from .forms import RegisterForm
from django.contrib.auth.views import LoginView
from django.contrib.auth.views import LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.utils import timezone
from bookings.models import Booking
from django.db.models import Q

class LoginPageView(LoginView):
    """
    Custom login view with branded template and authentication redirect.

    Uses custom template with branded styling and redirects already
    authenticated users to prevent unnecessary login attempts.
    """
    template_name = 'login/login.html'
    redirect_authenticated_user = True

class RegisterPageView(FormView):
    """
    User registration view with enhanced profile creation.

    Creates both User and UserProfile instances with additional fields
    like phone number and date of birth required for test drive bookings.
    Includes CAPTCHA protection against automated registration attempts.
    """
    template_name = 'accounts/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('login')  # After registration, go to login

    def form_valid(self, form):
        """
        Process successful user registration.

        Creates user account and associated profile with extended information
        including phone number and date of birth. Redirects to login page
        for immediate authentication.

        Args:
            form: Valid RegisterForm instance

        Returns:
            HttpResponse: Success response redirecting to login
        """
        form.save()  # This creates the user
        return super().form_valid(form)

class LogoutViewAllowGet(LogoutView):
    """
    Custom logout view that accepts both GET and POST requests.

    Overrides Django's default POST-only logout behavior to allow
    GET requests for simpler logout link implementation.
    """
    def dispatch(self, request, *args, **kwargs):
        """
        Handle both GET and POST logout requests.

        Converts GET requests to POST internally to maintain security
        while providing convenient logout links.

        Args:
            request: HTTP request object
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            HttpResponse: Logout response
        """
        if request.method.lower() == 'get':
            return self.post(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

class UserDashboardView(LoginRequiredMixin, TemplateView):
    """
    User dashboard displaying booking history and upcoming appointments.

    Shows:
    - Upcoming active bookings with reschedule/cancel options
    - Past booking history including canceled bookings
    - Booking status information and management actions

    Requires user authentication via LoginRequiredMixin.
    """
    template_name = 'accounts/dashboard.html'

    def get_context_data(self, **kwargs):
        """
        Prepare dashboard context with user's booking information.

        Separates user's bookings into two categories:
        - upcoming: Future or same-day non-canceled bookings
        - past: Previous dates or any canceled bookings

        Orders bookings chronologically for easy review.

        Returns:
            dict: Template context containing 'upcoming' and 'past' booking lists
        """
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        # Current user reservations
        my_bookings = Booking.objects.filter(user=user).order_by('-requested_date', '-requested_time')

        today = timezone.localdate()
        ctx['upcoming'] = my_bookings.filter(
            requested_date__gte=today
        ).exclude(status='canceled').order_by('requested_date', 'requested_time')

        ctx['past'] = my_bookings.filter(
            Q(requested_date__lt=today) | Q(status='canceled')
        ).order_by('-requested_date', '-requested_time')
        return ctx