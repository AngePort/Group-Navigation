import json
import pytest
from app import create_app


@pytest.fixture
def client(tmp_path):
    db_path = tmp_path / "test.db"
    app = create_app({
        "TESTING": True,
        "DATABASE": str(db_path),
    })
    with app.test_client() as c:
        with app.app_context():
            # db_init creates the schema
            pass
        yield c


def test_create_and_get_profile(client):
    payload = {"username": "alice", "email": "alice@example.com", "full_name": "Alice A"}
    rv = client.post("/profiles/", json=payload)
    assert rv.status_code == 201
    data = rv.get_json()
    assert data["username"] == "alice"
    pid = data["id"]

    # retrieve
    rv2 = client.get(f"/profiles/{pid}")
    assert rv2.status_code == 200
    got = rv2.get_json()
    assert got["email"] == "alice@example.com"


def test_list_profiles_empty_then_nonempty(client):
    rv = client.get("/profiles/")
    assert rv.status_code == 200
    data = rv.get_json()
    assert isinstance(data.get("profiles"), list)

    # create one
    client.post("/profiles/", json={"username": "bob", "email": "bob@example.com"})
    rv2 = client.get("/profiles/")
    data2 = rv2.get_json()
    assert len(data2.get("profiles")) >= 1


def test_delete_profile(client):
    # create a profile
    payload = {"username": "charlie", "email": "charlie@example.com"}
    rv = client.post("/profiles/", json=payload)
    assert rv.status_code == 201
    data = rv.get_json()
    pid = data["id"]

    # delete it
    rv_del = client.delete(f"/profiles/{pid}")
    assert rv_del.status_code == 200
    assert rv_del.get_json()["message"] == "profile deleted"

    # verify it's gone
    rv_get = client.get(f"/profiles/{pid}")
    assert rv_get.status_code == 404
