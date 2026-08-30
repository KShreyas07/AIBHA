def test_register_and_login(client):
    resp = client.post("/api/auth/register", json={"full_name": "Alice", "email": "alice@example.com", "password": "strongpass1"})
    assert resp.status_code == 201
    assert resp.json()["user"]["email"] == "alice@example.com"

    resp = client.post("/api/auth/login", json={"email": "alice@example.com", "password": "strongpass1"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client):
    client.post("/api/auth/register", json={"full_name": "Bob", "email": "bob@example.com", "password": "strongpass1"})
    resp = client.post("/api/auth/login", json={"email": "bob@example.com", "password": "wrongpass"})
    assert resp.status_code == 401


def test_duplicate_registration(client):
    payload = {"full_name": "Carl", "email": "carl@example.com", "password": "strongpass1"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/register", json=payload).status_code == 400


def test_me_requires_token(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code in (401, 403)
