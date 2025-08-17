from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from listings.models import Listing
from faker import Faker
import random

fake = Faker()

class Command(BaseCommand):
    help = 'Seed the database with sample listings'

    def handle(self, *args, **kwargs):
        # Get or create a demo host
        host, _ = User.objects.get_or_create(
            username='demo_host',
            defaults={'email': 'host@example.com', 'password': 'demo1234'}
        )

        for _ in range(10):
            name = fake.catch_phrase()
            description = fake.text(max_nb_chars=200)
            location = fake.city()
            price_per_night = round(random.uniform(50, 500), 2)

            Listing.objects.create(
                host=host,
                name=name,
                description=description,
                location=location,
                price_per_night=price_per_night
            )

        self.stdout.write(self.style.SUCCESS('Successfully seeded listings.'))
