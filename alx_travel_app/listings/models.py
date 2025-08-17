from django.db import models
from django.contrib.auth.models import User
import uuid
from django.core.exceptions import ValidationError
from datetime import timedelta


class Listing(models.Model):
    listing_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    name = models.CharField(max_length=50, null=False)
    description = models.TextField(null=False)
    location = models.CharField(max_length=50, null=False)
    price_per_night = models.DecimalField(max_digits=8, decimal_places=2, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at =models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Listing: {self.name}"


class Booking(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('canceled', 'Canceled'),
    ]
    booking_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    start_date = models.DateField(null=False)
    end_date = models.DateField(null=False)
    total_price = models.DecimalField(max_digits=8, decimal_places=2, null=False)
    status = models.CharField(choices=STATUS_CHOICES, max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.total_price:
            num_nights = (self.end_date - self.start_date).days
            self.total_price = self.listing.price_per_night * num_nights
        super().save(*args, **kwargs)

    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError('End date must be after start date (at least one night)')

    def __str__(self):
        return f"Booking: {self.booking_id} for Listing: {self.listing.name}"


class Review(models.Model):

    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    review_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, null=False)
    comment = models.TextField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum([r.rating for r in reviews]) / reviews.count(), 1)
        return None


    class Meta:
        unique_together = ('listing', 'user')  # Prevents duplicate reviews for same listing by same user


    def __str__(self):
        return f"Rating: {self.rating} by User:{self.user}"
