from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Listing, Booking, Review


class ListingSerializer(serializers.ModelSerializer):
    host = serializers.StringRelatedField(read_only=True)

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
        ]
        read_only_fields = ['listing_id', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['host'] = self.context['request'].user
        return super().create(validated_data)



class BookingSerializer(serializers.ModelSerializer):
    listing = serializers.PrimaryKeyRelatedField(queryset=Listing.objects.all())
    user = serializers.StringRelatedField(read_only=True)

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
        ]
        read_only_fields = ['booking_id', 'user', 'total_price', 'created_at']

    def validate(self, data):
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError("End date must be after start date.")
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user

        listing = validated_data['listing']
        nights = (validated_data['end_date'] - validated_data['start_date']).days
        validated_data['total_price'] = listing.price_per_night * nights

        return super().create(validated_data)

class ReviewSerializer(serializers.ModelSerializer):
    listing = serializers.PrimaryKeyRelatedField(queryset=Listing.objects.all())

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
