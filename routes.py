from flask import Blueprint, request, current_app
from db import get_db
from datetime import datetime

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
        "INSERT INTO user_profiles (username, email, full_name, vehicle_type, created_at) VALUES (?, ?, ?, ?, ?)",
        (username, email, data.get("full_name"), data.get("vehicle_type"), created_at),
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
    cur.execute(
        "UPDATE user_profiles SET full_name = ?, vehicle_type = ? WHERE id = ?",
        (full_name, vehicle_type, profile_id),
    )
    db.commit()
    cur.execute("SELECT * FROM user_profiles WHERE id = ?", (profile_id,))
    updated = cur.fetchone()
    return dict(updated)


@profiles_bp.route("/<int:profile_id>", methods=["DELETE"])
def delete_profile(profile_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM user_profiles WHERE id = ?", (profile_id,))
    row = cur.fetchone()
    if not row:
        return {"error": "not found"}, 404
    cur.execute("DELETE FROM user_profiles WHERE id = ?", (profile_id,))
    db.commit()
    return {"message": "profile deleted"}, 200
