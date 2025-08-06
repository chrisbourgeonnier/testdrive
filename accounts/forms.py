from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from captcha.fields import CaptchaField
from .models import UserProfile

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True, label='First Name')
    last_name = forms.CharField(max_length=30, required=True, label='Last Name')
    phone_number = forms.CharField(max_length=20, required=True, label='Phone Number')
    dob = forms.DateField(
        required=True,
        label='Date of Birth',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    captcha = CaptchaField()

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
            "phone_number",
            "dob",
            "captcha",
        ]

    def save(self, commit=True):
        user = super().save(commit)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.phone_number = self.cleaned_data["phone_number"]
            profile.dob = self.cleaned_data["dob"]
            profile.save()
        return user

class UserWithProfileForm(forms.ModelForm):
    phone_number = forms.CharField(max_length=20, required=False, label='Phone Number')
    dob = forms.DateField(required=False, label='Date of Birth', widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "dob",
            "is_staff",
            "is_active",
            "is_superuser",
            "groups",
            "user_permissions"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            try:
                profile = self.instance.profile
                self.fields['phone_number'].initial = profile.phone_number
                self.fields['dob'].initial = profile.dob
            except UserProfile.DoesNotExist:
                pass

    def save(self, commit=True):
        user = super().save(commit)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.phone_number = self.cleaned_data.get('phone_number')
        profile.dob = self.cleaned_data.get('dob')
        profile.save()
        return user
