import requests
import json
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
            booking = Booking.objects.get(id=booking_id, user=request.user)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)

        tx_ref = str(uuid.uuid4())  # unique transaction reference
        amount = booking.total_price

        payload = {
            "amount": str(amount),
            "currency": "ETB",
            "email": request.user.email,
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "tx_ref": tx_ref,
            "callback_url": f"http://localhost:8000/api/payments/verify/{tx_ref}/",
            "return_url": "http://localhost:8000/api/payments/success/",
            "customization": {
                "title": f"Payment for Booking {booking.id}",
                "description": f"Payment for {booking.listing.name}"
            }
        }

        headers = {
            "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(f"{settings.CHAPA_BASE_URL}/transaction/initialize",
                                 json=payload, headers=headers)
        data = response.json()

        if response.status_code != 200 or data.get("status") != "success":
            return Response({"error": data}, status=status.HTTP_400_BAD_REQUEST)

        # Save payment record
        payment = Payment.objects.create(
            booking=booking,
            user=request.user,
            transaction_id=tx_ref,
            amount=amount,
            status=Payment.Status.PENDING
        )

        return Response({
            "checkout_url": data["data"]["checkout_url"],
            "transaction_id": tx_ref
        }, status=status.HTTP_201_CREATED)

class VerifyPaymentView(APIView):
    def get(self, request, tx_ref):
        """
        Callback handler for Chapa.
        Always verify the transaction before updating status.
        """
        headers = {
            "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        # Verify transaction with Chapa
        response = requests.get(f"{settings.CHAPA_BASE_URL}/transaction/verify/{tx_ref}",
                                headers=headers)
        data = response.json()

        try:
            payment = Payment.objects.get(transaction_id=tx_ref)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

        # Update status based on verified response
        chapa_status = data.get("data", {}).get("status", "").lower()
        if chapa_status == "success":
            payment.status = Payment.Status.COMPLETED
        elif chapa_status in ["failed", "cancelled"]:
            payment.status = Payment.Status.FAILED
        else:
            payment.status = Payment.Status.PENDING

        payment.save()

        return Response({
            "transaction_id": payment.transaction_id,
            "status": payment.status
        }, status=status.HTTP_200_OK)


class PaymentSuccessView(APIView):
    def get(self, request):
        return Response({"message": "Payment completed. Frontend coming soon."})
    