from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from .forms import RegisterForm
from django.contrib.auth.views import LoginView
from django.contrib.auth.views import LogoutView


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