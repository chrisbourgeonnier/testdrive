from django import forms
from .models import Booking
from captcha.fields import CaptchaField

from django import forms
from .models import Booking
from captcha.fields import CaptchaField
from datetime import date
import re

class BookingForm(forms.ModelForm):
    # Captcha to prevent spam submissions
    captcha = CaptchaField()

    # HTML5 date picker for date of birth
    dob = forms.DateField(
        label='Date of Birth',
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    def __init__(self, *args, **kwargs):
        # Allow the vehicle to be passed as a pre-set hidden field
        vehicle = kwargs.pop('vehicle', None)
        super().__init__(*args, **kwargs)

        if vehicle:
            # Pre-fill and hide the vehicle field if provided
            self.fields['vehicle'].initial = vehicle
            self.fields['vehicle'].widget = forms.HiddenInput()

        # Hide booking date and time; selected via FullCalendar on the frontend
        self.fields['requested_date'].widget = forms.HiddenInput()
        self.fields['requested_time'].widget = forms.HiddenInput()

    # -------------------------------
    # Custom Field Validations
    # -------------------------------

    def clean_guest_name(self):
        """
        Ensure the guest name contains only letters and spaces.
        Disallows numbers, symbols, or empty input.
        """
        name = self.cleaned_data['guest_name']
        if not re.match(r'^[A-Za-z\s]+$', name):
            raise forms.ValidationError("Name must contain only letters and spaces.")
        return name

    def clean_guest_phone(self):
        """
        Ensure the guest phone contains exactly 10 digits.
        No letters or symbols are allowed.
        """
        phone = self.cleaned_data['guest_phone']
        if not re.match(r'^\d{10}$', phone):
            raise forms.ValidationError("Phone number must contain exactly 10 digits.")
        return phone

    def clean_dob(self):
        """
        Ensure the guest is at least 25 years old.
        If not, prevent form submission.
        """
        dob = self.cleaned_data['dob']
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        if age < 25:
            raise forms.ValidationError("You must be at least 25 years old to book a test drive.")
        return dob

    # ------------------------------------
    # Django Meta configuration
    # ------------------------------------
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
