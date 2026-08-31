# Duty Doctor Frontend Implementation Guide

## 1. Purpose

This document describes the staff frontend for a Duty Doctor. It covers:

- authentication and permission-based navigation;
- managing the logged-in doctor's weekly availability;
- viewing generated appointment slots;
- viewing the assigned appointment queue;
- starting and completing consultations;
- recording vitals, notes, diagnoses and referrals;
- sharing a case and viewing patient history.

New frontend code must use the `/api/v1` API prefix. All protected requests must
send the staff access token.

## 2. Duty Doctor Navigation

Recommended navigation:

```text
Duty Doctor Dashboard
├── My Appointments
├── My Consultations
├── My Availability
└── Patient History (opened from a consultation)
```

Load the authenticated staff member's identity on application startup:

```http
GET /api/v1/auth/me
```

The login response contains `roles` and `permissions`; `/auth/me` currently
returns profile information but does not repeat those two fields. Persist the
selected role and permission list from login. After token refresh, the new JWT
also contains `roles` and `permissions`, which may be decoded for UI state only.
Backend authorization remains authoritative. Use permission codes to control
navigation and action visibility, and always handle backend `403` responses.

Important Duty Doctor permissions:

```text
appointments.view
appointments.consult
appointments.complete
appointment_slots.view
doctor_availability.view
doctor_availability.manage_own
consultations.create
consultations.view_own
consultations.update
consultations.status
consultations.history
patient_vitals.view
patient_vitals.manage
clinical_notes.view
clinical_notes.manage
diagnoses.view
diagnoses.manage
specialist_referrals.view
specialist_referrals.manage
case_shares.view
case_shares.manage
```

`doctor_availability.manage` is the administrator permission for managing any
doctor. Duty Doctors receive `doctor_availability.manage_own` and can modify only
availability records belonging to their authenticated user ID.

## 3. Suggested Frontend Structure

```text
src/
├── api/
│   ├── appointments.ts
│   ├── availability.ts
│   └── consultations.ts
├── features/duty-doctor/
│   ├── dashboard/
│   ├── appointments/
│   ├── availability/
│   └── consultations/
├── hooks/
│   ├── useAuth.ts
│   └── usePermission.ts
└── types/
    ├── appointment.ts
    ├── availability.ts
    └── consultation.ts
```

Recommended routes:

```text
/duty-doctor
/duty-doctor/appointments
/duty-doctor/availability
/duty-doctor/consultations
/duty-doctor/consultations/:consultationId
```

## 4. My Availability Screen

The doctor records recurring weekly availability, not individual appointment
slots. Slots are generated automatically when a date is requested.

### 4.1 Screen layout

```text
My Weekly Availability                         [Add Availability]

Monday
  09:00 - 13:00    30-minute slots       [Edit] [Disable]
  15:00 - 18:00    30-minute slots       [Edit] [Disable]

Tuesday
  No availability
```

The form fields are:

- day of week;
- start time;
- end time;
- slot duration in minutes;
- active/inactive state.

Day values use Python weekday numbering:

| Value | Day |
|---:|---|
| 0 | Monday |
| 1 | Tuesday |
| 2 | Wednesday |
| 3 | Thursday |
| 4 | Friday |
| 5 | Saturday |
| 6 | Sunday |

### 4.2 Load availability

Use the authenticated user's ID returned by `/auth/me`:

```http
GET /api/v1/doctor-availability/{currentUser.id}
```

### 4.3 Add availability

```http
POST /api/v1/doctor-availability
Content-Type: application/json
```

```json
{
  "doctor_id": 7,
  "day_of_week": 0,
  "start_time": "09:00:00",
  "end_time": "13:00:00",
  "slot_duration_minutes": 30,
  "is_active": true
}
```

Always set `doctor_id` from authenticated state. Do not allow the doctor to
enter or change this value in the form.

### 4.4 Update availability

```http
PUT /api/v1/doctor-availability/{availabilityId}
```

Only changed fields are required:

```json
{
  "day_of_week": 0,
  "start_time": "10:00:00",
  "end_time": "14:00:00",
  "slot_duration_minutes": 20,
  "is_active": true
}
```

After a successful update, invalidate both the availability query and all
future-slot queries for that doctor. The backend clears affected future
unbooked slots; they are regenerated with the new schedule when requested.
Booked slots and manually blocked slots are preserved.

### 4.5 Disable availability

```http
DELETE /api/v1/doctor-availability/{availabilityId}
```

This disables the recurring schedule. Ask for confirmation before sending the
request. Future unbooked slots for the affected weekday are cleared. Existing
bookings remain unchanged.

