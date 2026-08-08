from pathlib import Path
from urllib.request import urlopen

from forgeos.cli import main
from forgeos.core import world_state as ws
from forgeos.dashboard.server import make_server
from forgeos.safety.approval import ApprovalStore


def test_dashboard_http_home_and_project(workspace: Path) -> None:
    assert main(["init", "web-demo"]) == 0
    httpd = make_server(workspace, host="127.0.0.1", port=0)
    host, port = httpd.server_address[:2]
    import threading

    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        home = urlopen(f"http://{host}:{port}/", timeout=5).read().decode("utf-8")
        assert "FORGEOS" in home
        assert "web-demo" in home
        page = urlopen(f"http://{host}:{port}/p/web-demo", timeout=5).read().decode("utf-8")
        assert "web-demo" in page
        assert "Health" in page
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_dashboard_refuse_remote_without_flag(capsys) -> None:
    assert main(["dashboard", "--host", "0.0.0.0", "--port", "8765"]) == 1
    err = capsys.readouterr().err
    assert "refusing" in err.lower()


def test_dashboard_approve_via_action(workspace: Path) -> None:
    assert main(["init", "web-appr"]) == 0
    root = ws.project_root(workspace, "web-appr")
    ticket = ApprovalStore(root).request(
        project_name="web-appr",
        task_id="t1",
        action={"tool": "filesystem.delete", "path": "x"},
        risk="critical",
        reason="test",
    )
    from forgeos.dashboard import actions

    actions.approve(root, ticket["id"])
    pending = ApprovalStore(root).list_pending()
    assert not any(t["id"] == ticket["id"] for t in pending)
