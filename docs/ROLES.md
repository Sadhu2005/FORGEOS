# FORGEOS Role Policies

Roles are **policies**, not concurrent agents. Each role is:

```text
Role =
  system prompt
  + allowed filesystem paths
  + allowed tools
  + forbidden actions
  + output artifacts
  + Definition of Done
```

The orchestrator activates exactly one role per LLM turn.

**Canonical machine config:** [`roles/*.yaml`](../roles/) at the repository root (validated by [schemas/role_policy.schema.yaml](schemas/role_policy.schema.yaml)). This markdown file is the human-readable companion; when they disagree, update both in the same change.

## Pipeline

```text
HumanGoal
  → CEO
  → ProductManager
  → SoftwareArchitect
  → UIUX / Database          (task-graph parallel; LLM serial)
  → Frontend / Backend       (task-graph parallel; LLM serial)
  → QA
      → fail → Diagnose → replan (Frontend | Backend | Database)
      → pass → Documentation → DevOps → Reporter → Human
```

## Role matrix

| Role | Writes | May run | Must not |
|---|---|---|---|
| CEO | goals, priorities, phase gates | read project state | write app code |
| Product Manager | requirements, stories, AC, MVP | read | write app code |
| Software Architect | project `docs/ARCHITECTURE.md`, decision records | read, research | write app code |
| UI/UX | `design/*.md` | read | write app code |
| Frontend | `frontend/` | npm, frontend tests, git on `feature/*` | touch `backend/`, production deploy |
| Backend | `backend/` | pytest, sandbox migrations, git on `feature/*` | touch `frontend/`, production deploy |
| Database | `database/` | schema/migration tools | app UI / unrelated app code |
| QA | QA reports only (e.g. `.forge/reports/qa-*`) | pytest, npm test/build, lint, `docker compose config` | “fix” production; may open fix tasks only |
| DevOps | `docker/`, CI configs, env templates | compose up/down locally | cloud/prod deploy without CRITICAL human approval |
| Documentation | project docs + `CHANGELOG.md` | read diffs | silent product code edits without a Docs task |
| Reporter | `.forge/reports/` task reports | read evidence | change product code |

---

## 1. CEO

**Purpose:** Understand the user goal, break work into phases, set priorities, approve/reject plans, track progress.

**Writes:** Goal statement, phase list, priority ordering, gate decisions (in world state / `.forge/`).

**Allowed tools:** Read world state, task graph, reports; create/update high-level tasks; set project phase; `filesystem.read` / `write` / `search` / `tree` under `.forge/**`.

**Forbidden:** Any application source edits under `frontend/`, `backend/`, `database/` (except metadata FORGEOS owns under `.forge/`).

**Definition of Done:**

- Goal restated clearly
- Phases and priorities recorded
- Next role (usually Product Manager) has a READY entry task

---

## 2. Product Manager

**Purpose:** Requirements, user stories, features, acceptance criteria, MVP definition.

**Writes:** e.g. `docs/REQUIREMENTS.md`, feature specs under `docs/features/` (project-level).

**Example artifact:**

```text
Feature: Student registration

Acceptance criteria:
- Phone authentication
- College ID verification
- Profile creation
- Validation
- Error handling
```

**Forbidden:** Application code changes.

**Definition of Done:** MVP scope listed; each in-scope feature has acceptance criteria; out-of-scope explicitly noted.

---

## 3. Software Architect

**Purpose:** Produce architecture for frontend, backend, database, API, auth, security, infrastructure, and local deployment.

**Writes:** Project `docs/ARCHITECTURE.md` (and decision records when needed).

**Default stack (unless a decision record says otherwise):**

```text
Next.js
   │
   ▼
FastAPI  (/api/v1)
   │
   ├── PostgreSQL
   ├── Redis
   └── Object storage (when required)
```

**Forbidden:** Application implementation code.

**Definition of Done:** Architecture doc covers boundaries, stack, API versioning, data stores, and security notes; Frontend/Backend/Database tasks can become READY.

---

## 4. UI/UX

**Purpose:** Pages, components, design system, navigation, responsive behavior, accessibility, UI specs.

**Writes:**

```text
design/
├── design-system.md
├── pages.md
├── components.md
└── user-flows.md
```

**Forbidden:** Implementing React/Next code (that is Frontend).

**Definition of Done:** Specs sufficient for Frontend to implement without inventing major UX.

---

## 5. Frontend

**Purpose:** Implement UI against design specs and versioned APIs.

**Workspace:** `frontend/` only.

**Allowed:** create/edit/search/tree/delete under `frontend/`; `terminal.execute`; `testing.run`; `git.status` / `diff` / `branch` / `commit` on `feature/*` branches.

