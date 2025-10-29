import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('instance/app.db')
cursor = conn.cursor()

password_hash = generate_password_hash('password123')  # Set a default password
cursor.execute('UPDATE user_profiles SET password_hash = ? WHERE username = ?', (password_hash, 'ewabeach'))

conn.commit()
conn.close()

print("Password set for ewabeach")