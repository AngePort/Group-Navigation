from flask import Blueprint, request, current_app
from db import get_db
from datetime import datetime
import folium
from folium import IFrame
import json
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash
from flask import redirect

profiles_bp = Blueprint("profiles", __name__)


@profiles_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login</title>
        </head>
        <body>
            <h1>Login</h1>
            <form action="/profiles/login" method="post">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" required><br>
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" required><br>
                <button type="submit">Login</button>
            </form>
        </body>
        </html>
        """
    
    # POST
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return {"error": "username and password required"}, 400
    
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, password_hash FROM user_profiles WHERE username = ?", (username,))
    row = cur.fetchone()
    if not row or not check_password_hash(row[1], password):
        return {"error": "invalid credentials"}, 401
    
    session['user_id'] = row[0]
    if request.is_json:
        return {"message": "logged in", "user_id": row[0]}
    else:
        return redirect("/profiles/map")


@profiles_bp.route("/logout", methods=["POST"])
def logout():
    session.pop('user_id', None)
    return {"message": "logged out"}


@profiles_bp.route("/me")
def get_me():
    user_id = session.get('user_id')
    if not user_id:
        return {"error": "not logged in"}, 401
    
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM user_profiles WHERE id = ?", (user_id,))
    row = cur.fetchone()
    if not row:
        return {"error": "user not found"}, 404
    return dict(row)


@profiles_bp.route("/", methods=["POST"])
def create_profile():
    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return {"error": "username, email, and password are required"}, 400

    db = get_db()
    cur = db.cursor()
    # simple uniqueness checks
    cur.execute("SELECT id FROM user_profiles WHERE username = ?", (username,))
    if cur.fetchone():
        return {"error": "username already exists"}, 400
    cur.execute("SELECT id FROM user_profiles WHERE email = ?", (email,))
    if cur.fetchone():
        return {"error": "email already exists"}, 400

    password_hash = generate_password_hash(password)
    created_at = datetime.utcnow().isoformat()
    cur.execute(
        "INSERT INTO user_profiles (username, email, password_hash, full_name, vehicle_type, latitude, longitude, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (username, email, password_hash, data.get("full_name"), data.get("vehicle_type"), data.get("latitude"), data.get("longitude"), created_at),
    )
    db.commit()
    pid = cur.lastrowid
    cur.execute("SELECT id, username, email, full_name, vehicle_type, latitude, longitude, created_at FROM user_profiles WHERE id = ?", (pid,))
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
    user_id = session.get('user_id')
    if not user_id or user_id != profile_id:
        return {"error": "unauthorized"}, 403
    
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
    cur.execute("SELECT id, username, email, full_name, vehicle_type, latitude, longitude, created_at FROM user_profiles WHERE id = ?", (profile_id,))
    updated = cur.fetchone()
    return dict(updated)


@profiles_bp.route("/map")
def show_map():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, username, full_name, latitude, longitude FROM user_profiles WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
    users = cur.fetchall()
    
    user_id = session.get('user_id')
    current_user = None
    if user_id:
        for u in users:
            if u[0] == user_id:
                current_user = u
                break
    
    # Build markers JavaScript
    markers_js = ""
    for user in users:
        uid, username, full_name, lat, lng = user
        name = full_name or username
        popup_text = f'{name} ({username})'
        if uid == user_id:
            popup_text += ' - YOU'
        markers_js += f"""
        L.marker([{lat}, {lng}]).addTo(map)
            .bindPopup('{popup_text}');
        """
    
    # Default center: current user, or first user, or New York
    if current_user:
        center_lat, center_lng = current_user[3], current_user[4]
    elif users:
        center_lat, center_lng = users[0][3], users[0][4]
    else:
        center_lat, center_lng = 40.7128, -74.0060
    
    # Simple HTML with Leaflet map
    logged_in_html = ""
    if user_id:
        logged_in_html = f"""
        <button id="updateLocationBtn">Update My Location</button>
        <p id="locationStatus"></p>
        """
    
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
        {logged_in_html}
        <div id="map"></div>
        <script>
            var map = L.map('map').setView([{center_lat}, {center_lng}], 10);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '© OpenStreetMap contributors'
            }}).addTo(map);
            {markers_js}
            
            // Update location function
            document.getElementById('updateLocationBtn')?.addEventListener('click', function() {{
                if (navigator.geolocation) {{
                    navigator.geolocation.getCurrentPosition(function(position) {{
                        const lat = position.coords.latitude;
                        const lng = position.coords.longitude;
                        document.getElementById('locationStatus').textContent = 'Updating location...';
                        
                        fetch('/profiles/{user_id}', {{
                            method: 'PUT',
                            headers: {{
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify({{ latitude: lat, longitude: lng }}),
                        }})
                        .then(response => response.json())
                        .then(data => {{
                            document.getElementById('locationStatus').textContent = 'Location updated! Refresh the page to see changes.';
                        }})
                        .catch(error => {{
                            document.getElementById('locationStatus').textContent = 'Error updating location.';
                            console.error('Error:', error);
                        }});
                    }}, function(error) {{
                        document.getElementById('locationStatus').textContent = 'Unable to retrieve your location.';
                    }});
                }} else {{
                    document.getElementById('locationStatus').textContent = 'Geolocation is not supported by this browser.';
                }}
            }});
        </script>
    </body>
    </html>
    """
    return html


@profiles_bp.route("/test")
def test_route():
    return "Test route works!"
