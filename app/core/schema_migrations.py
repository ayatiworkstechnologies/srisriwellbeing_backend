from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


async def ensure_patient_portal_schema(
    connection: AsyncConnection,
) -> None:
    """Add portal columns to an existing patients table.

    The project currently uses ``metadata.create_all()`` instead of a
    configured Alembic migration workflow. ``create_all()`` creates new
    tables but does not add columns to existing ones, so these checks keep
    older local databases compatible with the patient portal model.
    """

    result = await connection.execute(text("SHOW COLUMNS FROM patients"))
    column_names = {row[0] for row in result}

    if "user_id" not in column_names:
        await connection.execute(
            text(
                "ALTER TABLE patients "
                "ADD COLUMN user_id INT NULL, "
                "ADD UNIQUE INDEX uq_patients_user_id (user_id), "
                "ADD CONSTRAINT fk_patients_user_id "
                "FOREIGN KEY (user_id) REFERENCES users(id) "
                "ON DELETE SET NULL"
            )
        )

    if "blood_group" not in column_names:
        await connection.execute(
            text(
                "ALTER TABLE patients "
                "ADD COLUMN blood_group VARCHAR(10) NULL"
            )
        )
