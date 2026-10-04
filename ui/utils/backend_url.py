from urllib.parse import urlparse

import requests

DEFAULT_BACKEND_HOST = "localhost"
DEFAULT_BACKEND_PORT = 8055
DEFAULT_BACKEND_BASE_URL = f"http://{DEFAULT_BACKEND_HOST}:{DEFAULT_BACKEND_PORT}"
LOCALHOST_BACKEND_HOSTS = ("localhost",)
ACTIVE_BACKEND_HOST = DEFAULT_BACKEND_HOST


def normalize_backend_host(host: str | None) -> str:
    del host
    return DEFAULT_BACKEND_HOST


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
    configured_hosts = LOCALHOST_BACKEND_HOSTS
    getter = request_getter or requests.get

    for host in configured_hosts:
        if not str(host).strip().strip("/"):
            continue

        health_url = f"http://{host}:{port}/health_check"
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
                update_backend_host(host)
                return f"http://{host}:{port}"
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
