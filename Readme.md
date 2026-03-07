# Chitara – AI Music Generation Platform

Exercise 3: Domain Layer Implementation (Django)

---

## Project Overview

Chitara is an AI-powered music generation web application. This repository contains the domain layer implementation built with Django, translated directly from the domain model defined in Exercise 2.

---

## Tech Stack

- Python 3.10
- Django 4.x
- SQLite (default development database)

---

## Project Structure

```
chitara/
├── chitara/          # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── music/            # Main domain app
│   ├── models.py     # Domain entities
│   ├── admin.py      # Admin CRUD interface
│   └── migrations/   # Database migrations
├── manage.py
└── README.md
```

---

## Setup Instructions

**1. Clone the repository**
```bash
git clone https://github.com/RiccardoMarioBonato/Chitara.git
cd chitara
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
pip install django
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
| `User` | A registered user who can generate, manage, and share songs |
| `Song` | An AI-generated music track with all generation parameters |
| `SingerModel` | A predefined AI vocal model selected during song generation |
| `Feedback` | User-submitted feedback collected after song generation |

### Enumerations

| Enum | Values |
|------|--------|
| `Genre` | JAZZ, POP, ELECTRONIC, CLASSICAL, ROCK, HIPHOP |
| `Mood` | CALM, HAPPY, ENERGETIC, ROMANTIC, SAD |
| `Occasion` | BIRTHDAY, WEDDING, GRADUATION, HOLIDAY, CASUAL |
| `Theme` | CHRISTMAS, HALLOWEEN, LOVE, SUMMER, MAGICAL |
| `GenerationStatus` | PENDING, GENERATING, COMPLETED, FAILED |

---

## CRUD Operations

CRUD functionality is demonstrated through the Django Admin interface at `/admin`.

All four operations are supported for every domain entity:
- **Create** – Add new Users, Songs, SingerModels, and Feedback via admin forms
- **Read** – Browse and search all records with filters
- **Update** – Edit any existing record
- **Delete** – Remove records individually or in bulk

---