# KPL 7.0 Backend

Django REST Framework backend for the Sports Court Slot Booking System.

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py seed_kpl70
python manage.py runserver
```

Use PostgreSQL by setting `DATABASE_URL` in `.env`. If it is not set, Django falls back to a local SQLite database for development only.

Default seeded admin credentials come from `.env.example`:

- username: `admin`
- password: `admin12345`

## Main API

- `POST /api/auth/login/`
- `POST /api/auth/refresh/`
- `GET /api/auth/me/`
- `GET /api/admin/summary/`
- `GET|POST /api/admin/teams/`
- `GET|POST /api/admin/courts/`
- `GET|POST /api/admin/slots/`
- `GET|POST /api/admin/bookings/`
- `GET /api/owner/summary/`
- `GET /api/owner/slots/`
- `GET|POST /api/owner/bookings/`
