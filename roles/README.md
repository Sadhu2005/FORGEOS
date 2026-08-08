# Role policies (YAML)

These files are **sequential role policies**, not concurrent agents. Phase 1+ loads them via `forgeos.roles.loader` and validates against [docs/schemas/role_policy.schema.yaml](../docs/schemas/role_policy.schema.yaml).

Human-readable descriptions: [docs/ROLES.md](../docs/ROLES.md).

| File | Role id |
|---|---|
| [ceo.yaml](ceo.yaml) | ceo |
| [product_manager.yaml](product_manager.yaml) | product_manager |
| [software_architect.yaml](software_architect.yaml) | software_architect |
| [ui_ux.yaml](ui_ux.yaml) | ui_ux |
| [frontend.yaml](frontend.yaml) | frontend |
| [backend.yaml](backend.yaml) | backend |
| [database.yaml](database.yaml) | database |
| [qa.yaml](qa.yaml) | qa |
| [devops.yaml](devops.yaml) | devops |
| [documentation.yaml](documentation.yaml) | documentation |
| [reporter.yaml](reporter.yaml) | reporter |
