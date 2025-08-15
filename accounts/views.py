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
    template_name = 'login/login.html'
    redirect_authenticated_user = True

class RegisterPageView(FormView):
    template_name = 'accounts/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('login')  # After registration, go to login

    def form_valid(self, form):
        form.save()  # This creates the user
        return super().form_valid(form)

class LogoutViewAllowGet(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        if request.method.lower() == 'get':
            return self.post(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

class UserDashboardView(LoginRequiredMixin, TemplateView): # New class
    template_name = 'accounts/dashboard.html'

    def get_context_data(self, **kwargs):
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