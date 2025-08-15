from django.urls import path
from .views import (
    CreateBookingView, BookingThanksView, BookingListView,
    CancelBookingView, RescheduleBookingView,
)

urlpatterns = [
    path('list/', BookingListView.as_view(), name='booking_list'),
    path('request/', CreateBookingView.as_view(), name='create_booking'),
    path('thanks/', BookingThanksView.as_view(), name='booking_thanks'),
    path('<int:pk>/cancel/', CancelBookingView.as_view(), name='booking_cancel'),
    path('<int:pk>/reschedule/', RescheduleBookingView.as_view(), name='booking_reschedule'),
]
