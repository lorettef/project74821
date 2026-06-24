try:
    import pytest
except ImportError:
    pass  # standalone runner — no pytest required


class TestHealth:
    async def test_health_returns_ok(self, client):
        resp = await client.get("/api/v1/health")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["version"] == "2.0.0"
        assert "db" in data
