"""Stdlib HTTP dashboard server."""

from __future__ import annotations

import mimetypes
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from forgeos.core import world_state as ws
from forgeos.dashboard import actions, views

DEFAULT_HOST = "127.0.0.1"
# Avoid common Windows Hyper-V excluded ranges (~8571–9270).
DEFAULT_PORT = 18080
FALLBACK_PORTS = (18080, 19090, 28080, 34567)

class DashboardHandler(BaseHTTPRequestHandler):
    workspace: Path = Path.cwd()

    def log_message(self, fmt: str, *args: Any) -> None:
        # Quiet default logging in tests; CLI can still see prints from serve().
        return

    def _send(self, code: int, body: bytes, content_type: str = "text/html; charset=utf-8") -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, location: str) -> None:
        self.send_response(303)
        self.send_header("Location", location)
        self.end_headers()

    def _read_form(self) -> dict[str, str]:
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length).decode("utf-8") if length else ""
        parsed = parse_qs(raw, keep_blank_values=True)
        return {k: (v[0] if v else "") for k, v in parsed.items()}

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/static/"):
            rel = path[len("/static/") :]
            file_path = (views.STATIC_DIR / rel).resolve()
            try:
                file_path.relative_to(views.STATIC_DIR.resolve())
            except ValueError:
                self._send(404, b"not found", "text/plain")
                return
            if not file_path.is_file():
                self._send(404, b"not found", "text/plain")
                return
            data = file_path.read_bytes()
            ctype = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
            self._send(200, data, ctype)
            return

        if path == "/" or path == "":
            projects = views.list_projects(self.workspace)
            ollama = views.ollama_status()
            html = views.render(
                "index.html",
                title="FORGEOS",
                projects=projects,
                has_projects=bool(projects),
                ollama_label=ollama.get("label", "offline"),
                empty_hint=""
                if projects
                else "No managed projects yet. Run: forgeos init <name>",
            )
            self._send(200, html.encode("utf-8"))
            return

        m = re.fullmatch(r"/p/([A-Za-z0-9._-]+)", path)
        if m:
            name = m.group(1)
            try:
                ov = views.project_overview(self.workspace, name)
            except FileNotFoundError:
                self._send(404, b"project not found", "text/plain")
                return
            state = ov["state"]
            proj = state.get("project") or {}
            health = ov["health"]
            debt = ov["debt"]
            tests = health.get("tests") or {}
            env = health.get("environment") or {}
            html = views.render(
                "project.html",
                title=f"{name} · FORGEOS",
                name=name,
                phase=proj.get("phase", ""),
                status=proj.get("status", ""),
                completed=ov["task_counts"].get("completed", 0),
                pending=ov["task_counts"].get("pending", 0),
                blocked=ov["task_counts"].get("blocked", 0),
                task_total=ov["task_total"],
                pending_count=ov["pending_count"],
                health_passing=tests.get("passing", "—"),
                health_failing=tests.get("failing", "—"),
                health_total=tests.get("total", "—"),
                env_python=env.get("python", "—"),
                env_docker=env.get("docker", "—"),
                debt_score=debt.get("score", "—"),
                debt_todo=debt.get("todo_count", "—"),
                checkpoints=ov["checkpoints"],
                has_checkpoints=bool(ov["checkpoints"]),
                scaffold_hint=ov.get("scaffold_hint") or "",
                has_scaffold_hint=bool(ov.get("scaffold_hint")),
                ollama_label=(ov.get("ollama") or {}).get("label", "offline"),
            )
            self._send(200, html.encode("utf-8"))
            return

        m = re.fullmatch(r"/p/([A-Za-z0-9._-]+)/tasks", path)
        if m:
            name = m.group(1)
            try:
                tasks = views.project_tasks(self.workspace, name)
            except Exception:
                self._send(404, b"project not found", "text/plain")
                return
            html = views.render(
                "tasks.html",
                title=f"Tasks · {name}",
                name=name,
                tasks=tasks,
                has_tasks=bool(tasks),
                empty_hint="" if tasks else "No tasks in graph yet.",
            )
            self._send(200, html.encode("utf-8"))
            return

        m = re.fullmatch(r"/p/([A-Za-z0-9._-]+)/approvals", path)
        if m:
            name = m.group(1)
            try:
                pending = views.project_approvals(self.workspace, name)
            except Exception:
                self._send(404, b"project not found", "text/plain")
                return
            html = views.render(
                "approvals.html",
                title=f"Approvals · {name}",
                name=name,
                approvals=pending,
                has_approvals=bool(pending),
                empty_hint="" if pending else "No pending approvals.",
            )
            self._send(200, html.encode("utf-8"))
            return

        m = re.fullmatch(r"/p/([A-Za-z0-9._-]+)/audit", path)
        if m:
            name = m.group(1)
            try:
                rows = views.project_audit(self.workspace, name)
            except Exception:
                self._send(404, b"project not found", "text/plain")
                return
            html = views.render(
                "audit.html",
                title=f"Audit · {name}",
                name=name,
                rows=rows,
                has_rows=bool(rows),
                empty_hint="" if rows else "No audit entries yet.",
            )
            self._send(200, html.encode("utf-8"))
            return

        m = re.fullmatch(r"/p/([A-Za-z0-9._-]+)/memory", path)
        if m:
            name = m.group(1)
            try:
                mem = views.project_memory(self.workspace, name)
            except Exception:
                self._send(404, b"project not found", "text/plain")
                return
            counts = mem.get("counts") or {}
            html = views.render(
                "memory.html",
                title=f"Memory · {name}",
                name=name,
                tasks_count=counts.get("tasks", 0),
                decisions_count=counts.get("decisions", 0),
                events_count=counts.get("events", 0),
                decisions=mem.get("decisions") or [],
                events=mem.get("events") or [],
                has_decisions=bool(mem.get("decisions")),
                has_events=bool(mem.get("events")),
            )
            self._send(200, html.encode("utf-8"))
            return

        self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        form = self._read_form()

        m = re.fullmatch(r"/p/([A-Za-z0-9._-]+)/approvals/approve", path)
        if m:
            name = m.group(1)
            project = ws.project_root(self.workspace, name)
            try:
                actions.approve(project, form.get("id", ""))
            except (FileNotFoundError, ValueError) as exc:
                self._send(400, str(exc).encode("utf-8"), "text/plain")
                return
            self._redirect(f"/p/{name}/approvals")
            return

        m = re.fullmatch(r"/p/([A-Za-z0-9._-]+)/approvals/reject", path)
        if m:
            name = m.group(1)
            project = ws.project_root(self.workspace, name)
            try:
                actions.reject(project, form.get("id", ""))
            except (FileNotFoundError, ValueError) as exc:
                self._send(400, str(exc).encode("utf-8"), "text/plain")
                return
            self._redirect(f"/p/{name}/approvals")
            return

        m = re.fullmatch(r"/p/([A-Za-z0-9._-]+)/intel/health", path)
        if m:
            name = m.group(1)
            project = ws.project_root(self.workspace, name)
            actions.run_health(project)
            self._redirect(f"/p/{name}")
            return

        m = re.fullmatch(r"/p/([A-Za-z0-9._-]+)/intel/debt", path)
        if m:
            name = m.group(1)
            project = ws.project_root(self.workspace, name)
            actions.run_debt(project)
            self._redirect(f"/p/{name}")
            return

        m = re.fullmatch(r"/p/([A-Za-z0-9._-]+)/checkpoint", path)
        if m:
            name = m.group(1)
            project = ws.project_root(self.workspace, name)
            actions.create_checkpoint(project, message=form.get("message", ""))
            self._redirect(f"/p/{name}")
            return

        self._send(404, b"not found", "text/plain")


