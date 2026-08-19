import ast
from pathlib import Path

from seeds.permissions_seed import (
    ALL_PERMISSIONS,
    PATIENT_ROLE_PERMISSION_CODES,
    validate_permission_seeds,
)
from seeds.role_permissions_seed import (
    ROLE_PERMISSION_CODES,
    validate_configuration,
)
from seeds.roles_seed import DEFAULT_ROLES
from app.modules.rbac.model import Permission


def test_seed_configuration_is_complete_and_consistent() -> None:
    validate_permission_seeds()
    validate_configuration()

    role_codes = {role.code for role in DEFAULT_ROLES}
    permission_codes = {permission.code for permission in ALL_PERMISSIONS}
    mapped_codes = set().union(*ROLE_PERMISSION_CODES.values())

    assert role_codes == set(ROLE_PERMISSION_CODES)
    assert mapped_codes <= permission_codes
    assert ROLE_PERMISSION_CODES["patient"] == set(
        PATIENT_ROLE_PERMISSION_CODES
    )


def test_seed_definitions_have_unique_identifiers() -> None:
    role_codes = [role.code for role in DEFAULT_ROLES]
    permission_codes = [permission.code for permission in ALL_PERMISSIONS]

    assert len(role_codes) == len(set(role_codes))
    assert len(permission_codes) == len(set(permission_codes))
    assert all(permission.name.strip() for permission in ALL_PERMISSIONS)
    assert "name" in Permission.__table__.columns


def test_every_route_permission_is_seeded() -> None:
    route_permissions: set[str] = set()

    for path in Path("app").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Name):
                continue
            if node.func.id != "require_permission":
                continue

            route_permissions.update(
                argument.value
                for argument in node.args
                if isinstance(argument, ast.Constant)
                and isinstance(argument.value, str)
            )

    seeded_permissions = {
        permission.code for permission in ALL_PERMISSIONS
    }

    assert route_permissions <= seeded_permissions
