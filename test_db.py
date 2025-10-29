from app import create_app
import tempfile
import os

# Create a temporary database for testing
tmp = tempfile.mkdtemp()
db_path = os.path.join(tmp, 'test.db')

app = create_app({'TESTING': True, 'DATABASE': db_path})
client = app.test_client()

# Test health check
response = client.get('/')
print("Health check:", response.get_json())

# Create a profile
data = {"username": "testuser", "email": "test@example.com", "full_name": "Test User", "vehicle_type": "sedan"}
response = client.post('/profiles/', json=data)
print("Create profile:", response.status_code, response.get_json())
profile_id = response.get_json()["id"]

# List profiles
response = client.get('/profiles/')
print("List profiles:", response.get_json())

# Get specific profile
response = client.get(f'/profiles/{profile_id}')
print("Get profile:", response.get_json())

# Update profile
update_data = {"full_name": "Updated User", "vehicle_type": "SUV"}
response = client.put(f'/profiles/{profile_id}', json=update_data)
print("Update profile:", response.status_code, response.get_json())

# Delete profile
response = client.delete(f'/profiles/{profile_id}')
print("Delete profile:", response.status_code)

# Try to get deleted profile
response = client.get(f'/profiles/{profile_id}')
print("Get deleted profile:", response.status_code, response.get_json())