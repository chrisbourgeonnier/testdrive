from django.db import models

# Vehicle model to match car attributes
class Vehicle(models.Model):
    # vehicle_id = models.IntegerField(unique=True)  # Richmonds ID or imported ID
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField()
    km = models.IntegerField("Kilometres")
    engine_size = models.IntegerField("Engine Size (cc)")
    transmission = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    photo_link = models.URLField("Primary Photo URL")
    description = models.TextField()
    link = models.URLField("Vehicle page link on Richmonds")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Optional: - for local/media image uploads in the future instead of using photo_link
    # photo_image = models.ImageField(upload_to='vehicle_photos/', blank=True, null=True)

    def __str__(self):
        return f"{self.year} {self.make} {self.model}"