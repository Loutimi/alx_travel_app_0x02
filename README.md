# 🌍 ALX Travel App

A Django-based travel booking platform that allows users to browse listings, create bookings, pay securely via **Chapa**, and leave reviews.  
Built as part of the **ALX Backend Specialization** to demonstrate proficiency with **Django**, **Django REST Framework (DRF)**, **Celery**, and third‑party payment integration.

---

**Version:** v1  
**Base API URL:** `http://127.0.0.1:8000/api/`

---

## 🚀 Features

- User registration & authentication (DRF-compatible: Basic/Session)
- Create, browse, and manage **listings**
- Make **bookings** with overlap validation
- **Chapa** payment integration
  - Initiate transaction and get `checkout_url`
  - Verify payment via Chapa’s verification endpoint
  - Persist **transaction_id (tx_ref)** and **status** (`Pending`, `Completed`, `Failed`, `Refunded`)
- Email notifications via **Celery** tasks
  - “Complete your payment” email with `checkout_url`
  - “Payment confirmation” email after successful verification
- Environment variable management with `django-environ`

---

## 🏗 Tech Stack

- **Backend:** Django, Django REST Framework
- **Payments:** Chapa API
- **Task Queue:** Celery (Redis/RabbitMQ)
- **Email:** Django email backend (console/dev or SMTP/prod)
- **Environment:** `django-environ` + `.env`
- **Database:** MySQL / SQLite / PostgreSQL (configurable)
- **App modules shown:** `listings` (models, serializers, views, urls, tasks)

---

## ⚙️ Installation & Setup

```bash
# 1) Clone the repo
git clone https://github.com/Loutimi/alx_travel_app_0x00.git
cd alx_travel_app_0x00

# 2) Create and activate virtualenv
python -m venv venv
# macOS/Linux
source venv/bin/activate
# Windows
venv\Scripts\activate

# 3) Install dependencies
pip install -r requirements.txt
```

### 🔑 Environment Variables

Create a `.env` file in the project root (same level as `manage.py`). Example:

```
# Django
SECRET_KEY=your_django_secret_key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Database (example for MySQL)
DB_NAME=alx_travel
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306

# Chapa
CHAPA_SECRET_KEY=CHASECK-xxxxxxxxxxxxxxxxxxxxxxxx
CHAPA_BASE_URL=https://api.chapa.co/v1

# Email (dev)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=no-reply@yourdomain.com

# Celery (Redis example)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

> In production, switch the email backend to SMTP and configure credentials accordingly.

### ▶️ Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### ▶️ Run Services

```bash
# Django
python manage.py runserver

# Celery worker (replace `your_project` with your Django project package, e.g. `alx_travel_app`)
celery -A your_project worker --loglevel=info

# (Optional) Celery beat for periodic tasks
celery -A your_project beat --loglevel=info
```

---

## 🧩 App Overview

### Models (key fields)

- **Listing**
  - `listing_id` (UUID, PK), `host` (FK to `User`), `name`, `description`, `location`,
    `price_per_night`, `created_at`, `updated_at`
  - `average_rating` property (computed from `Review`)

- **Booking**
  - `booking_id` (UUID, PK), `listing` (FK), `user` (FK), `start_date`, `end_date`,
    `total_price`, `status` (`pending|confirmed|canceled`), `created_at`
  - Overlap validation enforced in serializer
  - `total_price` auto-calculated by nights × `price_per_night`

- **Review**
  - `review_id` (UUID, PK), `listing` (FK), `user` (FK), `rating` (1–5), `comment`, `created_at`
  - `unique_together = ('listing', 'user')`

- **Payment**
  - `payment_id` (UUID, PK), `user` (FK), `booking` (FK)
  - `transaction_id` (Chapa `tx_ref`, unique), `amount`
  - `status` (choices: `Pending`, `Completed`, `Failed`, `Refunded`)
  - `checkout_url` (URLField), `created_at`, `updated_at`

---

## 📡 API Endpoints

> All endpoints are served under `/api/` via DRF routers + custom payment paths.

### 🏡 Listings
- `GET /listings/` – list all listings  
- `POST /listings/` – create listing (host inferred from request user)  
- `GET /listings/{listing_id}/` – retrieve listing  
- `PUT /listings/{listing_id}/` – update listing  
- `PATCH /listings/{listing_id}/` – partial update  
- `DELETE /listings/{listing_id}/` – delete listing  

### 🧳 Bookings
- `GET /bookings/` – list user’s bookings (staff see all)  
- `POST /bookings/` – create booking (overlap checked; price auto-calculated)  
- `GET /bookings/{booking_id}/` – retrieve booking  
- `PUT /bookings/{booking_id}/` – update booking  
- `PATCH /bookings/{booking_id}/` – partial update  
- `DELETE /bookings/{booking_id}/` – delete booking  

**Create Booking Request Example**
```json
{
  "listing": "UUID-OF-LISTING",
  "start_date": "2025-08-03",
  "end_date": "2025-08-07"
}
```

### 💳 Payments (Chapa)

- `POST /payments/initiate/{booking_id}/`  
  Initiates a Chapa transaction. Creates a `Payment` with `status=Pending`, stores `transaction_id (tx_ref)` and `checkout_url`, and sends a **payment email** with the link.

  **Response:**
  ```json
  {
    "checkout_url": "https://checkout.chapa.co/checkout/payment/xxxxx",
    "transaction_id": "b3f1e6f4-0c9d-4c4a-8f2b-..."
  }
  ```

- `GET /payments/verify/{tx_ref}/`  
  Verifies the transaction with Chapa. Updates `Payment.status` to `Completed`/`Failed`. On success, triggers **confirmation email** via Celery.

  **Success Response:**
  ```json
  { "message": "Payment successful and confirmed." }
  ```

- `GET /payments/success/`  
  Simple landing endpoint for `return_url` after user completes checkout (useful before the frontend exists).

**Callback & Return URLs (dev):**
- `callback_url`: `http://localhost:8000/api/payments/verify/{tx_ref}/`
- `return_url`: `http://localhost:8000/api/payments/success/`

> N.B. Always verify the final state server-side using the verification endpoint (`/payments/verify/{tx_ref}/`).

---

## 🔔 Email & Celery Tasks

- `send_payment_email(email, checkout_url)` – sent after payment initiation
- `send_payment_confirmation(email, booking_id)` – sent after successful verification

These run asynchronously using Celery’s `.delay(...)` to avoid blocking API requests.

---

## 🧪 Testing the Payment Flow (Chapa Sandbox)

1. Create a booking: `POST /bookings/`  
2. Initiate payment: `POST /payments/initiate/{booking_id}/` → get `checkout_url`  
3. Open the `checkout_url` in the browser and complete payment in Chapa Sandbox  
4. Chapa redirects to your `return_url` and calls your `callback_url`  
5. Your server verifies via `GET /payments/verify/{tx_ref}/` and updates `Payment.status`  
6. Confirm Celery emails in worker logs (or mailbox if SMTP configured)

> Capture logs/console output to include proof of initiation, verification, and model updates.

---

## 🔐 Authentication

This API supports DRF authentication (Basic/Session).  
Add token/session auth as needed for production.

---

## 🧰 Useful Scripts

```bash
# Run tests
python manage.py test

# Create superuser
python manage.py createsuperuser
```

---

## 📜 License

MIT License
