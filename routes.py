from flask import Blueprint, request, current_app
from db import get_db
from datetime import datetime
import folium
from folium import IFrame
import json
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash
from flask import redirect
from flask_socketio import emit, join_room, leave_room

# Global dictionary to track connected users and their locations
connected_users = {}

profiles_bp = Blueprint("profiles", __name__)


@profiles_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 50px; }
                .container { max-width: 400px; }
                a { color: blue; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Login</h1>
                <form action="/profiles/login" method="post">
                    <label for="username">Username:</label><br>
                    <input type="text" id="username" name="username" required><br><br>
                    <label for="password">Password:</label><br>
                    <input type="password" id="password" name="password" required><br><br>
                    <button type="submit">Login</button>
                </form>
                <p>Don't have an account? <a href="/profiles/register">Create one here</a></p>
            </div>
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


@profiles_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Create Account</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 50px; }
                .container { max-width: 400px; }
                input { padding: 5px; margin: 5px 0 15px 0; width: 100%; }
                button { padding: 10px 20px; background-color: #4CAF50; color: white; border: none; cursor: pointer; }
                button:hover { background-color: #45a049; }
                .error { color: red; }
                a { color: blue; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Create Account</h1>
                <form action="/profiles/register" method="post">
                    <label for="username">Username:</label><br>
                    <input type="text" id="username" name="username" required><br>
                    
                    <label for="email">Email:</label><br>
                    <input type="email" id="email" name="email" required><br>
                    
                    <label for="password">Password:</label><br>
                    <input type="password" id="password" name="password" required><br>
                    
                    <label for="full_name">Full Name (optional):</label><br>
                    <input type="text" id="full_name" name="full_name"><br>
                    
                    <label for="vehicle_type">Vehicle Type (optional):</label><br>
                    <input type="text" id="vehicle_type" name="vehicle_type" placeholder="e.g., Car, Truck, Motorcycle"><br>
                    
                    <button type="submit">Create Account</button>
                </form>
                <p>Already have an account? <a href="/profiles/login">Login here</a></p>
            </div>
        </body>
        </html>
        """
    
    # POST - Register new user
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    full_name = data.get("full_name", "")
    vehicle_type = data.get("vehicle_type", "")
    
    # Validation
    if not username or not email or not password:
        if request.is_json:
            return {"error": "username, email, and password are required"}, 400
        else:
            return """
            <!DOCTYPE html>
            <html>
            <body>
                <h1 class="error">Error: username, email, and password are required</h1>
                <a href="/profiles/register">Go back</a>
            </body>
            </html>
            """, 400
    
    db = get_db()
    cur = db.cursor()
    
    # Check if username already exists
    cur.execute("SELECT id FROM user_profiles WHERE username = ?", (username,))
    if cur.fetchone():
        error_msg = "username already exists"
        if request.is_json:
            return {"error": error_msg}, 400
        else:
            return f"""
            <!DOCTYPE html>
            <html>
            <body>
                <h1 style="color: red;">{error_msg}</h1>
                <a href="/profiles/register">Go back</a>
            </body>
            </html>
            """, 400
    
    # Check if email already exists
    cur.execute("SELECT id FROM user_profiles WHERE email = ?", (email,))
    if cur.fetchone():
        error_msg = "email already exists"
        if request.is_json:
            return {"error": error_msg}, 400
        else:
            return f"""
            <!DOCTYPE html>
            <html>
            <body>
                <h1 style="color: red;">{error_msg}</h1>
                <a href="/profiles/register">Go back</a>
            </body>
            </html>
            """, 400
    
    # Create new user
    password_hash = generate_password_hash(password)
    created_at = datetime.utcnow().isoformat()
    
    try:
        cur.execute(
            "INSERT INTO user_profiles (username, email, password_hash, full_name, vehicle_type, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (username, email, password_hash, full_name, vehicle_type, created_at),
        )
        db.commit()
        user_id = cur.lastrowid
        
        if request.is_json:
            return {"message": "account created successfully", "user_id": user_id}, 201
        else:
            # Auto-login after registration
            session['user_id'] = user_id
            return redirect("/profiles/map")
    except Exception as e:
        db.rollback()
        if request.is_json:
            return {"error": str(e)}, 500
        else:
            return f"""
            <!DOCTYPE html>
            <html>
            <body>
                <h1 style="color: red;">Error creating account: {str(e)}</h1>
                <a href="/profiles/register">Go back</a>
            </body>
            </html>
            """, 500


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
    user_id = session.get('user_id')
    if not user_id:
        return redirect("/profiles/login")
    
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT username, full_name FROM user_profiles WHERE id = ?", (user_id,))
    user_info = cur.fetchone()
    if not user_info:
        return redirect("/profiles/login")
    
    username = user_info[0]
    full_name = user_info[1] or username
    
    # Get all users with locations
    cur.execute("SELECT id, username, full_name, latitude, longitude FROM user_profiles WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
    users = cur.fetchall()
    
    # Default center
    center_lat, center_lng = 40.7128, -74.0060
    if users:
        center_lat, center_lng = users[0][3], users[0][4]
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Real-Time Group Navigation</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 10px; }}
            #map {{ height: 600px; margin-top: 10px; }}
            #info {{ background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 10px; }}
            .status {{ color: green; font-weight: bold; }}
            .error {{ color: red; }}
            h1 {{ margin: 0 0 5px 0; }}
            p {{ margin: 5px 0; }}
        </style>
    </head>
    <body>
        <h1>Real-Time Group Navigation</h1>
        <div id="info">
            <p><strong>User:</strong> {full_name} ({username})</p>
            <p id="locationStatus" class="status">Connecting...</p>
            <p id="userCount">Connected users: 0</p>
        </div>
        <div id="map"></div>
        
        <script>
            const userId = {user_id};
            const username = '{username}';
            const fullName = '{full_name}';
            
            console.log('Map page loaded. User ID:', userId);
            
            // Initialize map
            var map = L.map('map').setView([{center_lat}, {center_lng}], 10);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '© OpenStreetMap contributors'
            }}).addTo(map);
            
            // Store markers
            var markers = {{}};
            var watchId = null;
            
            // Connect to WebSocket
            console.log('Attempting to connect to WebSocket...');
            const socket = io(window.location.origin, {{
                reconnection: true,
                reconnectionDelay: 1000,
                reconnectionDelayMax: 5000,
                reconnectionAttempts: 5
            }});
            
            socket.on('connect', function() {{
                console.log('✓ WebSocket connected! Socket ID:', socket.id);
                document.getElementById('locationStatus').textContent = 'Connected to server...';
                
                // Emit join_tracking event
                socket.emit('join_tracking', {{
                    user_id: userId,
                    username: username,
                    full_name: fullName
                }});
                console.log('Emitted join_tracking event');
                
                // Start tracking location
                if (navigator.geolocation) {{
                    console.log('Geolocation available, starting watch...');
                    watchId = navigator.geolocation.watchPosition(
                        function(position) {{
                            const lat = position.coords.latitude;
                            const lng = position.coords.longitude;
                            const accuracy = position.coords.accuracy;
                            
                            console.log('Location received:', lat, lng, 'Accuracy:', accuracy);
                            
                            // Send location to server
                            socket.emit('update_location', {{
                                latitude: lat,
                                longitude: lng
                            }});
                            
                            document.getElementById('locationStatus').textContent = 'Real-time tracking active ✓';
                        }},
                        function(error) {{
                            console.error('Geolocation error:', error);
                            document.getElementById('locationStatus').textContent = 'Geolocation error: ' + error.message;
                        }},
                        {{
                            enableHighAccuracy: true,
                            timeout: 10000,
                            maximumAge: 0
                        }}
                    );
                }} else {{
                    document.getElementById('locationStatus').textContent = 'Geolocation not supported';
                }}
            }});
            
            socket.on('connect_error', function(error) {{
                console.error('✗ WebSocket connection error:', error);
                document.getElementById('locationStatus').textContent = 'Connection error: ' + error;
            }});
            
            socket.on('user_count', function(count) {{
                console.log('User count update:', count);
                document.getElementById('userCount').textContent = 'Connected users: ' + count;
            }});
            
            socket.on('location_update', function(data) {{
                console.log('Location update received:', data);
                const {{user_id, username, full_name, latitude, longitude}} = data;
                const name = full_name || username;
                const isCurrentUser = user_id === userId;
                
                // Remove old marker if exists
                if (markers[user_id]) {{
                    map.removeLayer(markers[user_id]);
                    console.log('Removed old marker for user', user_id);
                }}
                
                // Create custom blue dot for current user
                let markerIcon;
                if (isCurrentUser) {{
                    markerIcon = L.divIcon({{
                        className: 'custom-marker',
                        html: `<div style="
                            background-color: #2196F3;
                            width: 20px;
                            height: 20px;
                            border-radius: 50%;
                            border: 3px solid white;
                            box-shadow: 0 0 10px rgba(33, 150, 243, 0.7);
                            cursor: pointer;
                        "></div>`,
                        iconSize: [20, 20],
                        iconAnchor: [10, 10],
                        popupAnchor: [0, -10]
                    }});
                }} else {{
                    markerIcon = L.icon({{
                        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/red-marker.png',
                        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                        iconSize: [25, 41],
                        iconAnchor: [12, 41],
                        popupAnchor: [1, -34],
                        shadowSize: [41, 41]
                    }});
                }}
                
                const popup = isCurrentUser ? name + ' (YOU - BLUE DOT)' : name;
                markers[user_id] = L.marker([latitude, longitude], {{icon: markerIcon}})
                    .bindPopup(popup)
                    .addTo(map);
                    
                console.log('Added marker for user:', name, 'at', latitude, longitude);
            }});
            
            socket.on('disconnect', function() {{
                console.log('✗ WebSocket disconnected');
                document.getElementById('locationStatus').textContent = 'Disconnected';
                if (watchId !== null) {{
                    navigator.geolocation.clearWatch(watchId);
                }}
            }});
            
            window.addEventListener('beforeunload', function() {{
                if (watchId !== null) {{
                    navigator.geolocation.clearWatch(watchId);
                }}
            }});
        </script>
    </body>
    </html>
    """


@profiles_bp.route("/test")
def test_route():
    return "Test route works!"


@profiles_bp.route("/admin")
def admin_dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect("/profiles/login")
    
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT is_admin FROM user_profiles WHERE id = ?", (user_id,))
    user = cur.fetchone()
    if not user or not user[0]:
        return {"error": "access denied - admin only"}, 403
    
    # Get all users
    cur.execute("SELECT id, username, email, full_name, vehicle_type, latitude, longitude, is_admin, created_at FROM user_profiles ORDER BY created_at DESC")
    users = cur.fetchall()
    users_list = [dict(u) for u in users]
    
    # Build HTML table
    users_html = ""
    for u in users_list:
        admin_badge = " (ADMIN)" if u['is_admin'] else ""
        users_html += f"""
        <tr>
            <td>{u['id']}</td>
            <td>{u['username']}{admin_badge}</td>
            <td>{u['email']}</td>
            <td>{u['full_name'] or 'N/A'}</td>
            <td>{u['vehicle_type'] or 'N/A'}</td>
            <td>
                <a href="/profiles/admin/edit/{u['id']}">Edit</a> |
                <a href="/profiles/admin/delete/{u['id']}" onclick="return confirm('Are you sure you want to delete this user?')">Delete</a>
            </td>
        </tr>
        """
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            table, th, td {{ border: 1px solid black; padding: 8px; text-align: left; }}
            th {{ background-color: #4CAF50; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            a {{ color: blue; text-decoration: none; margin: 0 5px; }}
            a:hover {{ text-decoration: underline; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Admin Dashboard</h1>
            <div>
                <a href="/profiles/map">View Map</a> | 
                <a href="/profiles/logout" onclick="this.form.submit()">Logout</a>
            </div>
        </div>
        
        <h2>User Management</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>Username</th>
                <th>Email</th>
                <th>Full Name</th>
                <th>Vehicle Type</th>
                <th>Actions</th>
            </tr>
            {users_html}
        </table>
    </body>
    </html>
    """


@profiles_bp.route("/admin/edit/<int:profile_id>", methods=["GET", "POST"])
def admin_edit_user(profile_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect("/profiles/login")
    
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT is_admin FROM user_profiles WHERE id = ?", (user_id,))
    user = cur.fetchone()
    if not user or not user[0]:
        return {"error": "access denied - admin only"}, 403
    
    if request.method == "GET":
        cur.execute("SELECT id, username, email, full_name, vehicle_type, latitude, longitude, is_admin FROM user_profiles WHERE id = ?", (profile_id,))
        target_user = cur.fetchone()
        if not target_user:
            return {"error": "user not found"}, 404
        
        user_data = dict(target_user)
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Edit User</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 50px; }}
                .container {{ max-width: 500px; }}
                input, textarea {{ width: 100%; padding: 8px; margin: 5px 0 15px 0; box-sizing: border-box; }}
                button {{ padding: 10px 20px; background-color: #4CAF50; color: white; border: none; cursor: pointer; }}
                button:hover {{ background-color: #45a049; }}
                label {{ display: block; font-weight: bold; margin-top: 10px; }}
                .checkbox {{ width: auto; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Edit User: {user_data['username']}</h1>
                <form action="/profiles/admin/edit/{profile_id}" method="post">
                    <label>Username:</label>
                    <input type="text" name="username" value="{user_data['username']}" readonly>
                    
                    <label>Email:</label>
                    <input type="email" name="email" value="{user_data['email']}" required>
                    
                    <label>Full Name:</label>
                    <input type="text" name="full_name" value="{user_data['full_name'] or ''}">
                    
                    <label>Vehicle Type:</label>
                    <input type="text" name="vehicle_type" value="{user_data['vehicle_type'] or ''}">
                    
                    <label>Latitude:</label>
                    <input type="number" name="latitude" step="0.0001" value="{user_data['latitude'] or ''}">
                    
                    <label>Longitude:</label>
                    <input type="number" name="longitude" step="0.0001" value="{user_data['longitude'] or ''}">
                    
                    <label>
                        <input type="checkbox" name="is_admin" class="checkbox" {"checked" if user_data['is_admin'] else ""}>
                        Admin User
                    </label><br>
                    
                    <button type="submit">Save Changes</button>
                    <a href="/profiles/admin">Cancel</a>
                </form>
            </div>
        </body>
        </html>
        """
    
    # POST - Update user
    data = request.form
    email = data.get("email")
    full_name = data.get("full_name", "")
    vehicle_type = data.get("vehicle_type", "")
    latitude = data.get("latitude") or None
    longitude = data.get("longitude") or None
    is_admin = 1 if data.get("is_admin") else 0
    
    cur.execute(
        "UPDATE user_profiles SET email = ?, full_name = ?, vehicle_type = ?, latitude = ?, longitude = ?, is_admin = ? WHERE id = ?",
        (email, full_name, vehicle_type, latitude, longitude, is_admin, profile_id),
    )
    db.commit()
    return redirect("/profiles/admin")


@profiles_bp.route("/admin/delete/<int:profile_id>", methods=["GET"])
def admin_delete_user(profile_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect("/profiles/login")
    
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT is_admin FROM user_profiles WHERE id = ?", (user_id,))
    user = cur.fetchone()
    if not user or not user[0]:
        return {"error": "access denied - admin only"}, 403
    
    # Prevent self-deletion
    if profile_id == user_id:
        return {"error": "cannot delete your own account"}, 400
    
    cur.execute("DELETE FROM user_profiles WHERE id = ?", (profile_id,))
    db.commit()
    return redirect("/profiles/admin")


# ============================================================================
# WEBSOCKET EVENTS FOR REAL-TIME LOCATION TRACKING
# ============================================================================

# Track socket connections to users
socket_to_user = {}  # Maps socket ID to user ID

def get_socketio():
    """Get the SocketIO instance from the app context"""
    from app import create_app
    app, socketio = create_app()
    return socketio

socketio = None

def init_socketio(sio):
    """Initialize WebSocket handlers"""
    print("[SocketIO] Registering WebSocket event handlers...")
    
    @sio.on('connect')
    def on_connect():
        from flask import request
        print(f"[SocketIO] NEW CONNECTION: {request.sid}")
    
    @sio.on('join_tracking')
    def on_join_tracking(data):
        """Handle user joining the real-time tracking"""
        from flask import request
        
        user_id = data.get('user_id')
        username = data.get('username')
        full_name = data.get('full_name')
        socket_id = request.sid
        
        print(f"[SocketIO] JOIN_TRACKING: User {username} (ID: {user_id}), Socket: {socket_id}")
        
        # Bind this socket to the user
        socket_to_user[socket_id] = user_id
        
        # Store user connection
        connected_users[user_id] = {
            'socket_id': socket_id,
            'username': username,
            'full_name': full_name,
            'latitude': None,
            'longitude': None
        }
        
        print(f"[SocketIO] Total connected users: {len(connected_users)}")
        
        # Notify all users about connection count
        sio.emit('user_count', len(connected_users), broadcast=True)
    
    @sio.on('update_location')
    def on_update_location(data):
        """Handle real-time location updates"""
        from flask import request
        
        socket_id = request.sid
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        # Find the user ID for this socket
        user_id = socket_to_user.get(socket_id)
        
        if user_id is None:
            print(f"[SocketIO] ERROR: Location update from unknown socket: {socket_id}")
            return
        
        if user_id not in connected_users:
            print(f"[SocketIO] ERROR: User ID {user_id} not in connected_users")
            return
        
        user_data = connected_users[user_id]
        
        # Update database
        db = get_db()
        cur = db.cursor()
        cur.execute("UPDATE user_profiles SET latitude = ?, longitude = ? WHERE id = ?", 
                   (latitude, longitude, user_id))
        db.commit()
        
        # Update our tracking dict
        user_data['latitude'] = latitude
        user_data['longitude'] = longitude
        
        print(f"[SocketIO] Location update: {user_data['username']} -> ({latitude}, {longitude})")
        
        # Broadcast update to all connected clients
        sio.emit('location_update', {
            'user_id': user_id,
            'username': user_data['username'],
            'full_name': user_data['full_name'],
            'latitude': latitude,
            'longitude': longitude
        }, broadcast=True)
    
    @sio.on('disconnect')
    def on_disconnect():
        """Handle user disconnection"""
        from flask import request
        
        socket_id = request.sid
        user_id = socket_to_user.get(socket_id)
        
        if user_id and user_id in connected_users:
            username = connected_users[user_id]['username']
            del connected_users[user_id]
            del socket_to_user[socket_id]
            print(f"[SocketIO] User {username} disconnected. Remaining: {len(connected_users)}")
        else:
            print(f"[SocketIO] Socket {socket_id} disconnected.")
        
        # Notify all users about connection count
        sio.emit('user_count', len(connected_users), broadcast=True)
    
    print("[SocketIO] Event handlers registered successfully")
