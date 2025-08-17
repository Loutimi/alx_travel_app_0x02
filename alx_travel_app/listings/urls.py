from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ListingViewSet,
    BookingViewSet,
    ReviewViewSet,
    InitiatePaymentView,
    VerifyPaymentView,
    PaymentSuccessView,
)

router = DefaultRouter()
router.register(r'listings', ListingViewSet, basename='listing')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
    
    # Payment endpoints
    path('payments/initiate/<int:booking_id>/', InitiatePaymentView.as_view(), name='initiate-payment'),
    path('payments/verify/<str:tx_ref>/', VerifyPaymentView.as_view(), name='verify-payment'),
    path('payments/success/', PaymentSuccessView.as_view(), name='payment-success'),
]
