from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.modules.duty_doctor.schemas import VitalCreate


def test_vitals_reject_height_supplied_in_feet():
    with pytest.raises(ValidationError, match="greater than or equal to 30"):
        VitalCreate(height_cm=Decimal("5.5"), weight_kg=Decimal("55"))


def test_vitals_reject_bmi_that_cannot_be_stored():
    with pytest.raises(ValidationError, match="BMI outside the supported range"):
        VitalCreate(height_cm=Decimal("30"), weight_kg=Decimal("100"))


def test_vitals_accept_metric_height_and_weight():
    vitals = VitalCreate(
        height_cm=Decimal("167.64"),
        weight_kg=Decimal("55"),
    )

    assert vitals.height_cm == Decimal("167.64")
    assert vitals.weight_kg == Decimal("55")
