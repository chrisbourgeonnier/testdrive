from django.db import models


class Vehicle(models.Model):
    """
    Represents a classic or prestige vehicle available for test drives.

    Contains vehicle specifications, pricing, images, and links to detailed
    information on the Richmonds website. Supports active/inactive states
    for inventory management and automatic import from external sources.

    Fields:
    - make, model, year: Basic vehicle identification
    - km, engine_size, transmission: Technical specifications
    - price: Vehicle pricing in AUD
    - photo_link: URL to primary vehicle image
    - description: Marketing description from vehicle detail page
    - link: URL to full vehicle details on Richmonds website
    - is_active: Controls visibility in public vehicle listings

    The link field serves as unique identifier for import operations.
    """
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