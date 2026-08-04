# Sri Sri Wellbeing Backend

FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL, JWT authentication, RBAC,
patient registration, and clinical-record services for the therapy centre.

## Local setup

1. Copy `.env.example` to `.env` and replace `JWT_SECRET_KEY`.
2. Create the virtual environment and install dependencies:

   ```powershell
   python -m venv venv
   .\venv\Scripts\pip.exe install -r requirements.txt
   ```

3. Start PostgreSQL and the API:

   ```powershell
   docker compose up --build
   ```

4. Seed the six default roles and permissions:

   ```powershell
   .\venv\Scripts\python.exe -m app.seeds
   ```

The canonical API is `/api/v1`. Swagger is at `/docs`, ReDoc at `/redoc`,
and health checks are available at `/health` and `/api/v1/health`.

## Environments

Use `.env.development`, `.env.staging`, and `.env.production` based on the
provided example files. Deployment secrets must be supplied by the hosting
platform and must never be committed.

Production and staging schema changes must use:

```powershell
.\venv\Scripts\alembic.exe upgrade head
```

## Modules

- Authentication: access/refresh JWTs, rotation and revocation, sessions,
  login attempts, password reset/change, profile, and account state.
- RBAC: users, roles, permissions, mappings, enforcement, and audit logs.
- Patients: registration, identifiers, address, duplicate detection, search,
  profile updates, portal access, and documents.
- Clinical records: history, conditions, surgeries, medicines, allergy alerts,
  emergency contacts, consent templates, and signed patient consents.

Admin is operational, not clinical. The service rejects assignment of
treatment-plan create/update/prepare/review/approve/finalize permissions to
every role except `duty_doctor` and `specialist_doctor`.

## Git workflow

- Branches: `main`, `develop`, `feature/<ticket>-<name>`,
  `fix/<ticket>-<name>`, and `release/<version>`.
- Commits follow Conventional Commits, for example
  `feat(auth): rotate refresh tokens` or `fix(rbac): restrict clinical access`.
- Pull requests require passing tests, migration review, and no committed
  secrets. Use squash merge for feature branches.

Run validation with:

```powershell
.\venv\Scripts\python.exe -m pytest -q
.\venv\Scripts\python.exe -m flake8 app tests
```
