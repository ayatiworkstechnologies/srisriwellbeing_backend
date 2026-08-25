# Sri Sri Wellbeing Frontend Implementation Report

**Date:** 2026-08-25  
**Backend:** FastAPI, SQLAlchemy, PostgreSQL, JWT, RBAC  
**Status:** Frontend planning and implementation specification

## 1. Executive Summary

This repository contains the backend for Sri Sri Wellbeing Therapy Centre. No frontend project or separate product requirements document currently exists, so this report uses the backend routes, schemas, permissions, tests, and README as the implementation source of truth.

The frontend should be treated as two connected applications:

1. A patient portal for self-service healthcare access.
2. A staff operations portal for reception, clinical, administration, pharmacy, and reporting workflows.

The patient portal is sufficiently defined for an MVP. The staff portal is broader and should be delivered incrementally using permission-driven navigation and controls.

## 2. Product Scope

### 2.1 Patient Portal

Patients can:

- Register and authenticate.
- View a dashboard and personal status.
- View and update their profile.
- Maintain medical history.
- View and manage clinical records.
- Manage conditions, surgeries, medicines, allergies, and emergency contacts.
- Review consent templates and patient consents.
- Upload, view, download, and delete documents.
- View admission readiness.
- Browse appointment availability.
- Book appointments.
- View appointment history and appointment details.

### 2.2 Staff Operations Portal

Staff functionality covers:

- Authentication, profile, password, and session management.
- Patient registration, search, duplicate detection, and lifecycle management.
- Appointment scheduling, calendar, doctor availability, slots, and waiting lists.
- Reception check-in and appointment status workflows.
- Duty doctor consultations, notes, vitals, diagnoses, referrals, and case sharing.
- Specialist doctor workflows.
- Therapist workflows and therapy sessions.
- Pharmacy, prescriptions, inventory, billing, and payments.
- Users, roles, permissions, audit logs, reports, and settings.

## 3. Existing Backend Contract

The API router is assembled in `app/api/router.py`. The canonical versioned prefix is `/api/v1`, configured in `app/core/config.py`.

Use this frontend environment variable:

```text
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

The backend also exposes `/api` compatibility routes. New frontend code should use `/api/v1`.

FastAPI documentation is available at:

```text
/docs
/redoc
/openapi.json
```

CORS currently allows frontend development origins on ports `3000` and `127.0.0.1:3000`.

## 4. Recommended Frontend Architecture

If the frontend is created from scratch, use:

- React with TypeScript.
- React Router for application navigation.
- TanStack Query for server state, caching, and mutations.
- React Hook Form for forms.
- A schema validation library matching the project standard.
- A shared component system.
- OpenAPI-generated types where practical.
- Centralized authentication and permission state.

Recommended feature-oriented structure:

```text
src/
  app/
    config/
    providers/
    router/
  auth/
    api/
    components/
    hooks/
    store/
  patient/
    dashboard/
    profile/
    appointments/
    clinical-records/
    documents/
    consents/
  staff/
    dashboard/
    patients/
    appointments/
    consultations/
    therapy/
    pharmacy/
    inventory/
    billing/
    users/
    roles/
    audit-logs/
    reports/
  components/
    forms/
    tables/
    dialogs/
    feedback/
  lib/
    api-client/
    errors/
    dates/
    permissions/
  types/
