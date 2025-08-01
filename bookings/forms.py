from django import forms
from .models import Booking
from captcha.fields import CaptchaField

class BookingForm(forms.ModelForm):
    captcha = CaptchaField()  # Adds a simple free captcha

    dob = forms.DateField(
        label='Date of Birth',
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    def __init__(self, *args, **kwargs):
        # Accept a 'vehicle' keyword-only argument to pre-set & lock the vehicle
        vehicle = kwargs.pop('vehicle', None)
        super().__init__(*args, **kwargs)
        self.vehicle_hidden = isinstance(self.fields['vehicle'].widget, forms.HiddenInput)

        if vehicle:
            # Set the vehicle field to the passed vehicle
            self.fields['vehicle'].initial = vehicle
            # Make field not editable and hide it
            self.fields['vehicle'].widget = forms.HiddenInput()
        else:
            # Otherwise vehicle remains a regular selectable dropdown
            pass

        # Hide booking date/time inputs; to be set by JS calendar
        self.fields['requested_date'].widget = forms.HiddenInput()
        self.fields['requested_time'].widget = forms.HiddenInput()

    class Meta:
        model = Booking
        fields = [
            'vehicle', 'guest_name', 'guest_email', 'guest_phone', 'dob',
            'requested_date', 'requested_time', 'captcha'
        ]
        labels = {
            'guest_name': 'Name',
            'guest_email': 'Email',
            'guest_phone': 'Phone',
            'dob': 'Date of Birth',
            'requested_date': 'Desired Date',
            'requested_time': 'Desired Time',
        }
