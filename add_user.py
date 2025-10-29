import sqlite3

conn = sqlite3.connect('instance/app.db')
cursor = conn.cursor()

cursor.execute('''
INSERT INTO user_profiles (username, email, full_name, latitude, longitude)
VALUES (?, ?, ?, ?, ?)
''', ('ewabeach', 'ewa@example.com', 'Ewa Beach Driver', 21.3156, -158.0072))

conn.commit()
conn.close()

print("User added successfully")