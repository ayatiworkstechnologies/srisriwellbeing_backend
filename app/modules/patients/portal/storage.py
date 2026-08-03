import asyncio
from pathlib import Path
from uuid import uuid4

from fastapi import (
    HTTPException,
    UploadFile,
    status,
)


MAX_FILE_SIZE = 10 * 1024 * 1024

UPLOAD_ROOT = (
    Path("storage")
    / "patient_documents"
).resolve()


MIME_EXTENSION_MAP = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def detect_mime_type(
    file_content: bytes,
) -> str | None:
    if file_content.startswith(
        b"%PDF-"
    ):
        return "application/pdf"

    if file_content.startswith(
        b"\xff\xd8\xff"
    ):
        return "image/jpeg"

    if file_content.startswith(
        b"\x89PNG\r\n\x1a\n"
    ):
        return "image/png"

    if (
        len(file_content) >= 12
        and file_content[0:4] == b"RIFF"
        and file_content[8:12] == b"WEBP"
    ):
        return "image/webp"

    return None


async def save_patient_document(
    *,
    upload_file: UploadFile,
    patient_id: int,
) -> dict:
    original_file_name = Path(
        upload_file.filename or "document"
    ).name

    file_content = await upload_file.read(
        MAX_FILE_SIZE + 1
    )

    await upload_file.close()

    if not file_content:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail="Uploaded file is empty",
        )

    if (
        len(file_content)
        > MAX_FILE_SIZE
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            ),
            detail=(
                "Document size must be "
                "10 MB or less"
            ),
        )

    detected_mime_type = (
        detect_mime_type(
            file_content
        )
    )

    if (
        detected_mime_type
        not in MIME_EXTENSION_MAP
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            ),
            detail=(
                "Only PDF, JPG, PNG and "
                "WEBP files are allowed"
            ),
        )

    extension = MIME_EXTENSION_MAP[
        detected_mime_type
    ]

    stored_file_name = (
        f"{uuid4().hex}{extension}"
    )

    patient_directory = (
        UPLOAD_ROOT
        / str(patient_id)
    )

    await asyncio.to_thread(
        patient_directory.mkdir,
        parents=True,
        exist_ok=True,
    )

    file_path = (
        patient_directory
        / stored_file_name
    ).resolve()

    try:
        file_path.relative_to(
            UPLOAD_ROOT
        )
    except ValueError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail="Invalid document path",
        ) from error

    await asyncio.to_thread(
        file_path.write_bytes,
        file_content,
    )

    return {
        "original_file_name": (
            original_file_name
        ),
        "stored_file_name": (
            stored_file_name
        ),
        "file_path": str(file_path),
        "mime_type": (
            detected_mime_type
        ),
        "file_size": len(
            file_content
        ),
    }


async def delete_stored_document(
    file_path: str | None,
) -> None:
    if not file_path:
        return

    path = Path(file_path).resolve()

    try:
        path.relative_to(
            UPLOAD_ROOT
        )
    except ValueError:
        return

    if path.exists() and path.is_file():
        await asyncio.to_thread(
            path.unlink
        )


def get_safe_document_path(
    file_path: str,
) -> Path:
    path = Path(file_path).resolve()

    try:
        path.relative_to(
            UPLOAD_ROOT
        )
    except ValueError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Document not found",
        ) from error

    if not path.exists():
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Document file not found",
        )

    return path