**Forbidden:** `backend/`, `database/` schema ownership, production deploy, commits directly to `main`.

**Definition of Done:** Files exist; relevant frontend tests/build checks pass (as specified by the task); evidence recorded for QA.

---

## 6. Backend

**Purpose:** APIs, domain logic, auth, tests, API-oriented docs stubs as needed.

**Workspace:** `backend/` (may coordinate with Database role for migrations; does not own `design/`).

**Allowed:** create APIs under `/api/v1`; models; business logic; `filesystem.*` under `backend/`; `terminal.execute`; `testing.run` (pytest); `git.status` / `diff` / `branch` / `commit` on `feature/*`.

**Forbidden:** `frontend/` edits, production deploy, direct commits to `main`.

**Definition of Done:** Endpoints/behavior match acceptance criteria; tests exist and pass for the task; OpenAPI reflects changes.

---

## 7. Database

**Purpose:** Schema, migrations, indexes, relationships, seed data, database documentation.

**Writes:**

```text
database/
├── schema.sql
├── migrations/
│   ├── 001_init.sql
│   └── ...
└── database.md
```

**Allowed tools (Phase 2):** `filesystem.*` under `database/`; `terminal.execute`; `git.status` / `diff` / `branch` / `commit`.

**Forbidden:** Frontend code; unrelated backend feature code outside migration/schema needs.

**Definition of Done:** Migration set is ordered and documented; `database.md` updated; Backend can depend on the schema.

---

## 8. QA

**Purpose:** Independent verification. Developers claim; QA proves.

**Writes:** QA reports only (e.g. `.forge/reports/qa-<id>.md`).

**May run:** `testing.run` (pytest), `terminal.execute`, `docker.compose_config`, local health checks when defined; `filesystem.read` / `search` / `tree`.

**Forbidden:** Shipping “fixes” as silent edits to greenwash results. Failures open fix tasks for coding roles.

**Example report shape:**

```text
QA REPORT
Passed: 24
Failed: 3
Critical: API authentication failure
Recommendation: Fix before merge/release.
```

**Definition of Done:** All task acceptance criteria checked with recorded evidence; pass or fail is explicit.

---

## 9. DevOps

**Purpose:** Dockerfiles, Compose, CI config, env templates, health checks, logging hooks; local deployment first.

**Writes:** `docker/`, CI workflows (when present), `.env.example`.

**Allowed:** `docker.compose_config` and `terminal.execute` locally; `filesystem.*` under `docker/` (and CI/env templates); `git.status` / `diff` / `branch` / `commit`. Compose **up/down** remains a later safety-gated capability.

**Forbidden:** Production/cloud deploy without CRITICAL human approval.

**Definition of Done:** Compose validates; services have healthchecks where applicable; DEPLOYMENT notes updated via Documentation handoff.

---

## 10. Documentation

**Purpose:** Keep living docs accurate after material changes.

**Maintains (project):** `README.md`, `docs/ARCHITECTURE.md`, `docs/API.md`, `docs/DATABASE.md`, `docs/DEPLOYMENT.md`, `CHANGELOG.md`.

**Forbidden:** Drive-by product code changes without a Documentation-scoped task.

**Definition of Done:** Docs match current behavior and CHANGELOG has an entry for user-visible changes.

---

## 11. Reporter

**Purpose:** End-of-task evidence summary for humans.

**Writes:** `.forge/reports/task-<id>.md` (or equivalent).

**Example:**

```text
TASK REPORT
Task: User Authentication
Status: COMPLETED
Frontend: done
Backend: done
Database: done
Tests: 18/18
Files changed: 14
Commits: 3
Next task: Profile system
```

**Forbidden:** Changing product code.

**Definition of Done:** Report cites evidence paths (test output, commits, QA report); next recommended task named if any.

---

## Handoff rules

1. **Artifact gates:** Downstream roles stay BLOCKED until required artifacts exist (e.g. Architect’s `docs/ARCHITECTURE.md` before Frontend/Backend READY).
2. **Path isolation:** Coding roles may only write their allowed trees unless the planner creates an explicit cross-cutting task with elevated approval.
3. **QA independence:** QA never shares a “make it pass” incentive with the last coding role; failures replan.
4. **Git:** Coding and DevOps roles use `feature/*` (or `hotfix/*`); never commit straight to `main`. See [GIT_AND_RELEASE.md](GIT_AND_RELEASE.md).
5. **Human gates:** CRITICAL actions (prod deploy, destructive data ops, secret changes) always require human approval.

## Implementation note

Phase 1+ loads [`roles/*.yaml`](../roles/) and encodes enforcement in `forgeos.roles.loader` / the orchestrator. This document remains the human-readable contract.
