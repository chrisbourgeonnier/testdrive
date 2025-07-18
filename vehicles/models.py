from django.db import models

# Create your models here.
class Vehicle(models.Model):
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='vehicle_images/', blank=True, null=True)
    """km = models.PositiveIntegerField()
    engine_size = models.CharField(max_length=100=
    cylinders = models.PositiveIntegerField()
    transmission = models.CharField(max_length=50)"""


    def __str__(self):
        return f"{self.year} {self.make} {self.model}"