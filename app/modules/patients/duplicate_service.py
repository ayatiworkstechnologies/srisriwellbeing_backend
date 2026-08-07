import re
import unicodedata
from typing import Optional

from rapidfuzz import fuzz
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patients.models import Patient
from app.modules.patients.schemas import (
    DuplicatePatientMatchResponse,
    PatientDuplicateCheckRequest,
    PatientDuplicateCheckResponse,
)


def normalize_name(
    first_name: Optional[str],
    middle_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> str:
    full_name = " ".join(
        part
        for part in [
            first_name,
            middle_name,
            last_name,
        ]
        if part
    )

    normalized = unicodedata.normalize(
        "NFKD",
        full_name,
    )

    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(
            character
        )
    )

    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)

    return normalized.strip()


def build_full_name(patient: Patient) -> str:
    return " ".join(
        value
        for value in [
            patient.first_name,
            patient.middle_name,
            patient.last_name,
        ]
        if value
    )


async def find_possible_duplicates(
    db: AsyncSession,
    payload: PatientDuplicateCheckRequest,
) -> PatientDuplicateCheckResponse:
    normalized_name = normalize_name(
        payload.first_name,
        payload.middle_name,
        payload.last_name,
    )

    filters = []

    if payload.mobile_number:
        filters.append(Patient.mobile_number == payload.mobile_number)

    if payload.email:
        filters.append(Patient.email == str(payload.email).lower())

    if payload.date_of_birth:
        filters.append(Patient.date_of_birth == payload.date_of_birth)

    if normalized_name:
        name_prefix = normalized_name.split()[0][:3]
        filters.append(Patient.normalized_full_name.ilike(f"%{name_prefix}%"))

    statement = select(Patient).where(or_(*filters)).limit(100)

    result = await db.execute(statement)
    candidate_patients = result.scalars().unique().all()

    matches: list[DuplicatePatientMatchResponse] = []

    for patient in candidate_patients:
        mobile_match = bool(
            payload.mobile_number
            and patient.mobile_number == payload.mobile_number
        )

        email_match = bool(
            payload.email
            and patient.email
            and patient.email.lower() == str(payload.email).lower()
        )

        dob_match = bool(
            payload.date_of_birth
            and patient.date_of_birth
            and patient.date_of_birth == payload.date_of_birth
        )

        name_score = (
            int(
                fuzz.token_sort_ratio(
                    normalized_name,
                    patient.normalized_full_name,
                )
            )
            if normalized_name
            else 0
        )

        overall_score = 0

        if mobile_match:
            overall_score += 45

        if email_match:
            overall_score += 30

        if dob_match:
            overall_score += 15

        overall_score += int(name_score * 0.10)

        if overall_score < 45 and name_score < 85:
            continue

        matches.append(
            DuplicatePatientMatchResponse(
                patient_id=patient.id,
                patient_code=patient.patient_code,
                full_name=build_full_name(patient),
                mobile_number=patient.mobile_number,
                email=patient.email,
                date_of_birth=patient.date_of_birth,
                mobile_match=mobile_match,
                email_match=email_match,
                date_of_birth_match=dob_match,
                name_similarity_score=name_score,
                overall_match_score=min(overall_score, 100),
            )
        )

    matches.sort(
        key=lambda item: item.overall_match_score,
        reverse=True,
    )

    first_match = matches[0] if matches else None

    return PatientDuplicateCheckResponse(
        has_possible_duplicates=bool(matches),
        matches=matches,
        is_duplicate=bool(matches),
        patient_id=first_match.patient_id if first_match else None,
        patient_code=first_match.patient_code if first_match else None,
        message=(
            "Possible duplicate patients found"
            if matches
            else "No possible duplicate patients found"
        ),
    )
