import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

conn = sqlite3.connect('instance/app.db')
cursor = conn.cursor()

username = 'Dxyasforg'
email = 'admin@groupnavigation.local'
password = 'Angello4845'

password_hash = generate_password_hash(password)
created_at = datetime.utcnow().isoformat()

try:
    cursor.execute(
        "INSERT INTO user_profiles (username, email, password_hash, full_name, is_admin, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (username, email, password_hash, 'Administrator', 1, created_at)
    )
    conn.commit()
    print(f"✓ Admin account created successfully!")
    print(f"  Username: {username}")
    print(f"  Password: {password}")
    print(f"  Access: http://127.0.0.1:5000/profiles/login")
except sqlite3.IntegrityError as e:
    print(f"✗ Error: {e}")
    print("Admin user may already exist")
except Exception as e:
    print(f"✗ Unexpected error: {e}")
finally:
    conn.close()