```

Keep API calls and response mapping outside presentation components.

## 5. Authentication

### 5.1 Staff Authentication

Staff endpoints are under `/auth` and include:

- `POST /auth/login`
- `POST /auth/logout`
- `POST /auth/refresh`
- `GET /auth/me`
- `GET /auth/sessions`
- `DELETE /auth/sessions/{session_id}`
- `POST /auth/logout-all`
- `POST /auth/change-password`
- Password reset endpoints

Staff login sets an HTTP-only `access_token` cookie and returns authentication data.

### 5.2 Patient Authentication

Patient endpoints are under `/patient-auth`:

- `POST /patient-auth/register`
- `POST /patient-auth/login`
- `POST /patient-auth/logout`

Patient login is restricted to users with the `patient` role. Its implementation is in `app/modules/patients/portal/auth_router.py`.

### 5.3 Frontend Authentication Rules

The API client must:

- Attach `Authorization: Bearer <token>` to protected requests.
- Refresh expired access tokens when possible.
- Prevent multiple simultaneous refresh requests.
- Clear authentication state after refresh failure.
- Redirect users to the correct staff or patient login screen.
- Handle `401` as an authentication failure.
- Handle `403` as a permission or account-status failure.
- Support logout and local state cleanup.
- Avoid storing sensitive data unnecessarily in local storage.

There is currently an inconsistency: staff login sets an access-token cookie, while patient login returns bearer tokens without using the same response-cookie behavior. This should be standardized before production.

## 6. Patient Screen Map

### Public Screens

- Patient login.
- Patient registration.
- Forgot password.
- Password reset.
- Authentication error states.

### Authenticated Screens

- Dashboard.
- Profile and edit profile.
- Medical history.
- Clinical summary.
- Admission readiness.
- Conditions.
- Surgeries.
- Medicines.
- Allergies.
- Emergency contacts.
- Consent templates.
- Patient consents.
- Documents.
- Appointment list.
- Appointment details.
- Book appointment.

The dashboard response provides patient identity, contact information, date of birth, gender, blood group, account status, upcoming appointment count, and document/report count.

The backend currently returns `0` for active prescriptions and pending payments. These should be displayed as unavailable or deferred rather than presented as fully implemented live features.

## 7. Patient Appointment Flow

The patient booking flow should be:

1. Select a doctor.
2. Select an appointment date.
3. Fetch available slots.
4. Select an available slot.
5. Enter the visit reason.
6. Optionally enter notes.
7. Submit the booking.
8. Display the appointment number and status.

Relevant endpoints:

```text
GET  /patient/appointments/available-slots
POST /patient/appointments
GET  /patient/appointments
GET  /patient/appointments/{appointment_id}
```

Only patients with active status can book appointments. The backend enforces this restriction, so the frontend must handle a `403` even if the UI disables the booking action.

The patient booking payload accepts `slot_id`, optional `doctor_id`, an optional reason, and optional notes.

## 8. Patient Clinical Records

The portal supports these resources:

- `conditions`
- `surgeries`
- `medicines`
- `allergies`
- `emergency-contacts`
- `consents`

The frontend should use shared list and form patterns for these resources:

- Resource list.
- Loading state.
- Empty state.
- Create dialog.
- Edit dialog.
- Delete confirmation.
- Success feedback.
- Validation and API error display.

Medical history uses `PUT /patient/medical-history`. Clinical summary and admission readiness are read-only patient views.

## 9. Documents

Document endpoints include:

```text
GET    /patient/documents
POST   /patient/documents
DELETE /patient/documents/{document_id}
GET    /patient/documents/{document_id}/view
GET    /patient/documents/{document_id}/download
```

Uploads use multipart form data.

Document view URLs require the authenticated bearer header. They must not be treated as public URLs. The frontend should fetch the document as a blob, create a temporary object URL, display or download it, and revoke the object URL afterward.

The document URL must never include an access token in its query string.

## 10. Staff Screen Map

### Staff Authentication

- Staff login.
- Forgot password.
- Password reset.
- Change password.
- Current profile.
- Active sessions.
- Session revocation.
- Logout all sessions.

### Patient Management

- Patient list.
- Patient search.
- Patient registration.
- Patient detail.
- Address and identifier views.
- Duplicate match review.
- Activate, deactivate, archive, and restore.
- Patient documents.
- Patient clinical summary.

### Appointment Operations

- Appointment calendar.
- Appointment list and detail.
- Create and update appointment.
- Confirm appointment.
- Reschedule and cancel.
- Check in patient.
- Start and complete consultation.
- Mark no-show.
- Waiting list.
- Doctor availability.
- Slot blocking.
- Duty doctor selection.

### Clinical Operations

- Duty doctor consultation list.
- Consultation detail.
- Clinical notes.
- Vitals.
- Diagnoses.
- Referrals.
- Case sharing.
- Specialist recommendations.
- Treatment plan workflows.
- Therapy sessions.

### Administration

- User list and details.
- Create and edit staff user.
- Activate, deactivate, suspend, and unsuspend users.
- Assign and remove roles.
- View user activity.
- Role list and details.
- Permission assignment.
- Audit logs.
- Audit export.
- Reports and settings.

## 11. RBAC and Navigation

Default roles are defined in `seeds/roles_seed.py`:

- `admin`
- `receptionist`
- `duty_doctor`
- `specialist_doctor`
- `therapist`
- `pharmacist`
- `patient`

Navigation and action controls must be based on permission codes rather than role names alone. Example permissions include:

```text
users.view
users.create
patient.view
patient.search
appointments.view
appointments.create
appointment_slots.manage
consultations.create
consultations.view_own
rbac.manage
audit_logs.view
```

Frontend permission checks are for usability only. Every protected action must still handle a backend `403`.

Admin must not be assumed to have clinical treatment-plan permissions. The backend specifically restricts treatment-plan operations to clinical roles.

## 12. Shared UI Requirements

Every data-driven screen should provide:

- Loading state.
- Empty state.
- Error state with retry.
- Success feedback.
- Pagination where supported.
- Search and filters where supported.
- Confirmation for destructive actions.
- Accessible labels and keyboard navigation.
- Responsive behavior.
- Localized date and time formatting.
- Consistent status badges.

Recommended reusable components:

- `DataTable`
- `Pagination`
- `SearchInput`
- `FilterBar`
- `StatusBadge`
- `FormDialog`
- `ConfirmDialog`
- `FileUploader`
- `DatePicker`
- `TimeSlotPicker`
- `Toast`
- `EmptyState`
- `ErrorState`
- `PermissionGate`

## 13. API Response and Error Handling

Many endpoints return an envelope similar to:

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {}
}
```

