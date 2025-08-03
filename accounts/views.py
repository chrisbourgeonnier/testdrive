from django.views.generic import TemplateView

class LoginPageView(TemplateView):
    template_name = 'login/login.html'
