# Chitara – AI Music Generation Platform

Exercise 3: Domain Layer Implementation (Django)

---

## Project Overview

Chitara is an AI-powered music generation web application. This repository contains the domain layer implementation built with Django, translated directly from the domain model defined in Exercise 2.

---

## Tech Stack

- Python 3.10+
- Django 4.x
- SQLite (default development database)

---

## Project Structure

```
Chitara/
├── chitara/          # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── music/            # Main domain app
│   ├── models.py     # Domain entities
│   ├── admin.py      # Admin CRUD interface
│   └── migrations/   # Database migrations
├── manage.py
├── requirements.txt
└── README.md
```

---

## Setup Instructions

**1. Clone the repository**
```bash
git clone https://github.com/RiccardoMarioBonato/Chitara.git
cd Chitara
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Apply migrations**
```bash
python manage.py migrate
```

**5. Create an admin user**
```bash
python manage.py createsuperuser
```

**6. Run the development server**
```bash
python manage.py runserver
```

**7. Open the admin panel**

Go to `http://127.0.0.1:8000/admin` and log in with your superuser credentials.

---

## Domain Models

| Model | Description |
|-------|-------------|
| `User` | Django built-in user model used for authentication and ownership |
| `Song` | An AI-generated music track with all generation parameters |
| `SingerModel` | A predefined AI vocal model selected during song generation |
| `Feedback` | User-submitted feedback collected after song generation |
| `Genre` | Reference model for musical genres (e.g. Jazz, Pop, Rock) |
| `Mood` | Reference model for emotional tone (e.g. Calm, Happy, Energetic) |
| `Occasion` | Reference model for song context (e.g. Birthday, Wedding) |
| `Theme` | Reference model for optional song tags (e.g. Christmas, Love) |

### Notes on Design Decisions

- **Genre, Mood, Occasion, Theme** are full Django Models so new values can be added via the admin panel without redeploying the application.
- **GenerationStatus** remains a `TextChoices` enum as it is a fixed, stable lifecycle state that will not change.
- **User** uses Django's built-in `auth.User` model to avoid redundancy with the framework's own authentication system.
- **Themes** use a `ManyToManyField` so a song can have zero or more themes without using a JSON field.

---

## CRUD Operations

CRUD functionality is demonstrated through the Django Admin interface at `/admin`.

All four operations are supported for every domain entity:
- **Create** – Add new records via admin forms
- **Read** – Browse and search all records with filters
- **Update** – Edit any existing record
- **Delete** – Remove records individually or in bulk