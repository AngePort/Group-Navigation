# Driving Navigation App (Prototype)

A real-time group navigation application built with Python Flask and WebSockets. Users can create accounts, log in, view their location on an interactive map, and see other connected users in real-time.

## Features

✅ **User Authentication**
- User registration and login system
- Secure password hashing with Werkzeug
- Session-based authentication

✅ **User Management**
- Create, read, update, and delete user profiles
- User profile fields: username, email, full name, vehicle type, location (lat/lng)
- Admin dashboard to manage all users

✅ **Real-Time Location Tracking**
- WebSocket-based real-time location updates using Flask-SocketIO
- Browser geolocation API integration (watch position)
- Live location markers on interactive map
- Connected users count

✅ **Interactive Map**
- Leaflet.js + OpenStreetMap integration
- Blue dot marker for current user location
- Red markers for other connected users
- User names displayed on markers
- Zoom and pan capabilities

## Tech Stack

- **Backend**: Python 3.14, Flask 2.3.2, Flask-SocketIO
- **Database**: SQLite3 with direct SQL queries
- **Frontend**: HTML, CSS, JavaScript (Vanilla + Socket.IO client)
- **Map**: Leaflet.js 1.9.4 + OpenStreetMap tiles
- **Real-time**: WebSocket (Socket.IO)

## Project Structure

```
Group-Navigation/
├── app.py              # Flask application factory
├── db.py               # Database initialization and connection
├── routes.py           # All HTTP routes and WebSocket handlers
├── requirements.txt    # Python dependencies
├── instance/
│   └── app.db         # SQLite database
├── tests/
│   └── test_*.py      # Unit tests
└── README.md          # This file
```

## Quick Start (macOS / zsh)

### 1. Clone and Setup

```bash
cd Group-Navigation
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the App

```bash
python3 app.py
```

The app will start on **http://127.0.0.1:5000**

## How to Use

### Register a New Account

1. Go to http://127.0.0.1:5000/profiles/register
2. Fill in username, email, password, and full name
3. Click "Register"

### Log In

1. Go to http://127.0.0.1:5000/profiles/login
2. Enter your username and password
3. Click "Login"

### View Real-Time Map

1. After logging in, click "Go to Map" or navigate to http://127.0.0.1:5000/profiles/map
2. **Allow location access** when your browser prompts
3. You'll see:
   - A blue dot showing your current location
   - Your username displayed on the map
   - "Connected users: X" counter
   - Other users' locations as red markers (if they're also logged in)

### Admin Dashboard

1. Log in with an admin account
2. Go to http://127.0.0.1:5000/profiles/admin
3. View all users, edit profiles, or delete users

## API Endpoints

### Authentication
- `GET /profiles/login` - Login page
- `POST /profiles/login` - Process login
- `GET /profiles/register` - Registration page
- `POST /profiles/register` - Create new account
- `POST /profiles/logout` - Logout

### User Profiles
- `GET /profiles/` - List all profiles
- `POST /profiles/` - Create profile (JSON)
- `GET /profiles/<id>` - Get specific profile
- `PUT /profiles/<id>` - Update profile (JSON)
- `GET /profiles/me` - Get current logged-in user profile

### Map & Tracking
- `GET /profiles/map` - Real-time navigation map with WebSocket
- `GET /profiles/admin` - Admin dashboard
- `GET /profiles/admin/edit/<id>` - Edit user (admin)
- `GET /profiles/admin/delete/<id>` - Delete user (admin)

### Health Check
- `GET /` - API health status

## WebSocket Events

The app uses Socket.IO for real-time location tracking:

### Client → Server
- `join_tracking` - User connects to location tracking
- `update_location` - Send location update (latitude, longitude)

### Server → Client
- `location_update` - Broadcast other users' location updates
- `user_count` - Update connected users count
- `connect` - WebSocket connection established
- `disconnect` - User disconnected

## Key Features Explained

### Real-Time Location Tracking

When you log in and go to the map:
1. Browser requests your geolocation (you must allow it)
2. WebSocket connects to server
3. Browser continuously watches your position using `navigator.geolocation.watchPosition()`
4. Location updates broadcast to all connected clients
5. All users see blue/red markers update in real-time

### Admin Functionality

Admin users can:
- View all user profiles
- Edit any user's information
- Delete user accounts
- Manage the entire user database

## Database Schema

### user_profiles Table

```sql
CREATE TABLE user_profiles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  full_name TEXT,
  vehicle_type TEXT,
  latitude REAL,
  longitude REAL,
  is_admin INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Testing

```bash
# Run all tests
python3 -m pytest -q

# Run specific test file
python3 -m pytest tests/test_profiles.py -v

# Run with coverage
python3 -m pytest --cov
```

## Helper Scripts

Create users and manage passwords:

```bash
# Add a new user
python3 add_user.py

# Create an admin user
python3 create_admin.py

# Set password for a user
python3 set_password.py
```

## Troubleshooting

### WebSocket Connection Issues

**Problem**: Map shows "Connected users: 0" and no blue dot appears

**Solution**:
1. Check browser console (F12 → Console) for JavaScript errors
2. Ensure geolocation permission is granted
3. Check server logs for `[SocketIO]` messages
4. Restart the app: `Ctrl+C` and run `python3 app.py` again

### Port Already in Use

```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9
```

### Database Issues

```bash
# Reset database (deletes all data)
rm instance/app.db
python3 app.py  # Will recreate database
```

## Future Enhancements

- [ ] Add route navigation and directions
- [ ] Implement speed and heading tracking
- [ ] Add group management and team tracking
- [ ] Store location history
- [ ] Mobile app using React Native
- [ ] Production deployment with Postgres and Gunicorn
- [ ] OAuth authentication (Google, GitHub)
- [ ] Push notifications for new users

## Development

### Running in Debug Mode

Edit `app.py` and change the Flask app initialization to enable debug mode for hot-reloading.

### Environment Variables

```bash
export FLASK_ENV=development
export DATABASE=instance/app.db
python3 app.py
```

## License

MIT License - feel free to use this for learning and development.

## Support

For issues or questions, check the logs and ensure:
- Python 3.14+ is installed
- All dependencies in `requirements.txt` are installed
- Port 5000 is not in use
- Browser geolocation is enabled
