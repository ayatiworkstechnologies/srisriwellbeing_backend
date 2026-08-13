from enum import Enum


class AppointmentStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CHECKED_IN = "CHECKED_IN"
    IN_CONSULTATION = "IN_CONSULTATION"
    COMPLETED = "COMPLETED"
    RESCHEDULED = "RESCHEDULED"
    NO_SHOW = "NO_SHOW"


class AppointmentType(str, Enum):
    WALK_IN = "WALK_IN"
    ONLINE = "ONLINE"
    FOLLOW_UP = "FOLLOW_UP"


class BookingSource(str, Enum):
    ADMIN = "ADMIN"
    RECEPTION = "RECEPTION"
    PATIENT_PORTAL = "PATIENT_PORTAL"
    DOCTOR = "DOCTOR"


class WaitingListStatus(str, Enum):
    WAITING = "WAITING"
    SLOT_OFFERED = "SLOT_OFFERED"
    BOOKED = "BOOKED"
    EXPIRED = "EXPIRED"


class ReminderChannel(str, Enum):
    SMS = "SMS"
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"
    PUSH = "PUSH"


class ReminderStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"