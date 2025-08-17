from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_payment_email(email, checkout_url):
    subject = "Complete your booking payment"
    message = f"Please complete your payment by visiting the link: {checkout_url}"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

@shared_task
def send_payment_confirmation(email, booking_id):
    subject = "Payment Successful"
    message = f"Your payment for booking {booking_id} has been successfully completed."
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
