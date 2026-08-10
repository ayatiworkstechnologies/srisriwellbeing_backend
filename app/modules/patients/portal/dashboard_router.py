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

from app.modules.clinical.schemas import (
    AllergyCreate,
    ConditionCreate,
    EmergencyContactCreate,
    MedicalHistoryUpsert,
    MedicineCreate,
    PatientConsentCreate,
    SurgeryCreate,
)

from app.modules.clinical.service import (
    ClinicalService,
)

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


PATIENT_CLINICAL_RESOURCES = (
    "conditions",
    "surgeries",
    "medicines",
    "allergies",
    "emergency-contacts",
    "consents",
)


CLINICAL_RESOURCE_PATTERN = (
    f"^({'|'.join(PATIENT_CLINICAL_RESOURCES)})$"
)


# =====================================================
# CLINICAL RESOURCE HELPER
# =====================================================

async def _create_patient_clinical_resource(
    *,
    db: AsyncSession,
    patient,
    user,
    resource: str,
    payload,
):
    return await ClinicalService.create_resource(
        db=db,
        patient_id=patient.id,
        resource=resource,
        data=payload.model_dump(),
        user_id=user.id,
    )


# =====================================================
# DOCUMENT DATA HELPER
# =====================================================

def create_document_data(
    *,
    request: Request,
    document,
) -> PatientDocumentData:

    # Authenticated document view URL.
    #
    # The frontend will call this endpoint using:
    #
    # Authorization: Bearer <patient token>
    #
    # We no longer put an authentication token
    # in the query string.

    view_url = request.url_for(
        "view_patient_document",
        document_id=str(
            document.id
        ),
    )

    return PatientDocumentData(
        id=document.id,

        patient_id=(
            document.patient_id
        ),

        document_type=(
            document.document_type
        ),

        title=(
            document.title
        ),

        original_file_name=(
            document.original_file_name
        ),

        file_url=str(
            view_url
        ),

        mime_type=(
            document.mime_type
        ),

        file_size=(
            document.file_size
        ),

        uploaded_by=(
            document.uploaded_by
        ),

        created_at=(
            document.created_at
        ),
    )


# =====================================================
# FILE RESPONSE HELPER
# =====================================================

def document_file_response(
    document,
    file_path,
) -> FileResponse:

    return FileResponse(
        path=str(
            file_path
        ),

        media_type=(
            document.mime_type
            or
            "application/octet-stream"
        ),

        filename=(
            document.original_file_name
        ),

        content_disposition_type=(
            "inline"
        ),

        headers={
            "Cache-Control":
                "private, no-store",

            "Referrer-Policy":
                "no-referrer",

            "X-Content-Type-Options":
                "nosniff",
        },
    )


# =====================================================
# VIEW PATIENT DOCUMENT
# =====================================================

@router.get(
    "/documents/{document_id}/view",
    name="view_patient_document",
    status_code=status.HTTP_200_OK,
    summary="View Patient Document",
)
async def view_patient_document(
    current_patient: CurrentPatient,

    document_id: int = Path(
        ...,
        gt=0,
    ),

    db: AsyncSession = Depends(
        get_db
    ),
):
    """
    View a document belonging to the
    currently authenticated patient.

    Authentication:

        Authorization: Bearer <JWT>

    The document must belong to the
    current patient.
    """

    document, file_path = (
        await PatientPortalService.get_document_file(
            db=db,
            patient=current_patient,
            document_id=document_id,
        )
    )

    return document_file_response(
        document,
        file_path,
    )


# =====================================================
# PATIENT DASHBOARD
# =====================================================

