# Git Branching and Release

FORGEOS (this repo) and every **managed project** use the same model: **trunk-based development + SemVer tags**. There is no long-lived `develop` branch and no forever-branch named `production`.

## Branch model

```text
main                 # always releasable; protected
  └── feature/<slug> # short-lived work (Frontend, Backend, Database, DevOps roles)
  └── release/x.y.z  # optional freeze branch for a tagged release
  └── hotfix/<slug>  # urgent fix from a tagged production commit

tags: vX.Y.Z         # immutable release markers (GitHub Releases from v*)
```

### What “production” means

**Production** is `main` at a given tag `vX.Y.Z` (or a deploy target pinned to that tag) — not a separate permanent branch.

## Rules

1. **Never commit directly to `main`** from a coding role. Always work on `feature/<slug>` (or `hotfix/<slug>`), then merge after QA pass.
2. **Short-lived features.** Prefer small branches merged often over long-running feature branches.
3. **Protected `main`.** PR (or equivalent merge gate) required; CI (when present) must pass.
4. **Same rules for FORGEOS engine and managed apps.**

## Naming

| Type | Pattern | Example |
|---|---|---|
| Feature | `feature/<slug>` | `feature/auth-login` |
| Hotfix | `hotfix/<slug>` | `hotfix/session-expiry` |
| Release freeze | `release/x.y.z` | `release/1.2.0` |
| Tag | `vX.Y.Z` | `v0.1.0`, `v1.2.3` |

Slugs: lowercase, hyphen-separated, no spaces.

## Commit messages

Prefer Conventional Commits on feature branches:

```text
feat(auth): add login endpoint
fix(api): handle duplicate email
docs(readme): link architecture pack
chore(docker): add healthcheck for backend
```

FORGEOS may auto-commit on `feature/*` with messages in this style.

## SemVer

| Bump | When |
|---|---|
| **MAJOR** (`X.0.0`) | Breaking API or data migration that clients must change |
| **MINOR** (`x.Y.0`) | Backward-compatible feature |
| **PATCH** (`x.y.Z`) | Bug fix, docs, non-breaking chores |

API path versioning (`/api/v1` → `/api/v2`) is related but separate; see [API_VERSIONING.md](API_VERSIONING.md). A breaking HTTP API usually implies a MAJOR release tag.

## Release flow

```text
feature/* work
  → QA pass
  → Documentation + CHANGELOG
  → merge to main
  → (optional) release/x.y.z freeze + final QA
  → human approval (for managed project v0.1+ and engine releases)
  → git tag vX.Y.Z
  → GitHub Release from tag
```

Tags are created only after QA + Docs + **human approval** for meaningful releases. Do not auto-tag every merge.

## Hotfix flow

```text
Identify tag in production (e.g. v1.2.3)
  → git checkout -b hotfix/<slug> v1.2.3
  → fix + tests + QA
  → merge to main
  → tag v1.2.4 (PATCH)
```

If a `release/*` branch still exists for an unfinished train, merge the hotfix there too.

## GitHub

- Default branch: `main`
- Releases: created from tags matching `v*`
- CI (later phases): on PRs into `main` and on tags
- Branch protection: require PR review/CI when collaboration expands; for solo local use, FORGEOS still simulates the gate via QA + human approval roles

## Role constraints

| Role | Git behavior |
|---|---|
| Frontend / Backend / Database / DevOps | Commit only on `feature/*` or `hotfix/*` |
| QA / Reporter / CEO / PM / Architect / UIUX / Documentation | Do not push product implementation commits (Docs may commit doc-only changes on `feature/*`) |
| Anyone | No force-push to `main`; no `git reset --hard` on shared history without CRITICAL approval |
