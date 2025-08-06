from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class UserWithProfileForm(forms.ModelForm):
    phone_number = forms.CharField(max_length=20, required=False, label='Phone Number')
    dob = forms.DateField(required=False, label='Date of Birth', widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email',
                  'phone_number', 'dob', 'is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions']

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