@router.get(
    "/dashboard",
    response_model=(
        PatientDashboardResponse
    ),
    status_code=(
        status.HTTP_200_OK
    ),
    summary="Patient Dashboard",
)
async def get_patient_dashboard(
    current_patient: CurrentPatient,

    db: AsyncSession = Depends(
        get_db
    ),
):
    dashboard = (
        await PatientPortalService.get_dashboard(
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


# =====================================================
# GET PATIENT PROFILE
# =====================================================

@router.get(
    "/profile",
    response_model=(
        PatientProfileResponse
    ),
    status_code=(
        status.HTTP_200_OK
    ),
    summary="Get Patient Profile",
)
async def get_patient_profile(
    current_patient: CurrentPatient,
):
    profile = (
        PatientPortalService.get_profile(
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


# =====================================================
# UPDATE PATIENT PROFILE
# =====================================================

@router.patch(
    "/profile",
    response_model=(
        PatientProfileResponse
    ),
    status_code=(
        status.HTTP_200_OK
    ),
    summary="Update Patient Profile",
)
async def update_patient_profile(
    payload: PatientProfileUpdate,

    current_patient: CurrentPatient,

    db: AsyncSession = Depends(
        get_db
    ),
):
    profile = (
        await PatientPortalService.update_profile(
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


# =====================================================
# MEDICAL HISTORY
# =====================================================

@router.put(
    "/medical-history",
    status_code=(
        status.HTTP_200_OK
    ),
    summary="Update Own Medical History",
)
async def update_patient_medical_history(
    payload: MedicalHistoryUpsert,

    current_patient: CurrentPatient,

    current_user: CurrentPatientUser,

    db: AsyncSession = Depends(
        get_db
    ),
):
    return await ClinicalService.upsert_history(
        db=db,
        patient_id=current_patient.id,
        data=payload.model_dump(),
        user_id=current_user.id,
    )


# =====================================================
# CLINICAL SUMMARY
# =====================================================

@router.get(
    "/clinical-summary",
    status_code=(
        status.HTTP_200_OK
    ),
    summary="View Own Clinical Summary",
)
async def get_patient_clinical_summary(
    current_patient: CurrentPatient,

    db: AsyncSession = Depends(
        get_db
    ),
):
    return await ClinicalService.clinical_summary(
        db=db,
        patient_id=current_patient.id,
    )


# =====================================================
# ADMISSION READINESS
# =====================================================

@router.get(
    "/admission-readiness",
    status_code=(
        status.HTTP_200_OK
    ),
    summary="View Own Admission Readiness",
)
async def get_patient_admission_readiness(
    current_patient: CurrentPatient,

    db: AsyncSession = Depends(
        get_db
    ),
):
    return (
        await ClinicalService
        .validate_admission_readiness(
            db=db,
            patient_id=current_patient.id,
        )
    )


# =====================================================
# CONSENT TEMPLATES
# =====================================================

@router.get(
    "/consent-templates",
    status_code=(
        status.HTTP_200_OK
    ),
    summary="List Patient Consent Templates",
)
async def list_patient_consent_templates(
    current_patient: CurrentPatient,

    db: AsyncSession = Depends(
        get_db
    ),
):
    return await ClinicalService.list_templates(
        db
    )


# =====================================================
# LIST CLINICAL RESOURCE
# =====================================================

@router.get(
    "/clinical-records/{resource}",
    status_code=(
        status.HTTP_200_OK
    ),
    summary="View Own Clinical Records",
)
async def list_patient_clinical_resource(
    current_patient: CurrentPatient,

    resource: str = Path(
        pattern=(
            CLINICAL_RESOURCE_PATTERN
        )
    ),

    db: AsyncSession = Depends(
        get_db
    ),
):
    return await ClinicalService.list_resource(
        db=db,
        patient_id=current_patient.id,
        resource=resource,
    )


# =====================================================
# CREATE CONDITION
# =====================================================

@router.post(
    "/clinical-records/conditions",
    status_code=(
        status.HTTP_201_CREATED
    ),
    summary="Add Own Medical Condition",
)
async def create_patient_condition(
    payload: ConditionCreate,

    current_patient: CurrentPatient,

    current_user: CurrentPatientUser,

    db: AsyncSession = Depends(
        get_db
    ),
):
    return await _create_patient_clinical_resource(
        db=db,
        patient=current_patient,
        user=current_user,
        resource="conditions",
        payload=payload,
    )


# =====================================================
# CREATE SURGERY
# =====================================================

@router.post(
    "/clinical-records/surgeries",
    status_code=(
        status.HTTP_201_CREATED
    ),
    summary="Add Own Surgery",
)
async def create_patient_surgery(
    payload: SurgeryCreate,

    current_patient: CurrentPatient,

    current_user: CurrentPatientUser,

    db: AsyncSession = Depends(
        get_db
    ),
):
    return await _create_patient_clinical_resource(
        db=db,
        patient=current_patient,
        user=current_user,
        resource="surgeries",
        payload=payload,
    )


# =====================================================
# CREATE MEDICINE
# =====================================================

@router.post(
    "/clinical-records/medicines",
    status_code=(
        status.HTTP_201_CREATED
    ),
    summary="Add Own Medicine",
)
async def create_patient_medicine(
    payload: MedicineCreate,

    current_patient: CurrentPatient,

    current_user: CurrentPatientUser,

    db: AsyncSession = Depends(
        get_db
    ),
):
    return await _create_patient_clinical_resource(
        db=db,
        patient=current_patient,
        user=current_user,
        resource="medicines",
        payload=payload,
    )


# =====================================================
# CREATE ALLERGY
# =====================================================

@router.post(
    "/clinical-records/allergies",
    status_code=(
        status.HTTP_201_CREATED
    ),
    summary="Add Own Allergy",
)
async def create_patient_allergy(
    payload: AllergyCreate,

    current_patient: CurrentPatient,

    current_user: CurrentPatientUser,

    db: AsyncSession = Depends(
        get_db
    ),
):
    return await _create_patient_clinical_resource(
        db=db,
        patient=current_patient,
        user=current_user,
        resource="allergies",
        payload=payload,
    )


# =====================================================
# CREATE EMERGENCY CONTACT
# =====================================================

@router.post(
    "/clinical-records/emergency-contacts",
    status_code=(
        status.HTTP_201_CREATED
    ),
    summary="Add Own Emergency Contact",
)
async def create_patient_emergency_contact(
    payload: EmergencyContactCreate,

    current_patient: CurrentPatient,

    current_user: CurrentPatientUser,

    db: AsyncSession = Depends(
        get_db
    ),
):
    return await _create_patient_clinical_resource(
        db=db,
        patient=current_patient,
        user=current_user,
        resource="emergency-contacts",
        payload=payload,
    )


# =====================================================
# CREATE CONSENT
# =====================================================

@router.post(
    "/clinical-records/consents",
    status_code=(
        status.HTTP_201_CREATED
    ),
    summary="Capture Own Consent",
)
async def create_patient_consent(
    payload: PatientConsentCreate,

    current_patient: CurrentPatient,

    current_user: CurrentPatientUser,

    db: AsyncSession = Depends(
        get_db
    ),
):
    return await _create_patient_clinical_resource(
        db=db,
        patient=current_patient,
        user=current_user,
        resource="consents",
        payload=payload,
    )


# =====================================================
# UPDATE CLINICAL RESOURCE
# =====================================================

@router.patch(
    "/clinical-records/{resource}/{item_id}",
    status_code=(
        status.HTTP_200_OK
    ),
    summary="Update Own Clinical Record",
)
async def update_patient_clinical_resource(
    payload: dict,

    current_patient: CurrentPatient,

    current_user: CurrentPatientUser,

    resource: str = Path(
        pattern=(
            CLINICAL_RESOURCE_PATTERN
        )
    ),

    item_id: int = Path(
        gt=0
    ),

    db: AsyncSession = Depends(
        get_db
    ),
):
    return await ClinicalService.update_resource(
        db=db,
        patient_id=current_patient.id,
        resource=resource,
        item_id=item_id,
        data=payload,
        user_id=current_user.id,
    )


# =====================================================
# DELETE CLINICAL RESOURCE
# =====================================================

@router.delete(
    "/clinical-records/{resource}/{item_id}",
    status_code=(
        status.HTTP_200_OK
    ),
    summary="Delete Own Clinical Record",
)
async def delete_patient_clinical_resource(
    current_patient: CurrentPatient,

    current_user: CurrentPatientUser,

    resource: str = Path(
        pattern=(
            CLINICAL_RESOURCE_PATTERN
        )
    ),

    item_id: int = Path(
        gt=0
    ),

    db: AsyncSession = Depends(
        get_db
    ),
):
    return await ClinicalService.delete_resource(
        db=db,
        patient_id=current_patient.id,
        resource=resource,
        item_id=item_id,
        user_id=current_user.id,
    )


# =====================================================
# REVOKE CONSENT
# =====================================================

@router.post(
    "/consents/{consent_id}/revoke",
    status_code=(
        status.HTTP_200_OK
    ),
    summary="Revoke Own Consent",
)
async def revoke_patient_consent(
    current_patient: CurrentPatient,

    consent_id: int = Path(
        gt=0
    ),

    db: AsyncSession = Depends(
        get_db
    ),
):
    return await ClinicalService.revoke_consent(
        db=db,
        patient_id=current_patient.id,
        consent_id=consent_id,
    )


# =====================================================
# LIST PATIENT DOCUMENTS
# =====================================================

@router.get(
    "/documents",
    response_model=(
        PatientDocumentListResponse
    ),
    status_code=(
        status.HTTP_200_OK
    ),
    summary="List Patient Documents",
)
async def list_patient_documents(
    request: Request,

    current_patient: CurrentPatient,

    db: AsyncSession = Depends(
        get_db
    ),
):
    documents = (
        await PatientPortalService.list_documents(
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
            total=len(
                document_items
            ),
        ),
    )


# =====================================================
# UPLOAD PATIENT DOCUMENT
# =====================================================

@router.post(
    "/documents",
    response_model=(
        PatientDocumentResponse
    ),
    status_code=(
        status.HTTP_201_CREATED
    ),
    summary="Upload Patient Document",
)
async def upload_patient_document(
    request: Request,

    current_patient: CurrentPatient,

    current_user: CurrentPatientUser,

    db: AsyncSession = Depends(
        get_db
    ),

    document_type: DocumentType = Form(
        ...
    ),

    title: str = Form(
        ...,
        min_length=1,
        max_length=255,
    ),

    file: UploadFile = File(
        ...
    ),
):
    document = (
        await PatientPortalService.upload_document(
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


# =====================================================
# DOWNLOAD PATIENT DOCUMENT
# =====================================================

@router.get(
    "/documents/{document_id}/download",
    name="download_patient_document",
    status_code=(
        status.HTTP_200_OK
    ),
    summary="Download Patient Document",
)
async def download_patient_document(
    current_patient: CurrentPatient,

    document_id: int = Path(
        ...,
        gt=0,
    ),

    db: AsyncSession = Depends(
        get_db
    ),
):
    document, file_path = (
        await PatientPortalService.get_document_file(
            db=db,
            patient=current_patient,
            document_id=document_id,
        )
    )

    # Browser may still display PDFs
    # depending on browser behavior.
    #
    # If you specifically want forced
    # download, create a separate
    # attachment response.
    return document_file_response(
        document,
        file_path,
    )


# =====================================================
# DELETE PATIENT DOCUMENT
# =====================================================

@router.delete(
    "/documents/{document_id}",
    response_model=(
        PatientDocumentDeleteResponse
    ),
    status_code=(
        status.HTTP_200_OK
    ),
    summary="Delete Patient Document",
)
async def delete_patient_document(
    current_patient: CurrentPatient,

    document_id: int = Path(
        ...,
        gt=0,
    ),

    db: AsyncSession = Depends(
        get_db
    ),
):
    document = (
        await PatientPortalService.delete_document(
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
            "document_id":
                document.id,
        },
    )