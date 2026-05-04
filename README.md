# Snip-Snap — UK Barbershop Discovery App

A web application for discovering local barbershops and barbers across the UK. Built as a Year 2 Software Engineering coursework project.

## Features

- **Interactive map** — Leaflet.js map showing barbershop locations across the UK with clickable pins
- **Discover feed** — Infinite-scroll gallery of barber posts sortable by closest, highest rated, most recent, or a blended algorithm (distance + rating + recency via PostGIS)
- **Search and filter** — Filter posts by tag, barber, or barbershop
- **Barber profiles** — Gallery, working hours timetable, and reviews with threaded replies
- **Barbershop profiles** — Shop info, opening hours aggregated from barber shifts, and gallery
- **Review system** — Star ratings with threaded barber replies, real-time submission
- **Barber dashboard** — Edit profile, manage timetable, upload posts and gallery photos, add social links
- **Authentication** — Email/password signup and login via Supabase Auth with role-based access (customer / barber)
- **Input sanitization** — Profanity filtering and type validation applied to all user-submitted text

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python / Flask |
| Database | PostgreSQL via Supabase (psycopg2 + SSL) |
| Spatial queries | PostGIS — ST_DistanceSphere for distance-based sorting |
| Auth | Supabase Auth (JWT) |
| Storage | Supabase Storage |
| Frontend | Vanilla JavaScript ES modules (no build step) |
| Map | Leaflet.js + OpenStreetMap tiles |
| Geocoding | Nominatim API + postcodes.io (postcode → lat/lng) |
| Templates | Jinja2 |

## Project Structure

```
app/
  routes.py               — page routes and form handlers
  api.py                  — REST API endpoints
  db.py                   — all database query functions
  input_sanitization.py   — sanitize_input() for user-submitted text
  auth.py                 — JWT verification
  supabase_storage.py     — image upload and signed URL generation
  access.py               — @login_required, @roles_required decorators
  static/
    js/
      pages/              — per-page JS entry points
      components/         — reusable UI components (map, reviews, timetable, gallery)
      features/           — feature modules (gallery edit, post upload, profile edit)
    css/
  templates/pages/        — Jinja2 HTML templates
scripts/
  seed_data.py            — seeds barbershops, barbers, customers, posts, reviews
  patch_seed_fixes.py     — adds coordinates, websites, gallery photos to seed data
  patch_reviews.py        — adds reviews, barber replies, and shop reviews
  rollback_seed.py        — removes all seed data
tests/
  test_sanitization.py    — 22 unit tests for sanitize_input()
  test_cursor.py          — 18 unit tests for _parse_cursor() and _make_next_cursor()
  test_label_picker.py    — 9 unit tests for _pick_label()
  manual_test_plan.xlsx   — complete manual test plan (3.4A)
  automated_test_plan.xlsx — automated test plan with pytest coverage report (3.4B)
```

## Setup

### Prerequisites
- Python 3.11+
- A Supabase project with PostgreSQL + PostGIS enabled

### Installation

```bash
# Clone the repository
git clone https://github.com/Cyrus0106/software-engineering-snip-snap.git
cd software-engineering-snip-snap

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_STORAGE_BUCKET=photos
DATABASE_URL=your_postgres_connection_string
FLASK_SECRET_KEY=your_secret_key
UNSPLASH_ACCESS_KEY=your_unsplash_key
```

### Running the App

```bash
flask run
```

The app will be available at `http://localhost:5000`.

### Seeding Test Data

```bash
# Full seed (run in order)
python scripts/seed_data.py
python scripts/patch_seed_fixes.py
python scripts/patch_reviews.py

# Remove all seed data
python scripts/rollback_seed.py
```

## Running Tests

```bash
pip install pytest pytest-cov
python -m pytest tests/ -v --cov=app.input_sanitization --cov-report=term-missing
```

**Result:** 49 tests, 100% coverage on all tested units.

## Known Unimplemented Features

The following were planned but deprioritised in favour of core functionality:

- **Google Login** — OAuth flow exists but Google provider not configured
- **Follow system** — `follow` table exists in DB, no UI or API built
- **Booking system** — timetable displays availability but booking is not implemented
- **Review helpful votes** — table exists in DB, no UI built
- **Services/skills listing** — deprioritised in favour of timetable editor
