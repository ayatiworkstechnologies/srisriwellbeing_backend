from app.main import app


def test_rbac_routes_are_registered_without_duplicate_prefix() -> None:
    routes = {
        (method, route.path)
        for route in app.routes
        for method in (route.methods or set())
    }

    expected_routes = {
        ("POST", "/api/rbac/roles"),
        ("GET", "/api/rbac/roles"),
        ("GET", "/api/rbac/roles/{role_id}"),
        ("POST", "/api/rbac/roles/{role_id}/permissions"),
        ("POST", "/api/rbac/users/{user_id}/roles"),
        ("GET", "/api/rbac/users/{user_id}/roles"),
        ("DELETE", "/api/rbac/users/{user_id}/roles/{role_id}"),
        ("POST", "/api/rbac/permissions"),
        ("GET", "/api/rbac/permissions"),
        ("GET", "/api/rbac/permissions/{permission_id}"),
    }

    assert expected_routes <= routes
    assert not any(path.startswith("/api/rbac/rbac/") for _, path in routes)
