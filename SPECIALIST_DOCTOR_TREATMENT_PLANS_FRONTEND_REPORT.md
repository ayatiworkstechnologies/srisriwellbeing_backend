# Specialist Doctor Treatment Plans — Frontend Implementation Report

**Date:** 2026-09-02
**Module:** Specialist Doctor — Treatment Plans  
**Backend:** FastAPI treatment-plan module  
**Frontend status:** API contract ready for creator-flow implementation; production backend release blocked by database migration and dedicated test coverage

## 1. Executive Summary

The treatment-plan backend supports a complete specialist workflow for creating and maintaining clinical plans. It includes therapies, medicines, services, room recommendations, collaborating specialists, server-side pricing, workflow approval, immutable versions, and status history.

The frontend should provide a specialist-only plan list, a multi-section treatment-plan builder, pricing summaries, workflow actions, and plan history. Navigation and controls must use the permissions returned by authentication rather than relying only on the `specialist_doctor` role name.

The canonical API base is:

```text
/api/v1/treatment-plans
```

The backend repository does not contain a frontend application. This document is the implementation contract for the frontend team.

Repository verification on 2026-09-02 confirmed that the router is registered, all 31 treatment-plan endpoints are present, the Week 8 permissions are seeded, and the existing architecture/RBAC/seed checks pass. However, no Alembic revision creates the seven treatment-plan tables, and the repository has no dedicated treatment-plan API or service tests. These are release blockers for production even though local development can create tables through `Base.metadata.create_all`.

## 2. Scope

The specialist doctor frontend must allow an authorized user to:

- List and filter treatment plans created by the specialist.
- Create a treatment plan for a patient, consultation, or referral.
- Maintain clinical summary, goals, duration, and notes.
- Add, edit, and remove therapies.
- Add, edit, and remove medicine recommendations.
- Add, edit, and remove services, procedures, and other items.
- Configure room and stay recommendations.
- Add and remove collaborating specialists.
- View server-calculated pricing.
- Submit a plan for review.
- Start a review and request modifications.
- Complete requested modifications and resubmit the plan.
- Approve and finalize eligible plans.
- Cancel eligible plans with a reason.
- View immutable versions and workflow status history.

## 3. Frontend Routes

Recommended routes:

```text
/specialist/treatment-plans
/specialist/treatment-plans/new
/specialist/treatment-plans/:planId
/specialist/treatment-plans/:planId/versions/:versionId
```

Route guards should require authentication and the appropriate treatment-plan permission.

## 4. Treatment Plan List

### API

```http
GET /api/v1/treatment-plans/my?status={status}&page={page}&limit={limit}
```

Supported query parameters:

| Parameter | Default | Validation |
|---|---:|---|
| `status` | None | Treatment-plan status |
| `page` | `1` | Minimum `1` |
| `limit` | `100` | Minimum `1`, maximum `100` |

### User interface

Provide:

- Page heading and “Create Treatment Plan” button.
- Status filter or status tabs.
- Plan table or responsive card list.
- Loading, error, empty, and retry states.
- Pagination controls.

Recommended columns:

| Column | Source field |
|---|---|
| Plan | `plan_title` |
| Patient | `patient_id` |
| Consultation | `consultation_id` |
| Referral | `referral_id` |
| Duration | `treatment_duration_days` |
| Version | `current_version` |
| Total | `grand_total` |
| Status | `status` |

The response is a plain array. It does not include total-row or total-page metadata.

## 5. Create Treatment Plan

### Permission

```text
treatment_plans.create
```

### API

```http
POST /api/v1/treatment-plans
```

Example request:

```json
{
  "patient_id": 123,
  "consultation_id": 45,
  "referral_id": 18,
  "plan_title": "Post-consultation wellness plan",
  "clinical_summary": "",
  "treatment_goal": "",
  "treatment_duration_days": 14,
  "notes": ""
}
```

Validation rules:

- `patient_id` must be a positive integer.
- `consultation_id` and `referral_id` are optional positive integers.
- `plan_title` is required and limited to 255 characters.
- `treatment_duration_days` must be between 1 and 3650 when provided.
- `stay_duration_days` must be between 0 and 3650 when provided.
- Room rates cannot be negative.

After successful creation, navigate to the treatment-plan detail page. The backend automatically attaches the creator as the primary specialist.

## 6. Treatment Plan Detail and Builder

### Initial data request

```http
GET /api/v1/treatment-plans/{planId}
```

The response includes:

