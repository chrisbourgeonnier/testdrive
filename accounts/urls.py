from django.urls import path
from .views import LoginPageView, RegisterPageView, UserDashboardView

urlpatterns = [
    path('login/', LoginPageView.as_view(), name='login'),
    path('register/', RegisterPageView.as_view(), name='register'),  # ✅ New
    path('dashboard/', UserDashboardView.as_view(), name='user_dashboard'),  # New user_dashboard
]