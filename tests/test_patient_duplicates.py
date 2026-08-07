from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.main import app
from app.modules.patients.duplicate_service import (
    find_possible_duplicates,
)
from app.modules.patients.schemas import PatientDuplicateCheckRequest

_ = app  # Initialize the complete SQLAlchemy model registry.


def test_duplicate_check_requires_at_least_one_identifier() -> None:
    with pytest.raises(ValidationError):
        PatientDuplicateCheckRequest()


@pytest.mark.asyncio
async def test_duplicate_check_matches_all_supported_signals(
) -> None:
    patient = SimpleNamespace(
        id=9,
        patient_code="PT202601010001",
        first_name="John",
        middle_name=None,
        last_name="Smith",
        normalized_full_name="john smith",
        mobile_number="9876543210",
        email="john@example.com",
        date_of_birth=date(1990, 1, 2),
    )
    scalar_result = SimpleNamespace(
        scalars=lambda: SimpleNamespace(
            unique=lambda: SimpleNamespace(all=lambda: [patient])
        )
    )
    db = SimpleNamespace(execute=AsyncMock(return_value=scalar_result))
    payload = PatientDuplicateCheckRequest(
        first_name="Jon",
        last_name="Smith",
        mobile_number="9876543210",
        email="JOHN@example.com",
        date_of_birth=date(1990, 1, 2),
    )

    response = await find_possible_duplicates(db=db, payload=payload)

    assert response.has_possible_duplicates is True
    assert response.is_duplicate is True
    assert response.patient_id == 9
    assert response.patient_code == "PT202601010001"
    assert response.matches[0].mobile_match is True
    assert response.matches[0].email_match is True
    assert response.matches[0].date_of_birth_match is True
    assert response.matches[0].name_similarity_score >= 85


@pytest.mark.asyncio
async def test_duplicate_check_keeps_mobile_only_frontend_compatible() -> None:
    scalar_result = SimpleNamespace(
        scalars=lambda: SimpleNamespace(
            unique=lambda: SimpleNamespace(all=lambda: [])
        )
    )
    db = SimpleNamespace(execute=AsyncMock(return_value=scalar_result))
    payload = PatientDuplicateCheckRequest(mobile_number="9876543210")

    response = await find_possible_duplicates(db=db, payload=payload)

    assert response.has_possible_duplicates is False
    assert response.is_duplicate is False
    assert response.patient_id is None
    assert response.matches == []
