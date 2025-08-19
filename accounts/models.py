from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    """
    Extended user profile information for registered users.

    Stores additional fields required for test drive bookings that are not
    part of Django's standard User model. Automatically created when a new
    User is registered through the post_save signal.

    Fields:
    - phone_number: Contact number for booking confirmations
    - dob: Date of birth for age verification (25+ requirement)

    Related to User model via OneToOne relationship accessible as user.profile
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone_number = models.CharField(max_length=20, blank=True)
    dob = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Profile for {self.user.username}"

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Signal handler to automatically create UserProfile when User is created.

    Ensures every User has an associated UserProfile for storing extended
    information required by the booking system. Triggered automatically
    on User creation.

    Args:
        sender: The User model class
        instance: The User instance being saved
        created: Boolean indicating if this is a new user
        **kwargs: Additional signal arguments
    """
    if created:
        UserProfile.objects.create(user=instance)
    # else:
    #     instance.profile.save()