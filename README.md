# 🌍 ALX Travel App

A Django-based travel booking platform that allows users to browse listings, book trips, and leave reviews. This project was built as part of the ALX Backend Specialization program to demonstrate proficiency in Django, REST APIs, Celery, and background task management.

---

**Version:** v1  
**Description:** RESTful API for managing travel listings, bookings, and reviews in the ALX Travel project.

---

## 📌 Base URL

```
http://127.0.0.1:8000/api/
```

## 🚀 Features

- User registration & authentication
- Create, browse, and manage travel listings
- Book listings and leave 1–5 star reviews
- Background tasks using Celery (e.g. sending confirmation emails)
- Environment variable management with `django-environ`

---

## 🏗 Tech Stack

- **Backend:** Django, Django REST Framework
- **Task Queue:** Celery with RabbitMQ or Redis (via `pika`)
- **Environment Management:** `django-environ`, `.env`
- **Fake Data Generation:** `Faker`
- **Database:** SQLite (default) or PostgreSQL

---

## 📦 Installation

```bash
# Clone the repo
git clone https://github.com/Loutimi/alx_travel_app_0x00.git
cd alx_travel_app_0x00

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

---

## 🔐 Authentication

This API uses **Basic Authentication**. Include your credentials in the request header.

Example:
```
Authorization: Basic <base64encoded(username:password)>
```

---

## 📂 Endpoints

### 🧳 Bookings

#### `GET /bookings/`
Retrieve all bookings.

**Responses:**
- `200 OK`: Returns list of bookings.

#### `POST /bookings/`
Create a new booking.

**Request Body Example:**
```json
{
  "user": 1,
  "listing": 3,
  "start_date": "2025-08-03",
  "end_date": "2025-08-07"
}
```

**Responses:**
- `201 Created`: Booking successfully created.

#### `GET /bookings/{booking_id}/`
Retrieve a specific booking.

**Responses:**
- `200 OK`: Returns booking data.
- `404 Not Found`: Booking not found.

#### `PUT /bookings/{booking_id}/`
Update a booking entirely.

**Request Body Example:**
```json
{
  "user": 1,
  "listing": 3,
  "start_date": "2025-08-10",
  "end_date": "2025-08-15"
}
```

**Responses:**
- `200 OK`: Booking updated.

#### `PATCH /bookings/{booking_id}/`
Partially update a booking.

**Request Body Example:**
```json
{
  "end_date": "2025-08-12"
}
```

**Responses:**
- `200 OK`: Booking partially updated.

#### `DELETE /bookings/{booking_id}/`
Delete a booking.

**Responses:**
- `204 No Content`: Booking deleted.

---

### 🏡 Listings

#### `GET /listings/`
Retrieve all listings.

**Responses:**
- `200 OK`: Returns list of listings.

#### `POST /listings/`
Create a new listing.

**Request Body Example:**
```json
{
  "title": "Beachside Bungalow",
  "description": "Beautiful sea view, 2-bedroom bungalow.",
  "price_per_night": 120.00,
  "location": "Lagos, Nigeria"
}
```

**Responses:**
- `201 Created`: Listing created.

#### `GET /listings/{listing_id}/`
Retrieve a specific listing.

**Responses:**
- `200 OK`: Returns listing.
- `404 Not Found`: Listing not found.

#### `PUT /listings/{listing_id}/`
Update a listing.

**Request Body Example:**
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "price_per_night": 150.00,
  "location": "Abuja"
}
```

**Responses:**
- `200 OK`: Listing updated.

#### `PATCH /listings/{listing_id}/`
Partially update a listing.

**Request Body Example:**
```json
{
  "price_per_night": 100.00
}
```

**Responses:**
- `200 OK`: Listing partially updated.

#### `DELETE /listings/{listing_id}/`
Delete a listing.

**Responses:**
- `204 No Content`: Listing deleted.

---

### 📝 Reviews

#### `GET /reviews/`
Retrieve all reviews.

**Responses:**
- `200 OK`: List of reviews.

#### `POST /reviews/`
Create a new review.

**Request Body Example:**
```json
{
  "user": 2,
  "listing": 3,
  "rating": 4,
  "comment": "Great experience!"
}
```

**Responses:**
- `201 Created`: Review created.