- Core treatment-plan fields.
- Therapies.
- Medicines.
- Generic items.
- Room and stay information.
- Pricing totals.
- Collaborating specialists.
- Version history.
- Status history.

Recommended builder tabs:

```text
Overview
Therapies
Medicines
Services
Room & Stay
Specialists
Pricing
History
```

Editing is allowed only in these statuses:

```text
DRAFT
MODIFICATION_REQUIRED
MODIFIED
```

All other statuses must display the clinical content as read-only.

### Overview update

```http
PATCH /api/v1/treatment-plans/{planId}
```

Editable fields:

```text
plan_title
clinical_summary
treatment_goal
treatment_duration_days
stay_duration_days
room_type_id
room_name
room_daily_rate
notes
```

The frontend should send only fields changed by the user.

## 7. Therapies

### Permissions

```text
treatment_plan_therapies.view
treatment_plan_therapies.manage
```

### Endpoints

```http
POST   /api/v1/treatment-plans/{planId}/therapies
GET    /api/v1/treatment-plans/{planId}/therapies
PATCH  /api/v1/treatment-plans/{planId}/therapies/{therapyItemId}
DELETE /api/v1/treatment-plans/{planId}/therapies/{therapyItemId}
```

Form fields:

```text
therapy_id
therapy_name
sessions
frequency
duration_days
unit_price
instructions
notes
```

The frontend may show `sessions × unit_price` as a preview. The returned `total_price` remains authoritative.

## 8. Medicines

### Permissions

```text
treatment_plan_medicines.view
treatment_plan_medicines.manage
```

### Endpoints

```http
POST   /api/v1/treatment-plans/{planId}/medicines
GET    /api/v1/treatment-plans/{planId}/medicines
PATCH  /api/v1/treatment-plans/{planId}/medicines/{medicineItemId}
DELETE /api/v1/treatment-plans/{planId}/medicines/{medicineItemId}
```

Form fields:

```text
medicine_id
medicine_name
dosage
frequency
route
duration_days
quantity
unit_price
instructions
notes
```

The returned `total_price` must be used for the persisted line total.

## 9. Services, Procedures, and Other Items

### Permissions

```text
treatment_plan_items.view
treatment_plan_items.manage
```

### Endpoints

```http
POST   /api/v1/treatment-plans/{planId}/items
GET    /api/v1/treatment-plans/{planId}/items
PATCH  /api/v1/treatment-plans/{planId}/items/{itemId}
DELETE /api/v1/treatment-plans/{planId}/items/{itemId}
```

Form fields:

```text
item_type
reference_id
item_name
description
quantity
unit_price
notes
```

Frontend item types should be limited to:

```text
SERVICE
PROCEDURE
OTHER
```

The backend schema also accepts `THERAPY`, `MEDICINE`, and `ROOM`, but generic-item pricing does not include those types. Their dedicated sections must be used instead.

## 10. Room and Stay Recommendation

### API

```http
PUT /api/v1/treatment-plans/{planId}/room
```

Request:

```json
{
  "room_type_id": 4,
  "room_name": "Deluxe Room",
  "stay_duration_days": 10,
  "daily_rate": "2500.00"
}
```

The frontend may preview `stay_duration_days × daily_rate`. The backend-calculated `room_total` is authoritative.

## 11. Collaborating Specialists

### Permissions

```text
treatment_plan_specialists.view
treatment_plan_specialists.manage
```

### Endpoints

```http
POST   /api/v1/treatment-plans/{planId}/specialists
GET    /api/v1/treatment-plans/{planId}/specialists
DELETE /api/v1/treatment-plans/{planId}/specialists/{specialistLinkId}
```

Specialist roles:

```text
PRIMARY_SPECIALIST
CONSULTING_SPECIALIST
REVIEWING_SPECIALIST
```

Rules:

- A specialist cannot be attached twice.
- The primary specialist cannot be removed.
- Removal requires the specialist-link `id`, not the user’s `specialist_id`.
- A user can access a plan when they are its creator or an attached specialist.

## 12. Pricing

### Permission

```text
treatment_plan_pricing.calculate
```

### API

```http
POST /api/v1/treatment-plans/{planId}/calculate
```

Display:

```text
Therapy total
Medicine total
Room total
Service total
Subtotal
Discount
Tax
Grand total
```

All monetary values should be stored as decimal strings in frontend types. Avoid authoritative financial arithmetic using JavaScript floating-point numbers.

Therapy, medicine, item, room, and overview mutations trigger backend price recalculation. The frontend should still refetch full plan details after mutations.

