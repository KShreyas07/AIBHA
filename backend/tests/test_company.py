def test_create_and_list_company(client, auth_headers):
    payload = {
        "name": "Acme Corp", "industry": "Retail", "country": "USA",
        "financial_year": "2026", "business_size": "small", "employees": 12,
    }
    resp = client.post("/api/company", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    company_id = resp.json()["id"]

    resp = client.get("/api/company", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.get(f"/api/company/{company_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Acme Corp"


def test_company_requires_auth(client):
    resp = client.get("/api/company")
    assert resp.status_code in (401, 403)


def test_cannot_access_other_users_company(client, auth_headers):
    client.post("/api/auth/register", json={"full_name": "Eve", "email": "eve@example.com", "password": "strongpass1"})
    eve_login = client.post("/api/auth/login", json={"email": "eve@example.com", "password": "strongpass1"})
    eve_headers = {"Authorization": f"Bearer {eve_login.json()['access_token']}"}

    payload = {"name": "Jane Co", "industry": "Tech", "country": "USA", "financial_year": "2026", "business_size": "small", "employees": 5}
    company_id = client.post("/api/company", json=payload, headers=auth_headers).json()["id"]

    resp = client.get(f"/api/company/{company_id}", headers=eve_headers)
    assert resp.status_code == 404
