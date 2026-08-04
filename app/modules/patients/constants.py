from enum import Enum


class PatientStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BLOCKED = "BLOCKED"
    DECEASED = "DECEASED"


class Gender(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"
    PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY"


class IdentifierType(str, Enum):
    INTERNAL_PATIENT_ID = "INTERNAL_PATIENT_ID"
    AADHAAR = "AADHAAR"
    PASSPORT = "PASSPORT"
    DRIVING_LICENCE = "DRIVING_LICENCE"
    OTHER = "OTHER"


class AddressType(str, Enum):
    HOME = "HOME"
    WORK = "WORK"
    TEMPORARY = "TEMPORARY"
    OTHER = "OTHER"


class DocumentType(str, Enum):
    ID_PROOF = "ID_PROOF"
    ADDRESS_PROOF = "ADDRESS_PROOF"
    MEDICAL_REPORT = "MEDICAL_REPORT"
    PRESCRIPTION = "PRESCRIPTION"
    SCAN = "SCAN"
    LAB_REPORT = "LAB_REPORT"
    OTHER = "OTHER"


class DuplicateMatchStatus(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    CONFIRMED_DUPLICATE = "CONFIRMED_DUPLICATE"
    NOT_DUPLICATE = "NOT_DUPLICATE"
    MERGED = "MERGED"