## 13. Workflow

### Status transitions

| Current status | Next status | Frontend action |
|---|---|---|
| `DRAFT` | `SUBMITTED` | Submit |
| `DRAFT` | `CANCELLED` | Cancel |
| `SUBMITTED` | `UNDER_REVIEW` | Start review |
| `SUBMITTED` | `CANCELLED` | Cancel |
| `UNDER_REVIEW` | `MODIFICATION_REQUIRED` | Request modification |
| `UNDER_REVIEW` | `APPROVED` | Approve |
| `UNDER_REVIEW` | `CANCELLED` | Cancel |
| `MODIFICATION_REQUIRED` | `MODIFIED` | Mark changes completed |
| `MODIFICATION_REQUIRED` | `CANCELLED` | Cancel |
| `MODIFIED` | `SUBMITTED` | Resubmit |
| `MODIFIED` | `CANCELLED` | Cancel |
| `APPROVED` | `FINALIZED` | Finalize |

`FINALIZED` and `CANCELLED` are terminal and read-only.

### Workflow endpoints

| Action | Permission | Endpoint |
|---|---|---|
| Submit/resubmit | `treatment_plans.submit` | `POST /{planId}/submit` |
| Start review | `treatment_plans.review` | `POST /{planId}/start-review` |
| Request modification | `treatment_plans.review` | `POST /{planId}/request-modification` |
| Complete modification | `treatment_plans.update` | `POST /{planId}/submit-modification` |
| Approve | `treatment_plans.approve` | `POST /{planId}/approve` |
| Finalize | `treatment_plans.finalize` | `POST /{planId}/finalize` |
| Cancel | `treatment_plans.cancel` | `POST /{planId}/cancel` |

Before submission, the plan must contain:

- Plan title.
- Clinical summary.
- Treatment goal.

Completing a modification moves the plan to `MODIFIED`. It must then be submitted separately to return to `SUBMITTED`.

## 14. Delete Plan

### Permission

```text
treatment_plans.delete
```

### API

```http
DELETE /api/v1/treatment-plans/{planId}
```

Deletion is permitted only when:

- The current specialist is the plan creator.
- The plan status is `DRAFT`.

Use a confirmation dialog and handle the successful `204 No Content` response without attempting JSON parsing.

## 15. Versions and Status History

### Endpoints

```http
GET /api/v1/treatment-plans/{planId}/versions
GET /api/v1/treatment-plans/{planId}/status-history
```

Version records contain:

```text
version_number
created_by
status
snapshot
change_note
```

Status-history records contain:

```text
from_status
to_status
changed_by
reason
notes
```

Create a timeline for workflow history and a read-only viewer for version snapshots.

## 16. Permissions and Navigation

The specialist doctor seed includes all treatment-plan permissions:

```text
treatment_plans.create
treatment_plans.view
treatment_plans.view_own
treatment_plans.update
treatment_plans.delete
treatment_plans.submit
treatment_plans.review
treatment_plans.approve
treatment_plans.finalize
treatment_plans.cancel
treatment_plan_therapies.view
treatment_plan_therapies.manage
treatment_plan_medicines.view
treatment_plan_medicines.manage
treatment_plan_items.view
treatment_plan_items.manage
treatment_plan_specialists.view
treatment_plan_specialists.manage
treatment_plan_pricing.calculate
treatment_plan_versions.view
treatment_plan_status_history.view
```

The seeded admin, receptionist, duty-doctor, therapist, pharmacist, and patient roles receive no Week 8 treatment-plan permissions.

Frontend permission checks improve usability but do not replace backend authorization. Every request must handle `403 Forbidden`.

## 17. State and Query Management

Recommended query keys:

```ts
export const treatmentPlanKeys = {
  all: ["treatment-plans"] as const,
  list: (filters: object) =>
    ["treatment-plans", "list", filters] as const,
  detail: (id: number) =>
    ["treatment-plans", "detail", id] as const,
};
```

After any plan or child mutation, invalidate:

```ts
queryClient.invalidateQueries({
  queryKey: treatmentPlanKeys.detail(planId),
});

queryClient.invalidateQueries({
  queryKey: treatmentPlanKeys.all,
});
```

Use the refreshed full-detail response as the source of truth for pricing, status, versions, and child collections.

## 18. Error Handling

HTTP errors use this shape:

```json
{
  "success": false,
  "message": "Treatment plan cannot be edited while status is SUBMITTED."
}
```

Validation errors include an error code and field details:

