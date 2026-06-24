import asyncio

try:
    import pytest
except ImportError:
    pass  # standalone runner — no pytest required


PASSWORD = "securePass1!"
ALT_PASSWORD = "wrongPassword1!"
_PHONE_COUNTER = 0


def _unique_phone() -> str:
    global _PHONE_COUNTER
    _PHONE_COUNTER += 1
    return f"+7999{_PHONE_COUNTER:07d}"


class TestAuthFlow:
    """Integration tests for the /api/v1/auth endpoints."""

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    async def _register(self, client, phone=None, password=PASSWORD):
        if phone is None:
            phone = _unique_phone()
        resp = await client.post(
            "/api/v1/auth/register",
            json={"phone": phone, "password": password},
        )
        return resp

    async def _login(self, client, phone=None, password=PASSWORD):
        if phone is None:
            phone = _unique_phone()
        resp = await client.post(
            "/api/v1/auth/login",
            json={"phone": phone, "password": password},
        )
        return resp

    # ------------------------------------------------------------------ #
    #  Registration
    # ------------------------------------------------------------------ #

    async def test_register_creates_user_and_returns_tokens(self, client):
        resp = await self._register(client)

        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
        assert len(data["refresh_token"]) > 0

    async def test_register_duplicate_phone_returns_409(self, client):
        phone = _unique_phone()
        await self._register(client, phone=phone)
        resp = await self._register(client, phone=phone)

        assert resp.status_code == 409
        err = resp.json()
        assert err["error"]["code"] == "CONFLICT"

    async def test_register_invalid_phone_returns_422(self, client):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"phone": "12", "password": PASSWORD},
        )

        assert resp.status_code == 422

    # ------------------------------------------------------------------ #
    #  Login
    # ------------------------------------------------------------------ #

    async def test_login_with_valid_credentials_returns_tokens(self, client):
        phone = _unique_phone()
        await self._register(client, phone=phone)
        resp = await self._login(client, phone=phone)

        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_with_wrong_password_returns_401(self, client):
        phone = _unique_phone()
        await self._register(client, phone=phone)
        resp = await self._login(client, phone=phone, password=ALT_PASSWORD)

        assert resp.status_code == 401
        err = resp.json()
        assert err["error"]["code"] == "UNAUTHORIZED"

    async def test_login_with_nonexistent_user_returns_401(self, client):
        resp = await self._login(client, phone="+70000000000")

        assert resp.status_code == 401
        err = resp.json()
        assert err["error"]["code"] == "UNAUTHORIZED"

    # ------------------------------------------------------------------ #
    #  GET /me
    # ------------------------------------------------------------------ #

    async def test_me_returns_user_data(self, client):
        phone = _unique_phone()
        reg_resp = await self._register(client, phone=phone)
        access_token = reg_resp.json()["access_token"]

        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["phone"] == phone
        assert "id" in data
        assert "created_at" in data

    async def test_me_without_token_returns_401(self, client):
        resp = await client.get("/api/v1/auth/me")

        assert resp.status_code in (401, 403)

    async def test_me_with_invalid_token_returns_401(self, client):
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer garbage.token.here"},
        )

        assert resp.status_code == 401

    # ------------------------------------------------------------------ #
    #  POST /refresh
    # ------------------------------------------------------------------ #

    async def test_refresh_returns_new_token_pair(self, client):
        reg_resp = await self._register(client)
        old_tokens = reg_resp.json()

        await asyncio.sleep(1.1)

        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_tokens["refresh_token"]},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"] != old_tokens["access_token"]
        assert data["refresh_token"] != old_tokens["refresh_token"]
        assert len(data["access_token"]) > 0
        assert len(data["refresh_token"]) > 0

    async def test_refresh_with_revoked_token_returns_401(self, client):
        reg_resp = await self._register(client)
        old_refresh = reg_resp.json()["refresh_token"]

        await asyncio.sleep(1.1)

        # First refresh — consumes (revokes) the original token.
        await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh},
        )

        # Second refresh with the SAME (now-revoked) token.
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh},
        )

        assert resp.status_code == 401

    # ------------------------------------------------------------------ #
    #  POST /logout
    # ------------------------------------------------------------------ #

    async def test_logout_revokes_token(self, client):
        reg_resp = await self._register(client)
        refresh_token = reg_resp.json()["refresh_token"]

        logout_resp = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
        )
        assert logout_resp.status_code == 204

        refresh_resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_resp.status_code == 401

    # ------------------------------------------------------------------ #
    #  Full flow
    # ------------------------------------------------------------------ #

    async def test_full_auth_flow(self, client):
        phone = _unique_phone()

        # 1. Register
        reg_resp = await self._register(client, phone=phone)
        assert reg_resp.status_code == 201
        tokens = reg_resp.json()
        reg_access = tokens["access_token"]
        reg_refresh = tokens["refresh_token"]

        # JWT tokens are deterministic per payload — ensure
        # register and login produce different tokens.
        await asyncio.sleep(1.1)

        # 2. Login
        login_resp = await self._login(client, phone=phone)
        assert login_resp.status_code == 200
        login_tokens = login_resp.json()
        login_access = login_tokens["access_token"]

        # 3. /me
        me_resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {login_access}"},
        )
        assert me_resp.status_code == 200
        assert me_resp.json()["phone"] == phone

        # 4. Refresh
        await asyncio.sleep(1.1)
        refresh_resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": login_tokens["refresh_token"]},
        )
        assert refresh_resp.status_code == 200
        new_tokens = refresh_resp.json()

        # 5. /me with new access token
        me2_resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
        )
        assert me2_resp.status_code == 200
        assert me2_resp.json()["phone"] == phone

        # 6. Logout
        logout_resp = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": new_tokens["refresh_token"]},
        )
        assert logout_resp.status_code == 204

        # 7. Refresh after logout — must fail
        refresh_after = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": new_tokens["refresh_token"]},
        )
        assert refresh_after.status_code == 401
