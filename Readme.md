# Chitara — AI Music Generation Platform

A Django 5.2 web application for generating AI-powered music using the Strategy Pattern, supporting both a local mock backend and the real Suno API.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, Django 5.2 |
| Auth | django-allauth 0.61+ (username/email + Google OAuth) |
| Database | SQLite (development) |
| HTTP | requests, gunicorn |
| Crypto | cryptography, PyJWT |
| Config | python-dotenv |

---

## Quickstart — Docker (recommended)

**One command to build, migrate, seed data, and start:**

```bash
docker compose up --build
```

Then open: [http://localhost:8000](http://localhost:8000)

The container automatically:
1. Runs all database migrations
2. Seeds Genres, Moods, Occasions, Themes
3. Seeds SingerModels (Soprano, Alto, Tenor, etc.)
4. Starts the development server on port 8000

To stop:
```bash
docker compose down
```

---

## Environment Variables

Copy `.env.example` to `chitara/.env` and fill in your values:

```bash
cp chitara/.env.example chitara/.env
```

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GENERATOR_STRATEGY` | No | `mock` | `mock` for offline dev, `suno` for real API |
| `SUNO_API_KEY` | If Suno | — | API key from sunoapi.org |
| `SUNO_CALLBACK_URL` | If Suno | — | Your ngrok HTTPS URL + `/songs/api/callback/` |
| `SUNO_API_BASE_URL` | No | `https://api.sunoapi.org/api/v1` | Suno endpoint |
| `SUNO_API_TIMEOUT` | No | `30` | Request timeout in seconds |
| `GOOGLE_CLIENT_ID` | No | — | Google OAuth app client ID |
| `GOOGLE_CLIENT_SECRET` | No | — | Google OAuth app client secret |

---

## Manual Setup (without Docker)

```bash
cd chitara

python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt

python manage.py migrate
python populate_initial_data.py
python populate_suno_models.py

python manage.py createsuperuser   # optional admin account
python manage.py runserver
```

---

## Project Structure

```
Chitara/
├── Dockerfile
├── docker-compose.yml
├── docker-entrypoint.sh
├── Readme.md
└── chitara/
    ├── manage.py
    ├── requirements.txt
    ├── .env                        # local secrets — never commit
    ├── .env.example
    ├── populate_initial_data.py    # seeds Genres, Moods, Occasions, Themes
    ├── populate_suno_models.py     # seeds SingerModels
    ├── demo_strategy.py            # strategy pattern demo script
    ├── chitara/                    # Django project settings
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    └── music/                      # main app
        ├── models.py
        ├── views.py
        ├── urls.py
        ├── forms.py
        ├── services.py
        ├── repositories.py
        ├── suno_client.py
        ├── strategies/
        │   ├── base.py             # abstract SongGeneratorStrategy
        │   ├── factory.py          # StrategyFactory
        │   ├── mock_strategy.py    # offline / deterministic
        │   ├── suno_strategy.py    # real Suno API
        │   └── exceptions.py
        └── templates/
```

---

## Domain Models

| Model | Description |
|-------|-------------|
| `Song` | AI-generated track with all generation parameters |
| `SingerModel` | Vocal type selected during generation (Soprano, Alto, etc.) |
| `Genre` | Musical genre (Pop, Rock, Jazz, …) |
| `Mood` | Emotional tone (Happy, Energetic, Calm, …) |
| `Occasion` | Song context (Party, Wedding, Workout, …) |
| `Theme` | Optional tag, many-to-many with Song (Summer, Love, …) |
| `Feedback` | User-submitted feedback after generation |

Admin panel at `/admin` supports full CRUD on all models.

---

## Strategy Pattern (Song Generation)

Song generation is decoupled from the rest of the app via the Strategy Pattern.

| Strategy | Class | Use when |
|----------|-------|----------|
| Mock | `MockSongGeneratorStrategy` | Local dev, offline, testing |
| Suno | `SunoSongGeneratorStrategy` | Real AI generation via sunoapi.org |

Switch strategy with one line in `.env`:

```env
GENERATOR_STRATEGY=mock   # or: suno
```

```
SongGeneratorStrategy (ABC)
├── MockSongGeneratorStrategy   → instant, deterministic
└── SunoSongGeneratorStrategy   → async polling, real API

StrategyFactory.get_strategy() → correct instance based on env var
```

### Suno Setup (real API)

Suno's callback requires HTTPS, so use ngrok locally:

```bash
# Terminal 1
ngrok http 8000
# copy the https URL, e.g. https://abc123.ngrok-free.app

# .env
GENERATOR_STRATEGY=suno
SUNO_API_KEY=your_key_here
SUNO_CALLBACK_URL=https://abc123.ngrok-free.app/songs/api/callback/

# Terminal 2
docker compose up --build
```

---

## URL Map

| URL | Description |
|-----|-------------|
| `/` | Landing page |
| `/accounts/login/` | Login (username/email or Google) |
| `/songs/` | Your song library |
| `/songs/generate/` | Generate a new song |
| `/songs/<pk>/` | Song detail / status |
| `/songs/shared/<id>/` | Publicly shared song (no login) |
| `/songs/feedback/` | Submit feedback |
| `/songs/api/callback/` | Suno webhook endpoint |
| `/admin/` | Django admin |

---

## Running the Strategy Demo

```bash
cd chitara
python demo_strategy.py
```

Prints Mock output, Factory selection, and (if `SUNO_API_KEY` is set) a live Suno call.
