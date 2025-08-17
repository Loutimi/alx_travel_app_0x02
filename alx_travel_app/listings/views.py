import requests
import uuid
from rest_framework import viewsets, status
from .models import Listing, Booking, Review, Payment
from .serializers import ListingSerializer, BookingSerializer, ReviewSerializer, PaymentSerializer
from rest_framework.exceptions import PermissionDenied
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from .tasks import send_payment_email, send_confirmation_email


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

        tx_ref = str(uuid.uuid4())
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

        # Save payment record with checkout_url
        payment = Payment.objects.create(
            booking=booking,
            user=request.user,
            transaction_id=tx_ref,
            amount=amount,
            status=Payment.Status.PENDING,
            checkout_url=data["data"]["checkout_url"] 
        )

        # Send reminder email via Celery
        send_payment_email.delay(request.user.email, payment.checkout_url)

        return Response({
            "checkout_url": payment.checkout_url,
            "transaction_id": tx_ref
        }, status=status.HTTP_201_CREATED)


class VerifyPaymentView(APIView):
    def get(self, request, tx_ref):
        try:
            payment = Payment.objects.get(transaction_id=tx_ref)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

        response = requests.get(
            f"https://api.chapa.co/v1/transaction/verify/{tx_ref}",
            headers={"Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"}
        )
        data = response.json()

        if data["status"] == "success" and data["data"]["status"] == "success":
            payment.status = "Completed"
            payment.save()

            # Send confirmation email asynchronously
            send_confirmation_email.delay(payment.user.email, payment.amount)

            return Response({"message": "Payment successful and confirmed."}, status=status.HTTP_200_OK)

        payment.status = "Failed"
        payment.save()
        return Response({"message": "Payment verification failed."}, status=status.HTTP_400_BAD_REQUEST)


class PaymentSuccessView(APIView):
    def get(self, request):
        return Response({"message": "Payment completed. Frontend coming soon."})
    