from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Listing, Booking, Review, Payment
from django.conf import settings


class ListingSerializer(serializers.ModelSerializer):
    host = serializers.StringRelatedField(read_only=True)
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Listing
        fields = [
            'listing_id',
            'host',
            'name',
            'description',
            'location',
            'price_per_night',
            'created_at',
            'updated_at',
            'average_rating'
        ]
        read_only_fields = ['listing_id', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['host'] = self.context['request'].user
        return super().create(validated_data)


class BookingSerializer(serializers.ModelSerializer):
    listing = serializers.PrimaryKeyRelatedField(queryset=Listing.objects.all())
    user = serializers.StringRelatedField(read_only=True)
    average_rating = serializers.FloatField(source="listing.average_rating", read_only=True)
    checkout_url = serializers.CharField(read_only=True)  # dynamically added after payment
    tx_ref = serializers.CharField(read_only=True)

    class Meta:
        model = Booking
        fields = [
            'booking_id',
            'listing',
            'user',
            'start_date',
            'end_date',
            'total_price',
            'status',
            'created_at',
            'average_rating',
            'checkout_url',
            'tx_ref'
        ]
        read_only_fields = ['booking_id', 'user', 'total_price', 'created_at', 'checkout_url', 'tx_ref']

    def validate(self, data):
        # End date check
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError("End date must be after start date.")

        # Overlapping booking check
        listing = data['listing']
        start_date = data['start_date']
        end_date = data['end_date']

        overlapping = Booking.objects.filter(
            listing=listing,
            start_date__lt=end_date,
            end_date__gt=start_date
        )

        if self.instance:
            overlapping = overlapping.exclude(pk=self.instance.pk)  # exclude self when updating
        if overlapping.exists():
            raise serializers.ValidationError("This listing is already booked for the selected dates.")

        return data

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user

        listing = validated_data['listing']
        nights = (validated_data['end_date'] - validated_data['start_date']).days
        validated_data['total_price'] = listing.price_per_night * nights

        booking = super().create(validated_data)
        return booking

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        nights = (instance.end_date - instance.start_date).days
        instance.total_price = instance.listing.price_per_night * nights
        instance.save()
        return instance


class ReviewSerializer(serializers.ModelSerializer):
    listing = serializers.PrimaryKeyRelatedField(queryset=Listing.objects.all())
    average_rating = serializers.FloatField(source="listing.average_rating", read_only=True)

    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

    def validate(self, data):
        user = self.context['request'].user
        listing = data.get('listing')

        if Review.objects.filter(user=user, listing=listing).exists():
            raise serializers.ValidationError("You've already reviewed this listing.")
        return data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ("status", "transaction_id", "checkout_url", "created_at", "updated_at")