def make_server(
    workspace: Path,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> ThreadingHTTPServer:
    handler = type(
        "BoundDashboardHandler",
        (DashboardHandler,),
        {"workspace": workspace.resolve()},
    )
    return ThreadingHTTPServer((host, port), handler)


def serve(
    workspace: Path | None = None,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    *,
    allow_remote: bool = False,
) -> None:
    """Serve the dashboard until interrupted."""
    if host not in ("127.0.0.1", "localhost", "::1") and not allow_remote:
        raise ValueError(
            f"refusing to bind {host!r}; use loopback or pass allow_remote=True"
        )
    ws_path = (workspace or Path.cwd()).resolve()
    candidates = [port]
    for alt in FALLBACK_PORTS:
        if alt not in candidates:
            candidates.append(alt)

    last_err: OSError | None = None
    httpd = None
    bound_port = port
    for candidate in candidates:
        try:
            httpd = make_server(ws_path, host=host, port=candidate)
            bound_port = candidate
            break
        except OSError as exc:
            last_err = exc
            continue
    if httpd is None:
        assert last_err is not None
        raise OSError(
            f"{last_err}; tried ports {candidates}. "
            "On Windows, Hyper-V often reserves 8571–9270 — use --port 18080"
        ) from last_err

    if bound_port != port:
        print(f"note: port {port} unavailable; using {bound_port}")
    print(f"FORGEOS dashboard: http://{host}:{bound_port}/")
    print(f"workspace: {ws_path}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down dashboard")
    finally:
        httpd.server_close()
