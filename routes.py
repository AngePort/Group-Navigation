from flask import Blueprint, request, current_app
from db import get_db
from datetime import datetime
import folium
from folium import IFrame
import json

profiles_bp = Blueprint("profiles", __name__)


@profiles_bp.route("/", methods=["POST"])
def create_profile():
    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")

    if not username or not email:
        return {"error": "username and email are required"}, 400

    db = get_db()
    cur = db.cursor()
    # simple uniqueness checks
    cur.execute("SELECT id FROM user_profiles WHERE username = ?", (username,))
    if cur.fetchone():
        return {"error": "username already exists"}, 400
    cur.execute("SELECT id FROM user_profiles WHERE email = ?", (email,))
    if cur.fetchone():
        return {"error": "email already exists"}, 400

    created_at = datetime.utcnow().isoformat()
    cur.execute(
        "INSERT INTO user_profiles (username, email, full_name, vehicle_type, latitude, longitude, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (username, email, data.get("full_name"), data.get("vehicle_type"), data.get("latitude"), data.get("longitude"), created_at),
    )
    db.commit()
    pid = cur.lastrowid
    cur.execute("SELECT * FROM user_profiles WHERE id = ?", (pid,))
    row = cur.fetchone()
    return dict(row), 201


@profiles_bp.route("/", methods=["GET"])
def list_profiles():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM user_profiles")
    rows = cur.fetchall()
    return {"profiles": [dict(r) for r in rows]}


@profiles_bp.route("/<int:profile_id>", methods=["GET"])
def get_profile(profile_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM user_profiles WHERE id = ?", (profile_id,))
    row = cur.fetchone()
    if not row:
        return {"error": "not found"}, 404
    return dict(row)


@profiles_bp.route("/<int:profile_id>", methods=["PUT"])
def update_profile(profile_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM user_profiles WHERE id = ?", (profile_id,))
    row = cur.fetchone()
    if not row:
        return {"error": "not found"}, 404
    data = request.get_json() or {}
    full_name = data.get("full_name", row[3])
    vehicle_type = data.get("vehicle_type", row[4])
    latitude = data.get("latitude", row[5])
    longitude = data.get("longitude", row[6])
    cur.execute(
        "UPDATE user_profiles SET full_name = ?, vehicle_type = ?, latitude = ?, longitude = ? WHERE id = ?",
        (full_name, vehicle_type, latitude, longitude, profile_id),
    )
    db.commit()
    cur.execute("SELECT * FROM user_profiles WHERE id = ?", (profile_id,))
    updated = cur.fetchone()
    return dict(updated)


@profiles_bp.route("/map")
def show_map():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, username, full_name, latitude, longitude FROM user_profiles WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
    users = cur.fetchall()
    
    # Build markers JavaScript
    markers_js = ""
    for user in users:
        user_id, username, full_name, lat, lng = user
        name = full_name or username
        markers_js += f"""
        L.marker([{lat}, {lng}]).addTo(map)
            .bindPopup('{name} ({username})')
            .openPopup();
        """
    
    # Default center: first user or New York
    if users:
        center_lat, center_lng = users[0][3], users[0][4]
    else:
        center_lat, center_lng = 40.7128, -74.0060
    
    # Simple HTML with Leaflet map
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Group Navigation Map</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            #map {{ height: 600px; }}
        </style>
    </head>
    <body>
        <h1>Group Navigation Map</h1>
        <p>Showing locations of users with coordinates.</p>
        <div id="map"></div>
        <script>
            var map = L.map('map').setView([{center_lat}, {center_lng}], 10);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '© OpenStreetMap contributors'
            }}).addTo(map);
            {markers_js}
        </script>
    </body>
    </html>
    """
    return html


@profiles_bp.route("/test")
def test_route():
    return "Test route works!"
