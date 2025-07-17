from django import forms
from .models import Booking
from captcha.fields import CaptchaField

class BookingForm(forms.ModelForm):
    captcha = CaptchaField()  # Adds a simple free captcha

    class Meta:
        model = Booking
        fields = [
            'vehicle', 'guest_name', 'guest_email', 'guest_phone',
            'requested_date', 'requested_time', 'captcha'
        ]