### 4.6 Availability validation

- `start_time` must be before `end_time`.
- `slot_duration_minutes` must be between 5 and 240.
- `day_of_week` must be between 0 and 6.
- Show a validation message before submission when possible.
- Treat backend `403` as an ownership or permission failure.
- Treat `409` as a conflicting or no-longer-valid operation.
- Display the backend `detail` value for `422` validation errors.

### 4.7 Preview generated slots

```http
GET /api/v1/appointments/available-slots
    ?doctor_id={currentUser.id}
    &appointment_date=2026-09-01
```

The response is wrapped in `data`:

```json
{
  "success": true,
  "message": "Available slots fetched successfully",
  "data": [
    {
      "id": 101,
      "slot_id": 101,
      "doctor_id": 7,
      "slot_date": "2026-09-01",
      "start_time": "10:00:00",
      "end_time": "10:20:00",
      "is_available": true,
      "is_blocked": false,
      "appointment_id": null
    }
  ]
}
```

Past dates cannot generate slots. For the current date, only future times are
returned as bookable.

## 5. Appointment Queue

Load appointments assigned to the logged-in doctor:

```http
GET /api/v1/appointments?doctor_id={currentUser.id}&page=1&limit=20
```

Recommended tabs:

| Tab | Status filter | Main action |
|---|---|---|
| Waiting | `CHECKED_IN` | Start consultation |
| In consultation | `IN_CONSULTATION` | Continue consultation |
| Completed | `COMPLETED` | View record |
| All | none | View appointment |

Appointment status flow:

```text
PENDING -> CONFIRMED -> CHECKED_IN -> IN_CONSULTATION -> COMPLETED
```

Reception handles confirmation and check-in. The Duty Doctor takes over when
the appointment reaches `CHECKED_IN`.

## 6. Start Consultation

From a checked-in appointment:

```http
PATCH /api/v1/appointments/{appointmentId}/start-consultation
```

```json
{
  "reason": "Consultation started",
  "notes": null
}
```

The backend verifies that the appointment belongs to the logged-in doctor,
changes it to `IN_CONSULTATION`, and creates the linked consultation. The call
is safe to retry after a network timeout.

Do not also call `POST /consultations` in the normal appointment flow.

After starting, fetch the linked consultation:

```http
GET /api/v1/consultations/by-appointment/{appointmentId}
```

Then navigate to:

```text
/duty-doctor/consultations/{consultationId}
```

## 7. Consultation Workspace

Recommended page:

```text
Patient and Appointment Header
Consultation Status

Tabs
├── Assessment
├── Vitals
├── Clinical Notes
├── Diagnoses
├── Referrals
├── Case Sharing
└── Patient History

[Save Assessment] [Refer] [Complete Consultation]
```

### 7.1 My consultations

```http
GET /api/v1/consultations/my
```

### 7.2 Consultation detail

```http
GET /api/v1/consultations/{consultationId}
```

### 7.3 Save assessment

```http
PATCH /api/v1/consultations/{consultationId}
```

```json
{
  "chief_complaint": "Fever and headache",
  "medical_assessment": "Possible viral infection",
  "clinical_observations": "Patient is conscious and stable",
  "follow_up_instructions": "Review after three days"
}
```

If autosave is implemented, debounce it. Each backend update creates an audit
entry.

### 7.4 Vitals

```http
GET  /api/v1/consultations/{consultationId}/vitals
POST /api/v1/consultations/{consultationId}/vitals
```

```json
{
  "temperature": 98.6,
  "systolic_bp": 120,
  "diastolic_bp": 80,
  "pulse_rate": 72,
  "respiratory_rate": 16,
  "oxygen_saturation": 98,
  "height_cm": 170,
  "weight_kg": 70,
  "notes": null
}
```

BMI is calculated by the backend.

### 7.5 Clinical notes

```http
GET  /api/v1/consultations/{consultationId}/notes
POST /api/v1/consultations/{consultationId}/notes
```

```json
{
  "note_type": "ASSESSMENT",
  "content": "Patient is stable with no respiratory distress."
}
```

Valid note types are `INITIAL`, `ASSESSMENT`, `OBSERVATION` and `FOLLOW_UP`.

### 7.6 Diagnoses

```http
GET  /api/v1/consultations/{consultationId}/diagnoses
POST /api/v1/consultations/{consultationId}/diagnoses
```

```json
{
  "diagnosis_code": "J06.9",
  "diagnosis_name": "Acute upper respiratory infection",
  "diagnosis_type": "PROVISIONAL",
  "is_primary": true,
  "notes": null
}
```

