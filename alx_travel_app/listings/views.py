import requests
import uuid
from django.shortcuts import render
from rest_framework import viewsets, status
from .models import Listing, Booking, Review, Payment
from .serializers import ListingSerializer, BookingSerializer, ReviewSerializer, PaymentSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.exceptions import PermissionDenied
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response



class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if self.request.user.is_staff:
                return Booking.objects.all()  # Admins/staff see all bookings
            return Booking.objects.filter(user=user)  # Normal users see only theirs
        return Booking.objects.none()  # Anonymous users see nothing

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.user != self.request.user:
            raise PermissionDenied("You can only edit your own review.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied("You can only delete your own review.")
        instance.delete()


class InitiatePaymentView(APIView):
    def post(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)

        tx_ref = str(uuid.uuid4())  # unique transaction reference
        amount = booking.total_price

        payload = {
            "amount": str(amount),
            "currency": "ETB",  # adjust based on your setup
            "email": request.user.email,
            "tx_ref": tx_ref,
            "callback_url": "https://yourdomain.com/api/payments/verify/",
        }

        headers = {"Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"}

        response = requests.post(f"{settings.CHAPA_BASE_URL}/initialize", json=payload, headers=headers)
        data = response.json()

        if response.status_code != 200:
            return Response({"error": data}, status=status.HTTP_400_BAD_REQUEST)

        # Save payment record
        payment = Payment.objects.create(
            booking=booking,
            transaction_id=tx_ref,
            amount=amount,
            status=Payment.Status.PENDING,
        )

        return Response({
            "checkout_url": data["data"]["checkout_url"],
            "transaction_id": tx_ref,
        }, status=status.HTTP_201_CREATED)


class VerifyPaymentView(APIView):
    def get(self, request, tx_ref):
        headers = {"Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"}
        response = requests.get(f"{settings.CHAPA_BASE_URL}/verify/{tx_ref}", headers=headers)
        data = response.json()

        try:
            payment = Payment.objects.get(transaction_id=tx_ref)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

        if data.get("status") == "success":
            payment.status = Payment.Status.COMPLETED
        else:
            payment.status = Payment.Status.FAILED
        payment.save()

        return Response(PaymentSerializer(payment).data, status=status.HTTP_200_OK)