```json
{
  "success": false,
  "message": "Validation failed",
  "error_code": "VALIDATION_ERROR",
  "details": []
}
```

Required handling:

| Status | Frontend response |
|---:|---|
| `401` | Refresh authentication or redirect to login |
| `403` | Show access-denied feedback and hide unauthorized controls |
| `404` | Show plan/item not found and provide navigation back |
| `409` | Display workflow, read-only, or duplicate-specialist message |
| `422` | Map validation details to fields and show submission requirements |
| `500` | Show generic error feedback and retry option |

## 19. Backend Gaps and Risks

The specialist creator frontend is implementable against the documented API contract, but the first two items below block a production-ready backend release:

1. **Critical — missing database migration.** The models define `treatment_plans`, `treatment_plan_versions`, `treatment_plan_items`, `treatment_plan_therapies`, `treatment_plan_medicines`, `treatment_plan_specialists`, and `treatment_plan_status_history`, but no Alembic revision creates them. Local development may hide this because application startup runs `Base.metadata.create_all`; staging and production rely on Alembic.
2. **High — no dedicated treatment-plan tests.** There are no Week 8 tests covering endpoint authorization, CRUD operations, pricing, status transitions, version snapshots, collaboration rules, or terminal read-only behavior.
3. `GET /my` returns only plans created by the current user. It does not return plans shared with the specialist.
4. There is no reviewer inbox or endpoint listing plans awaiting the current specialist’s review.
5. Attached reviewers can access a plan only when they already know its ID.
6. Plan lists provide patient and specialist IDs rather than display names.
7. List responses provide no total count, search, sorting, or date fields.
8. Version and status-history responses do not expose timestamps.
9. The room request accepts `notes`, but the service does not persist them.
10. Discount and tax are returned but cannot be modified through treatment-plan endpoints.
11. All specialist doctors receive review, approval, and finalization permissions by default; the backend does not enforce separation of duties between creator, reviewer, and approver.

Recommended backend additions:

- An Alembic revision for every Week 8 treatment-plan table, foreign key, unique constraint, and index.
- Automated API/service tests for the complete treatment-plan lifecycle and permission boundaries.
- An accessible/assigned-plans endpoint.
- A review-queue endpoint.
- Patient and specialist summary objects in list/detail responses.
- Pagination metadata and server-side search.
- Timestamps in version and status-history schemas.
- Explicit workflow responsibility or separation-of-duty rules.

## 20. Acceptance Criteria

The frontend implementation is complete when an authorized specialist doctor can:

- View and filter treatment plans created by them.
- Create a treatment plan from a patient, consultation, or referral.
- Save and update an editable draft.
- Add, update, and remove therapies, medicines, services, and collaborators.
- Configure room and stay recommendations.
- View current server-calculated pricing.
- Submit and resubmit plans with the required clinical information.
- Start review, request modification, approve, finalize, and cancel according to status and permission.
- View immutable version snapshots and workflow history.
- See read-only treatment-plan content in non-editable statuses.
- Receive usable validation, authorization, conflict, and not-found feedback.
- Complete destructive actions only after confirmation.
- Use responsive and accessible controls with loading, empty, error, and success states.

## 21. Delivery Recommendation

Delivery should begin with backend release hardening, followed by three frontend increments:

1. **Backend release gate:** add the Alembic migration and automated lifecycle/authorization tests.
2. **Creator MVP:** list, create, overview, therapies, medicines, services, room, pricing, and draft deletion.
3. **Workflow:** submission, modification, approval, finalization, cancellation, versions, and history.
4. **Collaboration:** assigned-plan list, reviewer inbox, specialist discovery, and responsibility controls after the required backend endpoints are available.

Overall status: **frontend contract ready; production backend release blocked by the missing migration and dedicated tests; complete collaborative review requires additional backend endpoints.**

## 22. Verification Record

Verified against commit `8117a90` on 2026-09-02.

| Check | Result |
|---|---|
| Treatment-plan router registered under `/api/v1/treatment-plans` | Pass |
| CRUD, child-resource, pricing, workflow, version, and history routes present | Pass — 31 endpoints |
| Week 8 permission definitions and Specialist Doctor assignments present | Pass |
| Architecture, RBAC permission-name, and seed tests | Pass — 11 tests |
| Dedicated treatment-plan tests | Fail — none present |
| Alembic migration for treatment-plan tables | Fail — none present |

Verification command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_architecture.py tests\test_rbac_permission_names.py tests\test_seeds.py -q
```

Observed result: `11 passed`.