Valid diagnosis types are `PROVISIONAL`, `FINAL` and `DIFFERENTIAL`.

### 7.7 Specialist referrals

```http
GET  /api/v1/consultations/{consultationId}/referrals
POST /api/v1/consultations/{consultationId}/referrals
```

```json
{
  "specialist_id": 25,
  "specialty": "Cardiology",
  "reason": "Further cardiac assessment required",
  "priority": "HIGH",
  "referral_notes": "Review ECG and blood-pressure history"
}
```

Creating a referral changes the consultation status to `REFERRED`. Priorities
are `LOW`, `NORMAL`, `HIGH` and `URGENT`.

Update referral status:

```http
PATCH /api/v1/consultations/{consultationId}/referrals/{referralId}/status
```

```json
{
  "status": "ACCEPTED"
}
```

Supported progression:

```text
PENDING -> ACCEPTED -> COMPLETED
        -> REJECTED
        -> CANCELLED

ACCEPTED -> CANCELLED
```

### 7.8 Case sharing

```http
GET  /api/v1/consultations/{consultationId}/case-shares
POST /api/v1/consultations/{consultationId}/case-shares
```

```json
{
  "shared_with_user_id": 25,
  "share_note": "Please review this patient's diagnosis."
}
```

The recipient must be an active user. A doctor cannot share a case with
themselves.

### 7.9 Patient history

```http
GET /api/v1/duty-doctor/patients/{patientId}/history
```

Display the history newest first and open historical consultations in read-only
mode unless the current doctor owns an active consultation.

## 8. Complete Consultation

Use one completion request. Recommended from the clinical workspace:

```http
PATCH /api/v1/consultations/{consultationId}/status
```

```json
{
  "status": "COMPLETED"
}
```

Completing the consultation also completes the linked appointment. Do not send
a second appointment-completion request.

After success:

1. invalidate the consultation query;
2. invalidate the doctor's appointment queue;
3. make all clinical forms read-only;
4. hide create/update actions;
5. show the appointment completion timestamp when available and a success
   message.

Completed and cancelled consultations are terminal. The backend returns `409`
when clinical changes are attempted after either terminal state.

## 9. Frontend Action Rules

| State | Visible action |
|---|---|
| Appointment `CHECKED_IN` | Start consultation |
| Appointment `IN_CONSULTATION` | Continue consultation |
| Consultation `IN_PROGRESS` | Edit, refer or complete |
| Consultation `REFERRED` | Continue notes or complete |
| Consultation `COMPLETED` | Read-only view |
| Consultation `CANCELLED` | Read-only view |

Buttons should also require the related permission. Never infer clinical write
access from the role name alone.

## 10. API Response Handling

Appointment and availability endpoints generally return an envelope:

```ts
type ApiEnvelope<T> = {
  success: boolean;
  message?: string;
  data: T;
};
```

Duty Doctor consultation endpoints return the resource or list directly. Keep
this difference inside the API client so page components consume normalized
data.

Recommended error behavior:

| Status | Frontend behavior |
|---:|---|
| 401 | Clear authentication and redirect to login |
| 403 | Show permission/ownership error; hide invalid action |
| 404 | Show not found and return to the relevant list |
| 409 | Show workflow conflict and refresh current data |
| 422 | Render field validation messages |
| 500 | Show retry option and preserve unsaved form input |

Prevent duplicate submissions by disabling action buttons while requests are
pending. On a `409`, refetch because another user or browser session may have
changed the appointment, slot or consultation.

## 11. Recommended Implementation Order

1. Authentication state and permission helper.
2. Duty Doctor layout and navigation.
3. My Availability list, add, edit and disable forms.
4. Generated-slot preview.
5. Assigned appointment queue.
6. Start-consultation action and linked-consultation lookup.
7. Consultation assessment and vitals.
8. Notes and diagnoses.
9. Referrals, case sharing and history.
10. Completion flow and read-only state.
11. Loading, empty, error and responsive states.

## 12. Acceptance Checklist

- Duty Doctor can add only their own availability.
- Duty Doctor cannot update or disable another doctor's availability.
- Schedule edits regenerate future unbooked slots.
- Existing booked and blocked slots remain protected.
- Appointment queue is filtered using the logged-in doctor ID.
- Only checked-in appointments show Start Consultation.
- Starting creates or reuses exactly one linked consultation.
- Vitals, notes, diagnoses, referrals and shares refresh after creation.
- Completed and cancelled consultations are read-only.
- Completing a consultation refreshes the appointment queue.
- Navigation and actions use permissions returned by `/auth/me`.
- Every request handles `401`, `403`, `404`, `409` and `422` appropriately.
