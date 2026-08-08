from pathlib import Path

from forgeos.core import world_state as ws
from forgeos.safety.audit import AuditLog, audit_path


def test_audit_append_and_read(tmp_path: Path) -> None:
    root = ws.create_project(tmp_path, "aud")
    log = AuditLog(root)
    log.append("permission", "denied", task_id="t1", payload={"kind": "deny"})
    log.append("approval", "pending appr-1", task_id="t1")
    rows = log.read_lines(limit=10)
    assert len(rows) == 2
    assert rows[0]["kind"] == "permission"
    assert rows[1]["kind"] == "approval"
    assert audit_path(root).is_file()
