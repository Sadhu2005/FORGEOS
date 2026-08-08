# API Versioning

Public HTTP APIs for managed projects are **versioned in the URL path**. Clients never call unversioned business endpoints.

## Locked rules

1. Current public API lives under **`/api/v1/...`**.
2. A **breaking** change requires **`/api/v2/...`** plus an Architect decision record. Keep `/api/v1` until a deprecation task completes.
3. FastAPI generates OpenAPI/Swagger; the Documentation role syncs human-readable `docs/API.md`.
4. Next.js (or other clients) talk only to versioned routes.

## What counts as breaking (MAJOR / new path version)

- Removing or renaming endpoints or fields clients rely on  
- Changing response shapes or status semantics incompatibly  
- Changing auth requirements in a way that breaks existing clients  
- Incompatible pagination or error envelope changes  

Non-breaking (stay on `/api/v1`, usually MINOR release tag):

- Adding optional fields  
- Adding new endpoints  
- Additive query parameters with safe defaults  

See SemVer for git tags in [GIT_AND_RELEASE.md](GIT_AND_RELEASE.md).

## Backend layout expectation

```text
backend/
  app/
    api/
      v1/
        ...
      # v2/ when introduced
```

Router mount example (conceptual):

```text
app.include_router(..., prefix="/api/v1")
```

## Deprecation

When `/api/v2` ships:

1. Document migration in `docs/API.md` and CHANGELOG  
2. Mark v1 endpoints deprecated in OpenAPI  
3. Track a task graph item to remove v1 after the agreed sunset  
4. Frontend migrates in a dedicated feature branch  

## Health and meta endpoints

Operational endpoints (e.g. `/health`) may sit outside `/api/v1` if Architect documents them as infrastructure, not business API. Business resources always stay under `/api/vN`.
