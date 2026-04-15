# Matrimony Backend API

Production-style backend API for a matrimony platform with role-based workflows for users, community coordinators, community admins, and super admins.

## Overview

This project is a FastAPI + SQLAlchemy backend that supports:

- User onboarding and OTP-based verification
- Invite-based activation for admin/coordinator/member accounts
- JWT authentication and role-based authorization
- Profile completion (basic info, education, profession, lifestyle, family, horoscope, addresses)
- Community membership requests and coordinator review workflows
- Match feed, connection requests, favorites, blocking, and preferences
- Events, announcements, support tickets, and app feedback
- Media/document upload flows (Cloudinary)

## Tech Stack

- Python
- FastAPI
- SQLAlchemy ORM
- Pydantic
- PostgreSQL or SQLite (via DATABASE_URL)
- Redis (OTP, cooldown, rate limits, pending payloads)
- Twilio (SMS OTP)
- SMTP email (OTP/invite/reset flows)
- Cloudinary (profile/event/document media)
- JWT auth

## Project Structure

Key backend folders:

- `main.py` - FastAPI app entry point and router registration
- `database.py` - engine/session setup and DB dependency
- `routers/` - HTTP API routers
- `services/` - business logic
- `models/` - SQLAlchemy models
- `schemas/` - request/response Pydantic schemas
- `utils/` - auth, OTP, uploads, enums, helpers
- `crud/` - focused data-access helpers
- `scripts/` - bootstrap/seed utility scripts

## API Modules (Mounted in App)

The following routers are currently mounted in `main.py`:

- `/auth` - login, me, dashboard payload, invite/password flows
- `/users` - registration, profile completion, uploads, verification actions
- `/data` - countries/states/cities/universities/religions/castes/sub-castes
- `/super-admin` - community and community-admin setup
- `/community-admin` - coordinator management, events, members, announcements
- `/coordinator` - review pipelines, requests, member/docs oversight
- `/settings` - visibility, block/unblock, user preference
- `/feed` - suggestions, connections, communities, favorites, support/feedback
- `/events` - event listing/details for end users

Additional router files exist (for example analytics/suggestions/block/cities), but are not included in `main.py` yet.

## Local Setup

### 1. Prerequisites

- Python 3.11+
- Redis server (for OTP and temporary state)
- A running DB (PostgreSQL recommended, SQLite supported)

### 2. Create and activate virtual environment

Windows PowerShell:

```powershell
python -m venv env
.\env\Scripts\Activate.ps1
```

### 3. Install dependencies

Install from requirements:

```powershell
pip install -r requirements.txt
```

If your environment is missing runtime packages used in code, install these as well:

```powershell
pip install uvicorn python-jose[cryptography] passlib[bcrypt] redis twilio cloudinary
```

### 4. Configure environment variables

Create a `.env` file in the repo root.

Required/commonly used keys:

```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/matrimony_db

# Auth
SECRET_KEY=replace_with_secure_random_value
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Email (SMTP)
EMAIL_ADDRESS=your_email@example.com
EMAIL_PASSWORD=your_email_app_password

# Twilio (for phone OTP)
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_FROM=+10000000000

# Frontend links in action emails
FRONTEND_BASE_URL=http://127.0.0.1:3000

# Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### 5. Run the API

```powershell
uvicorn main:app --reload
```

Open docs:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Bootstrap and Utility Scripts

Useful scripts present in the repo:

- `add_super_admin.py` or `scripts/add_super_admin.py` - seed a super admin user
- `scripts/insert_countries.py`, `scripts/insert_states.py`, `scripts/insert_city.py` - location seeds
- `scripts/testdata.py` or `insert_script.py` - sample data population
- `scripts/verify_analytics.py` - analytics checks

Run a script with:

```powershell
python scripts/add_super_admin.py
```

## Authentication and Roles

- OAuth2 bearer token pattern is used in API security dependency flow.
- Login returns a JWT bearer access token.
- Role guards are implemented for:
	- super admin
	- community admin
	- coordinator
	- authenticated user

## Notes and Operational Tips

- CORS is currently open to all origins (`*`) in `main.py`; lock this down for production.
- `Base.metadata.create_all(bind=engine)` runs on startup. For mature environments, use migrations.
- The repository includes more dependencies than the API strictly needs. Keep requirements curated before production deployment.





