import time
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import List, Dict, Any, Optional
from playwright.async_api import Page, ConsoleMessage, Request, Response

SENSITIVE_HEADERS = {
    "authorization", "cookie", "set-cookie", "x-api-key", 
    "x-auth-token", "proxy-authorization", "token"
}

SENSITIVE_PARAMS = {
    "password", "secret", "token", "access_token", "refresh_token", 
    "api_key", "apikey", "auth", "credential", "private_key"
}

def redact_url(url: str) -> str:
    """
    Redacts sensitive query parameters like passwords and tokens from URLs.
    """
    try:
        parsed = urlparse(url)
        if not parsed.query:
            return url
        qs = parse_qs(parsed.query, keep_blank_values=True)
        clean = []
        for k, v_list in qs.items():
            if k.lower() in SENSITIVE_PARAMS:
                clean.append((k, "[REDACTED]"))
            else:
                for val in v_list:
                    clean.append((k, val))
        return urlunparse((
            parsed.scheme, parsed.netloc, parsed.path,
            parsed.params, urlencode(clean), parsed.fragment
        ))
    except Exception:
        return url

def redact_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Redacts sensitive HTTP headers.
    """
    clean = {}
    for k, v in headers.items():
        if k.lower() in SENSITIVE_HEADERS:
            clean[k] = "[REDACTED]"
        else:
            clean[k] = v
    return clean

class DiagnosticsRecorder:
    """
    Records, analyzes, and redacts console output and network transactions.
    """
    def __init__(self, page: Page):
        self.page = page
        self.console_logs: List[Dict[str, Any]] = []
        self.network_records: List[Dict[str, Any]] = []
        self._request_start_times: Dict[str, float] = {}
        
        # Attach listeners
        self._setup_listeners()

    def _setup_listeners(self):
        self.page.on("console", self._handle_console)
        self.page.on("pageerror", self._handle_page_error)
        self.page.on("request", self._handle_request)
        self.page.on("requestfailed", self._handle_request_failed)
        self.page.on("response", self._handle_response)

    def _handle_console(self, msg: ConsoleMessage):
        text = msg.text
        m_type = msg.type # 'error', 'warning', 'info', 'log', etc.
        location = f"{msg.location.get('url', '')}:{msg.location.get('lineNumber', 0)}"

        # Classify sub-type
        sub_type = "GENERAL"
        lower = text.lower()
        if "hydration" in lower or "minified react error" in lower:
            sub_type = "REACT_HYDRATION"
        elif "content security policy" in lower or "csp" in lower:
            sub_type = "CSP_VIOLATION"
        elif "failed to load resource" in lower:
            sub_type = "RESOURCE_FAIL"
        elif "deprecated" in lower:
            sub_type = "DEPRECATED_API"

        self.console_logs.append({
            "type": "error" if m_type == "error" else ("warning" if m_type == "warning" else "info"),
            "text": text,
            "location": location,
            "sub_type": sub_type,
            "timestamp": time.time(),
            "stack_trace": None
        })

    def _handle_page_error(self, err: Exception):
        err_msg = str(err)
        self.console_logs.append({
            "type": "error",
            "text": err_msg,
            "location": getattr(err, "stack", "uncaught"),
            "sub_type": "UNCAUGHT_EXCEPTION",
            "timestamp": time.time(),
            "stack_trace": getattr(err, "stack", None)
        })

    def _handle_request(self, request: Request):
        req_id = f"{request.method}_{request.url}_{time.time()}"
        self._request_start_times[request.url] = time.time()

    def _handle_request_failed(self, request: Request):
        start_time = self._request_start_times.pop(request.url, time.time())
        duration_ms = (time.time() - start_time) * 1000.0
        failure = request.failure
        failure_text = failure if isinstance(failure, str) else (failure.get("errorText", "Failed") if isinstance(failure, dict) else str(failure))

        self.network_records.append({
            "method": request.method,
            "url": redact_url(request.url),
            "resource_type": request.resource_type,
            "status_code": None,
            "duration_ms": round(duration_ms, 2),
            "size_bytes": 0,
            "failed": True,
            "failure_reason": failure_text,
            "timestamp": time.time()
        })

    def _handle_response(self, response: Response):
        start_time = self._request_start_times.pop(response.url, time.time())
        duration_ms = (time.time() - start_time) * 1000.0
        status = response.status
        is_failed = status >= 400

        # Attempt to get body size from headers safely
        size_bytes = 0
        cl = response.headers.get("content-length")
        if cl and cl.isdigit():
            size_bytes = int(cl)

        self.network_records.append({
            "method": response.request.method,
            "url": redact_url(response.url),
            "resource_type": response.request.resource_type,
            "status_code": status,
            "duration_ms": round(duration_ms, 2),
            "size_bytes": size_bytes,
            "failed": is_failed,
            "failure_reason": f"HTTP {status}" if is_failed else None,
            "timestamp": time.time()
        })

    def get_console_errors(self) -> List[Dict[str, Any]]:
        """Returns all logged console errors."""
        return [c for c in self.console_logs if c["type"] == "error"]

    def get_failed_network_requests(self) -> List[Dict[str, Any]]:
        """Returns all failed network requests (failed or HTTP status >= 400)."""
        return [n for n in self.network_records if n["failed"]]

    def get_deduplicated_console_errors(self) -> List[Dict[str, Any]]:
        """
        Deduplicates console errors based on error text and location.
        """
        deduped: Dict[str, Dict[str, Any]] = {}
        for c in self.get_console_errors():
            key = f"{c['sub_type']}_{c['text'][:150]}_{c['location']}"
            if key not in deduped:
                item = dict(c)
                item["count"] = 1
                deduped[key] = item
            else:
                deduped[key]["count"] += 1
        return list(deduped.values())

    def get_grouped_network_failures(self) -> List[Dict[str, Any]]:
        """
        Groups repeated network failures by URL and status code.
        """
        grouped: Dict[str, Dict[str, Any]] = {}
        for n in self.get_failed_network_requests():
            key = f"{n['method']}_{n['status_code']}_{n['url']}"
            if key not in grouped:
                item = dict(n)
                item["count"] = 1
                grouped[key] = item
            else:
                grouped[key]["count"] += 1
        return list(grouped.values())
