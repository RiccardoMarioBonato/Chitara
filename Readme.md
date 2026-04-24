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

---

## Exercise 4 — Strategy Pattern (Song Generation)

### Overview

Song generation uses the **Strategy design pattern** to decouple the
generation backend from the rest of the application. Two strategies are
implemented:

| Strategy | Class | When to use |
|----------|-------|-------------|
| Mock | `MockSongGeneratorStrategy` | Local development, testing, offline |
| Suno | `SunoSongGeneratorStrategy` | Real AI music generation via sunoapi.org |

Both strategies inherit from the abstract base class `SongGeneratorStrategy`
(defined in `music/strategies/base.py`), which enforces the common interface
via Python's `abc.ABC` and `@abstractmethod`.

### How to Switch Strategy

Strategy selection is controlled by the `GENERATOR_STRATEGY` environment
variable in your `.env` file. It is **never hard-coded** in source files.

**Run in Mock mode (offline, no API key needed):**

```env
# .env
GENERATOR_STRATEGY=mock
```

**Run in Suno mode (real API, requires API key + ngrok):**

```env
# .env
GENERATOR_STRATEGY=suno
SUNO_API_KEY=your_suno_api_key_here
SUNO_CALLBACK_URL=https://your-ngrok-url.ngrok-free.app/generation/suno/callback/
```

Restart Django after changing `.env`:

```bash
python manage.py runserver
```

### Setting Up the Suno API Key

1. Register at [https://sunoapi.org](https://sunoapi.org) to get your API key.
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Set `SUNO_API_KEY=<your key>` in `.env`.
4. **Never commit `.env` to Git.** It is listed in `.gitignore`.

For local HTTPS (required by Suno's callback):

```bash
# Terminal 1 -- run ngrok
ngrok http 8000

# Copy the HTTPS URL (e.g. https://abc123.ngrok-free.app)
# Set in .env:
SUNO_CALLBACK_URL=https://abc123.ngrok-free.app/generation/suno/callback/

# Terminal 2 -- run Django
python manage.py runserver
```

### Strategy Architecture

```
music/strategies/
├── __init__.py         # Package marker
├── base.py             # Abstract base class (SongGeneratorStrategy)
├── exceptions.py       # SunoOfflineError, SunoInsufficientCreditsError
├── mock_strategy.py    # Strategy A -- offline, instant, deterministic
├── suno_strategy.py    # Strategy B -- real Suno API, async polling
└── factory.py          # StrategyFactory (reads GENERATOR_STRATEGY env var)
```

The `StrategyFactory.get_strategy()` method is the single point of
strategy selection. Controllers and services never instantiate strategies
directly -- they always go through the factory.

### Running the Demo

```bash
cd chitara
python demo_strategy.py
```

This script:
- Demonstrates Mock strategy (always works, no API key needed)
- Demonstrates Factory correctly selecting each strategy
- Attempts a live Suno API call (if `SUNO_API_KEY` is set)
- Prints output suitable for submission as grading evidence

### Strategy Pattern Class Diagram

```
SongGeneratorStrategy (ABC)
  └── generate(song_request) [abstract]

MockSongGeneratorStrategy(SongGeneratorStrategy)
  └── generate(song_request) -> {status: "SUCCESS", audio_url: "...", ...}

SunoSongGeneratorStrategy(SongGeneratorStrategy)
  └── generate(song_request, song_instance=None) -> {status: "PENDING", task_id: "...", ...}
      └── _poll_until_done(task_id, song_instance)  [background thread]

StrategyFactory
  └── get_strategy(force_mock=False) -> SongGeneratorStrategy instance
```