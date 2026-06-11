"""Smoke test: todas las vistas GET responden 200 (red de seguridad para el refactor)."""
import pytest

GET_ROUTES = [
    "/",
    "/calendar/2026/6",
    "/week/2026-06-09",
    "/day/2026-06-09",
    "/recurring",
    "/journal",
    "/ajustes",
    "/export",
    "/backup",
    "/search",
    "/search?q=algo",
]


@pytest.mark.parametrize("route", GET_ROUTES)
def test_get_route_ok(client, route):
    r = client.get(route, follow_redirects=True)
    assert r.status_code == 200
