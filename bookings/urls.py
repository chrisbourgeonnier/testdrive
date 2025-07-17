from django.urls import path
from .views import CreateBookingView, BookingThanksView

urlpatterns = [
    path('request/', CreateBookingView.as_view(), name='create_booking'),
    path('thanks/', BookingThanksView.as_view(), name='booking_thanks'),
]
