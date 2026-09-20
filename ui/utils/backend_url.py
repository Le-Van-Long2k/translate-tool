from urllib.parse import urlparse

import requests

DEFAULT_BACKEND_HOST = "127.0.0.1"
DEFAULT_BACKEND_PORT = 8052
DEFAULT_BACKEND_BASE_URL = f"http://{DEFAULT_BACKEND_HOST}:{DEFAULT_BACKEND_PORT}"
LOCALHOST_BACKEND_HOSTS = ("127.0.0.1", "localhost", "127.0.0.0", "0.0.0.0")
ACTIVE_BACKEND_HOST = DEFAULT_BACKEND_HOST


def normalize_backend_host(host: str | None) -> str:
    if host is None:
        return DEFAULT_BACKEND_HOST

    candidate = str(host).strip().strip("/")
    if not candidate:
        return DEFAULT_BACKEND_HOST

    if candidate.startswith("http://") or candidate.startswith("https://"):
        parsed = urlparse(candidate)
        candidate = parsed.hostname or parsed.netloc or candidate

    candidate = candidate.lower()
    if candidate in {"localhost", "127.0.0.0", "0.0.0.0"}:
        return DEFAULT_BACKEND_HOST

    if candidate.startswith("[") and candidate.endswith("]"):
        candidate = candidate[1:-1]

    return candidate or DEFAULT_BACKEND_HOST


def normalize_backend_url(url: str | None, fallback_path: str = "/") -> str:
    candidate = (url or "").strip()
    if not candidate:
        candidate = f"http://{DEFAULT_BACKEND_HOST}:{DEFAULT_BACKEND_PORT}{fallback_path if fallback_path.startswith('/') else '/' + fallback_path}"

    parsed = urlparse(candidate)
    host = normalize_backend_host(parsed.hostname or candidate)
    path = parsed.path or "/" if parsed.scheme else candidate
    if not parsed.scheme:
        if not path.startswith("/"):
            path = f"/{path}"
        return f"http://{host}:{parsed.port or DEFAULT_BACKEND_PORT}{path}"

    port = parsed.port or DEFAULT_BACKEND_PORT
    if parsed.path:
        effective_path = parsed.path
    else:
        effective_path = fallback_path if fallback_path.startswith("/") else f"/{fallback_path}"

    return f"{parsed.scheme}://{host}:{port}{effective_path}"


def update_backend_host(host: str | None) -> str:
    global ACTIVE_BACKEND_HOST
    ACTIVE_BACKEND_HOST = normalize_backend_host(host) or DEFAULT_BACKEND_HOST
    return ACTIVE_BACKEND_HOST


def resolve_backend_base_url(
    hosts: tuple[str, ...] | list[str] | None = None,
    port: int = DEFAULT_BACKEND_PORT,
    request_getter=None,
) -> str:
    configured_hosts = tuple(hosts or LOCALHOST_BACKEND_HOSTS)
    getter = request_getter or requests.get

    for host in configured_hosts:
        candidate_host = str(host).strip().strip("/")
        if not candidate_host:
            continue

        health_url = f"http://{candidate_host}:{port}/health_check"
        try:
            response = getter(health_url, timeout=5)
            status_code = getattr(response, "status_code", 200)
            if status_code < 200 or status_code >= 300:
                continue

            payload = {}
            try:
                payload = response.json() if hasattr(response, "json") else {}
            except Exception:
                payload = {}

            if payload == {} or payload.get("status") == "ok":
                update_backend_host(candidate_host)
                return f"http://{candidate_host}:{port}"
        except Exception:
            continue

    return f"http://{ACTIVE_BACKEND_HOST}:{port}"


def build_backend_url(path: str, host: str | None = None, port: int = DEFAULT_BACKEND_PORT) -> str:
    cleaned_path = (path or "").strip()
    if not cleaned_path:
        cleaned_path = "/"
    if not cleaned_path.startswith("/"):
        cleaned_path = f"/{cleaned_path}"

    backend_host = normalize_backend_host(host) if host is not None else ACTIVE_BACKEND_HOST
    return f"http://{backend_host}:{port}{cleaned_path}"
