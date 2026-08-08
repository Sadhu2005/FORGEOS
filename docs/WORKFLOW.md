# End-to-End Workflow

How a single human goal becomes a verified, reported outcome under FORGEOS.

## Pipeline

```text
1. CEO          Understand goal, phases, priorities, world state
2. Product Mgr  Requirements, MVP, acceptance criteria
3. Architect    Stack + boundaries → docs/ARCHITECTURE.md
4. UI/UX        design/*.md
   Database     schema + migrations + database.md
   (graph-parallel; one LLM role at a time)
5. Frontend     implement on feature/* against design + /api/v1
   Backend      implement on feature/* against schema + AC
6. QA           independent verify → pass or fail+replan
7. Documentation  README, API, CHANGELOG, …
8. DevOps       Compose/CI/env; local health
9. Reporter     evidence-backed task report
10. Human       gate for merge to main / tag release
```

## Step detail

### 1. CEO

- Restate the goal
- Open or update `.forge/state.yaml`
- Create phase-level tasks and priorities
- Do not write application code

### 2. Product Manager

- Produce requirements and MVP boundary
- Attach acceptance criteria to features
- Hand off READY tasks for Architect

### 3. Software Architect

- Write project `docs/ARCHITECTURE.md`
- Lock API versioning (`/api/v1`), data stores, auth approach
- Unblock UI/UX and Database (and later Frontend/Backend)

### 4. UI/UX and Database

- UI/UX writes design specs only
- Database writes migrations and `database.md`
- Task graph may mark both READY; orchestrator runs them sequentially

### 5. Frontend and Backend

- Small, verifiable changes on `feature/<slug>`
- Frontend: `frontend/` only; Backend: `backend/` (+ migration apply in sandbox as allowed)
- Commit with Conventional Commits; never straight to `main`

### 6. QA

- Run tests, build, lint, compose config as applicable
- Emit QA report with pass/fail and severity
- On fail: classify, open fix tasks, replan — do not infinite-retry the same broken action

### 7–8. Documentation and DevOps

- Docs match reality; CHANGELOG updated for user-visible changes
- Compose and healthchecks ready for local run

### 9. Reporter

- Summarize evidence: tests, files, commits, QA outcome, next task

### 10. Human gate

- Approve merge to `main` and any `vX.Y.Z` tag (see [GIT_AND_RELEASE.md](GIT_AND_RELEASE.md))

## Failure path

```text
Task failed
  → capture error
  → classify (syntax, dependency, logic, env, …)
  → update task graph
  → replan (often: start dependency service, fix code, re-run QA)
  → after N failed attempts on same root cause → STOP for human
```

## Context discipline

Each LLM turn receives only:

- Current goal and task  
- Project summary from world state  
- Relevant files / errors  
- Allowed tools for the active role  
- Constraints and Definition of Done  

Not: entire repo + full chat history + all logs.

## Success criteria for a milestone

- Acceptance criteria covered  
- QA report green for the milestone scope  
- Docs/CHANGELOG updated  
- Feature branch merged (or ready) per git rules  
- Reporter artifact stored under `.forge/reports/`  

## Phase 1 V1 CLI (engine)

Phase exit criteria for the FORGEOS engine CLI live in [PHASES.md](PHASES.md) (Phase 1 Definition of Done). This workflow doc describes the **managed-project** role pipeline; Phase 1 implements the loop that will later drive that pipeline.

## See also

- [ARCHITECTURE.md](ARCHITECTURE.md) — system loop  
- [ROLES.md](ROLES.md) — permissions per role  
- [DOCKER.md](DOCKER.md) — local runtime  
- [API_VERSIONING.md](API_VERSIONING.md) — `/api/v1`  
- [PHASES.md](PHASES.md) — phase map and Phase 1 DoD  
