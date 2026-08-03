from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Path,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.patients.constants import (
    DocumentType,
)
from app.modules.patients.portal.dependencies import (
    CurrentPatient,
    CurrentPatientUser,
)
from app.modules.patients.portal.schemas import (
    PatientDashboardResponse,
    PatientDocumentData,
    PatientDocumentDeleteResponse,
    PatientDocumentListData,
    PatientDocumentListResponse,
    PatientDocumentResponse,
    PatientProfileResponse,
    PatientProfileUpdate,
)
from app.modules.patients.portal.service import (
    PatientPortalService,
)


router = APIRouter()


def create_document_data(
    *,
    request: Request,
    document,
) -> PatientDocumentData:
    download_url = str(
        request.url_for(
            "download_patient_document",
            document_id=str(
                document.id
            ),
        )
    )

    return PatientDocumentData(
        id=document.id,
        patient_id=document.patient_id,
        document_type=(
            document.document_type
        ),
        title=document.title,
        original_file_name=(
            document.original_file_name
        ),
        file_url=download_url,
        mime_type=document.mime_type,
        file_size=document.file_size,
        uploaded_by=(
            document.uploaded_by
        ),
        created_at=document.created_at,
    )


@router.get(
    "/dashboard",
    response_model=PatientDashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Patient Dashboard",
)
async def get_patient_dashboard(
    current_patient: CurrentPatient,
    db: AsyncSession = Depends(get_db),
):
    dashboard = (
        await PatientPortalService
        .get_dashboard(
            db=db,
            patient=current_patient,
        )
    )

    return PatientDashboardResponse(
        message=(
            "Patient dashboard retrieved "
            "successfully"
        ),
        data=dashboard,
    )


@router.get(
    "/profile",
    response_model=PatientProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Patient Profile",
)
async def get_patient_profile(
    current_patient: CurrentPatient,
):
    profile = (
        PatientPortalService
        .get_profile(
            patient=current_patient,
        )
    )

    return PatientProfileResponse(
        message=(
            "Patient profile retrieved "
            "successfully"
        ),
        data=profile,
    )


@router.patch(
    "/profile",
    response_model=PatientProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Patient Profile",
)
async def update_patient_profile(
    payload: PatientProfileUpdate,
    current_patient: CurrentPatient,
    db: AsyncSession = Depends(get_db),
):
    profile = (
        await PatientPortalService
        .update_profile(
            db=db,
            patient=current_patient,
            payload=payload,
        )
    )

    return PatientProfileResponse(
        message=(
            "Patient profile updated "
            "successfully"
        ),
        data=profile,
    )


@router.get(
    "/documents",
    response_model=PatientDocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Patient Documents",
)
async def list_patient_documents(
    request: Request,
    current_patient: CurrentPatient,
    db: AsyncSession = Depends(get_db),
):
    documents = (
        await PatientPortalService
        .list_documents(
            db=db,
            patient=current_patient,
        )
    )

    document_items = [
        create_document_data(
            request=request,
            document=document,
        )
        for document in documents
    ]

    return PatientDocumentListResponse(
        message=(
            "Patient documents retrieved "
            "successfully"
        ),
        data=PatientDocumentListData(
            documents=document_items,
            total=len(document_items),
        ),
    )


@router.post(
    "/documents",
    response_model=PatientDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Patient Document",
)
async def upload_patient_document(
    request: Request,
    current_patient: CurrentPatient,
    current_user: CurrentPatientUser,
    db: AsyncSession = Depends(get_db),
    document_type: DocumentType = Form(...),
    title: str = Form(
        ...,
        min_length=1,
        max_length=255,
    ),
    file: UploadFile = File(...),
):
    document = (
        await PatientPortalService
        .upload_document(
            db=db,
            patient=current_patient,
            user_id=current_user.id,
            upload_file=file,
            document_type=(
                document_type.value
            ),
            title=title,
        )
    )

    return PatientDocumentResponse(
        message=(
            "Document uploaded successfully"
        ),
        data=create_document_data(
            request=request,
            document=document,
        ),
    )


@router.get(
    "/documents/{document_id}/download",
    name="download_patient_document",
    status_code=status.HTTP_200_OK,
    summary="Download Patient Document",
)
async def download_patient_document(
    current_patient: CurrentPatient,
    document_id: int = Path(
        ...,
        gt=0,
    ),
    db: AsyncSession = Depends(get_db),
):
    document, file_path = (
        await PatientPortalService
        .get_document_file(
            db=db,
            patient=current_patient,
            document_id=document_id,
        )
    )

    return FileResponse(
        path=file_path,
        media_type=document.mime_type,
        filename=(
            document.original_file_name
        ),
    )


@router.delete(
    "/documents/{document_id}",
    response_model=PatientDocumentDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete Patient Document",
)
async def delete_patient_document(
    current_patient: CurrentPatient,
    document_id: int = Path(
        ...,
        gt=0,
    ),
    db: AsyncSession = Depends(get_db),
):
    document = (
        await PatientPortalService
        .delete_document(
            db=db,
            patient=current_patient,
            document_id=document_id,
        )
    )

    return PatientDocumentDeleteResponse(
        message=(
            "Document deleted successfully"
        ),
        data={
            "document_id": document.id,
        },
    )