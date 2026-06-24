"""Integration tests for Company CRUD — /api/v1/companies endpoints."""

import uuid as _uuid

try:
    import pytest
except ImportError:
    pass  # standalone runner — no pytest required

from tests.test_auth import _PHONE_COUNTER, _unique_phone, PASSWORD


class TestCompanyCRUD:
    """Integration tests for /api/v1/companies endpoints."""

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    async def _register(self, client, phone=None):
        if phone is None:
            phone = _unique_phone()
        resp = await client.post(
            "/api/v1/auth/register",
            json={"phone": phone, "password": PASSWORD},
        )
        return resp

    async def _auth_header(self, client, phone=None):
        """Register user and return Authorization header dict."""
        resp = await self._register(client, phone)
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}, token

    # ------------------------------------------------------------------ #
    #  CREATE
    # ------------------------------------------------------------------ #

    async def test_create_company_returns_201(self, client):
        headers, _ = await self._auth_header(client)
        resp = await client.post("/api/v1/companies", json={"name": "TestCo"}, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "TestCo"
        assert data["stage"] == "idea"
        assert "id" in data
        assert "owner_id" in data

    async def test_create_company_duplicate_name_returns_409(self, client):
        headers, _ = await self._auth_header(client)
        await client.post("/api/v1/companies", json={"name": "DupCo"}, headers=headers)
        resp = await client.post("/api/v1/companies", json={"name": "DupCo"}, headers=headers)
        assert resp.status_code == 409

    async def test_create_company_without_token_returns_401(self, client):
        resp = await client.post("/api/v1/companies", json={"name": "TestCo"})
        assert resp.status_code == 401

    # ------------------------------------------------------------------ #
    #  GET ONE
    # ------------------------------------------------------------------ #

    async def test_get_company_returns_200(self, client):
        headers, _ = await self._auth_header(client)
        create_resp = await client.post("/api/v1/companies", json={"name": "MyCo"}, headers=headers)
        company_id = create_resp.json()["id"]
        resp = await client.get(f"/api/v1/companies/{company_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "MyCo"

    async def test_get_company_not_found_returns_404(self, client):
        headers, _ = await self._auth_header(client)
        fake_id = str(_uuid.uuid4())
        resp = await client.get(f"/api/v1/companies/{fake_id}", headers=headers)
        assert resp.status_code == 404

    async def test_get_company_without_token_returns_401(self, client):
        resp = await client.get(f"/api/v1/companies/{str(_uuid.uuid4())}")
        assert resp.status_code == 401

    # ------------------------------------------------------------------ #
    #  LIST
    # ------------------------------------------------------------------ #

    async def test_list_companies_returns_200(self, client):
        headers, _ = await self._auth_header(client)
        await client.post("/api/v1/companies", json={"name": "A"}, headers=headers)
        await client.post("/api/v1/companies", json={"name": "B"}, headers=headers)
        resp = await client.get("/api/v1/companies", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    async def test_list_companies_empty_returns_200(self, client):
        headers, _ = await self._auth_header(client)
        resp = await client.get("/api/v1/companies", headers=headers)
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_companies_only_returns_owned(self, client):
        h1, _ = await self._auth_header(client)
        await client.post("/api/v1/companies", json={"name": "User1Co"}, headers=h1)
        h2, _ = await self._auth_header(client)
        await client.post("/api/v1/companies", json={"name": "User2Co"}, headers=h2)
        # User1 sees only their company
        resp = await client.get("/api/v1/companies", headers=h1)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "User1Co"

    # ------------------------------------------------------------------ #
    #  UPDATE
    # ------------------------------------------------------------------ #

    async def test_update_company_returns_200(self, client):
        headers, _ = await self._auth_header(client)
        create_resp = await client.post("/api/v1/companies", json={"name": "Old"}, headers=headers)
        cid = create_resp.json()["id"]
        resp = await client.put(f"/api/v1/companies/{cid}", json={"name": "New", "stage": "seed"}, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "New"
        assert data["stage"] == "seed"

    async def test_update_company_partial_returns_200(self, client):
        headers, _ = await self._auth_header(client)
        create_resp = await client.post(
            "/api/v1/companies", json={"name": "Partial", "stage": "pre_seed"}, headers=headers
        )
        cid = create_resp.json()["id"]
        resp = await client.put(f"/api/v1/companies/{cid}", json={"name": "Renamed"}, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Renamed"
        assert data["stage"] == "pre_seed"  # unchanged

    # ------------------------------------------------------------------ #
    #  DELETE
    # ------------------------------------------------------------------ #

    async def test_delete_company_returns_204(self, client):
        headers, _ = await self._auth_header(client)
        create_resp = await client.post("/api/v1/companies", json={"name": "DelMe"}, headers=headers)
        cid = create_resp.json()["id"]
        resp = await client.delete(f"/api/v1/companies/{cid}", headers=headers)
        assert resp.status_code == 204
        # Verify gone
        get_resp = await client.get(f"/api/v1/companies/{cid}", headers=headers)
        assert get_resp.status_code == 404

    # ------------------------------------------------------------------ #
    #  OWNERSHIP
    # ------------------------------------------------------------------ #

    async def test_get_other_users_company_returns_404(self, client):
        h1, _ = await self._auth_header(client)
        create_resp = await client.post("/api/v1/companies", json={"name": "Mine"}, headers=h1)
        cid = create_resp.json()["id"]
        h2, _ = await self._auth_header(client)
        resp = await client.get(f"/api/v1/companies/{cid}", headers=h2)
        assert resp.status_code == 404

    async def test_update_other_users_company_returns_404(self, client):
        h1, _ = await self._auth_header(client)
        create_resp = await client.post("/api/v1/companies", json={"name": "NotYours"}, headers=h1)
        cid = create_resp.json()["id"]
        h2, _ = await self._auth_header(client)
        resp = await client.put(f"/api/v1/companies/{cid}", json={"name": "Hacked"}, headers=h2)
        assert resp.status_code == 404

    async def test_delete_other_users_company_returns_404(self, client):
        h1, _ = await self._auth_header(client)
        create_resp = await client.post("/api/v1/companies", json={"name": "KeepIt"}, headers=h1)
        cid = create_resp.json()["id"]
        h2, _ = await self._auth_header(client)
        resp = await client.delete(f"/api/v1/companies/{cid}", headers=h2)
        assert resp.status_code == 404