Some routes return raw lists or different shapes. Response parsing should therefore be implemented in typed feature adapters rather than assumed globally.

Normalize errors for use by UI components:

```ts
type ApiError = {
  status: number;
  message: string;
  fields?: Record<string, string>;
};
```

The frontend should explicitly handle:

- `401` authentication failure.
- `403` permission or inactive-account failure.
- `404` missing resource.
- `409` duplicate or state conflict.
- `422` validation failure.
- `500` unexpected server failure.

## 14. Backend Gaps and Decisions Required

Before production frontend work, resolve or document:

1. Staff and patient cookie/token behavior.
2. Standard API response envelopes.
3. Pagination format for all list endpoints.
4. Appointment timezone rules.
5. Document MIME types and size limits.
6. Supported document types.
7. Patient cancellation and rescheduling rules.
8. Current-user role and permission retrieval.
9. Notification behavior for bookings and reminders.
10. Production patient-file storage behavior.
11. Exact staff MVP scope.
12. Whether prescriptions, payments, and notifications are included in the first release.
13. Availability of stable seeded data for frontend development.
14. Expected deployment URL and CORS origins.

## 15. Delivery Plan

### Phase 1: Frontend Foundation

- Create the frontend project.
- Configure environment variables.
- Implement API client and types.
- Add authentication state.
- Add refresh handling.
- Add protected routes.
- Add shared loading, empty, error, and form components.

### Phase 2: Patient MVP

- Patient registration.
- Patient login and logout.
- Dashboard.
- Profile.
- Medical history.
- Appointment booking.
- Appointment history.
- Document management.

### Phase 3: Patient Clinical Features

- Clinical summary.
- Admission readiness.
- Conditions.
- Surgeries.
- Medicines.
- Allergies.
- Emergency contacts.
- Consent templates and consents.

### Phase 4: Staff Foundation

- Staff login.
- Staff dashboard.
- Permission-aware navigation.
- Staff profile.
- Session management.

### Phase 5: Core Operations

- Patients.
- Appointments.
- Doctor availability.
- Waiting list.
- Check-in.
- Calendar.

### Phase 6: Clinical and Administration

- Consultations.
- Diagnoses.
- Referrals.
- Case sharing.
- Treatment plans.
- Pharmacy.
- Inventory.
- Billing.
- RBAC.
- Audit logs.
- Reports.

## 16. Testing Strategy

Frontend tests should cover:

- Registration validation.
- Login success and failure.
- Token refresh.
- Logout.
- Protected-route redirects.
- Permission-based navigation and controls.
- Profile updates.
- Appointment slot selection.
- Appointment booking failures.
- Document upload and blob viewing.
- Clinical record CRUD.
- Pagination and search.
- Inactive patient behavior.
- `401`, `403`, `404`, `409`, and `422` responses.

Existing backend tests relevant to integration include `tests/test_patient_portal_api.py`, `tests/test_auth.py`, `tests/test_rbac.py`, and the appointment tests under `tests/appointments`.

## 17. Final Recommendation

Implement the patient portal first because its backend contract and user journey are clearly defined. Build shared authentication, API, types, error handling, and UI foundations so the staff portal can reuse them.

Treat the staff portal as a separate operations product rather than extending the patient UI with additional menus. Its workflows, permissions, data density, and error handling requirements are substantially different.

The highest-priority backend decisions are authentication consistency, response standardization, pagination, document access, appointment timezone behavior, and the exact staff MVP scope.
