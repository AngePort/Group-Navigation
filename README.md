Driving Navigation App (prototype)

This is a minimal Python (Flask + SQLAlchemy) prototype for a Driving Navigation App focusing on a database of user profiles.

What you get
- Flask application factory in `app.py`
- SQLAlchemy setup in `db.py`
- `UserProfile` model in `models.py`
- CRUD endpoints in `routes.py` for user profiles
- Simple pytest tests in `tests/test_profiles.py`

Quick start (macOS / zsh)

1) Create and activate a virtualenv (optional but recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2) Install dependencies:

```bash
pip install -r requirements.txt
```

3) Run tests:

```bash
python3 -m pytest -q
```

4) Run the app locally:

```bash
python3 -m flask --app app:create_app run --host=127.0.0.1 --port=5000
```

Next steps
- Add authentication and secure endpoints
- Replace SQLite with Postgres for production
- Add navigation engine and map integration (Mapbox / Google Maps)
