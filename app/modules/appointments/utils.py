import secrets
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


APP_TIMEZONE = ZoneInfo(
    "Asia/Kolkata",
)


def now_local() -> datetime:
    return datetime.now(
        APP_TIMEZONE,
    ).replace(
        tzinfo=None,
    )


def today_local() -> date:
    return datetime.now(
        APP_TIMEZONE,
    ).date()


def generate_appointment_number() -> str:
    today = today_local()

    random_part = (
        secrets.token_hex(4)
        .upper()
    )

    return (
        f"APT-"
        f"{today.strftime('%Y%m%d')}-"
        f"{random_part}"
    )


def combine_date_time(
    value_date: date,
    value_time: time,
) -> datetime:
    return datetime.combine(
        value_date,
        value_time,
    )


def generate_time_slots(
    slot_date: date,
    start_time: time,
    end_time: time,
    duration_minutes: int,
) -> list[tuple[time, time]]:

    start_datetime = datetime.combine(
        slot_date,
        start_time,
    )

    end_datetime = datetime.combine(
        slot_date,
        end_time,
    )

    duration = timedelta(
        minutes=duration_minutes,
    )

    slots: list[
        tuple[time, time]
    ] = []

    current = start_datetime

    while (
        current + duration
        <= end_datetime
    ):

        slot_end = (
            current
            + duration
        )

        slots.append(
            (
                current.time(),
                slot_end.time(),
            )
        )

        current = slot_end

    return slots