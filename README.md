Driving Navigation App (prototype)

This is a minimal Python (Flask + SQLAlchemy) prototype for a Driving Navigation App focusing on a database of user profiles.

What you get
- Flask application factory in `app.py`
- SQLite database setup in `db.py`
- User profiles table and CRUD operations in `routes.py`
- Interactive map using Folium and OpenStreetMap
- Simple pytest tests in `tests/test_profiles.py`

API endpoints
- `GET /` - Health check
- `POST /profiles/` - Create profile (json: username, email, full_name?, vehicle_type?, latitude?, longitude?)
- `GET /profiles/` - List all profiles
- `GET /profiles/<id>` - Get profile by ID
- `PUT /profiles/<id>` - Update profile (json: full_name?, vehicle_type?, latitude?, longitude?)
- `DELETE /profiles/<id>` - Delete profile by ID
- `GET /profiles/map` - View interactive navigation map with user locations

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
