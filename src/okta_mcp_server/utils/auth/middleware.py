import asyncio
import contextvars
import json
import os
import secrets
import time
from typing import Any, Callable
from urllib.parse import parse_qs, urlencode, urlparse

import requests as _requests

# Per-connection context variable: set by TokenExtractionMiddleware for each /sse request,
# read by the lifespan to use as the caller's delegated Okta access token.
_user_token_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "user_token", default=None
)

_ORG_URL = os.environ.get("OKTA_ORG_URL", "").rstrip("/")
_CLIENT_ID = os.environ.get("OKTA_OIDC_CLIENT_ID", "")
_BASE_URL = os.environ.get("MCP_PUBLIC_URL", f"http://localhost:{os.environ.get('MCP_PORT', '8001')}")

# In-memory store mapping proxy state → {redirect_uri, original_state, ts}.
# States are cleaned up on callback or after _PROXY_STATE_TTL seconds to prevent
# unbounded growth from abandoned authorization flows.
_PROXY_STATE_TTL = 300  # 5 minutes
_PROXY_STATE_MAX = 1000  # reject new flows when limit is reached
_oauth_proxy_states: dict[str, dict[str, str]] = {}


def _prune_proxy_states() -> None:
    """Remove OAuth proxy states that have exceeded the TTL."""
    cutoff = time.time() - _PROXY_STATE_TTL
    stale = [k for k, v in _oauth_proxy_states.items() if float(v.get("ts", 0)) < cutoff]
    for k in stale:
        del _oauth_proxy_states[k]


def _is_safe_redirect_uri(uri: str) -> bool:
    """Return True only for localhost redirect URIs (PKCE native app flows).

    Prevents open-redirect attacks where an attacker-controlled redirect_uri
    would receive the authorization code when the callback fires.
    """
    try:
        parsed = urlparse(uri)
        return parsed.scheme in ("http", "https") and parsed.hostname in ("localhost", "127.0.0.1", "::1")
    except Exception:
        return False


def _build_oauth_metadata() -> bytes:
    """OAuth 2.0 Authorization Server Metadata (RFC 8414).

    Advertises our proxy /authorize and /token endpoints so that:
    - The authorization request redirect_uri is rewritten to our fixed /callback.
    - The token exchange redirect_uri is also rewritten to match.
    Both are required because Okta enforces redirect_uri consistency across both legs.
    """
    metadata: dict[str, Any] = {
        "issuer": _ORG_URL,
        "authorization_endpoint": f"{_BASE_URL}/authorize",
        "token_endpoint": f"{_BASE_URL}/token",
        "jwks_uri": f"{_ORG_URL}/oauth2/v1/keys",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": ["none"],
        "userinfo_endpoint": f"{_ORG_URL}/oauth2/v1/userinfo",
        "code_challenge_methods_supported": ["S256"],
        "registration_endpoint": f"{_BASE_URL}/register",
        "scopes_supported": [
            "openid", "profile", "email",
            "okta.users.read", "okta.users.manage",
            "okta.groups.read", "okta.groups.manage",
            "okta.apps.read", "okta.apps.manage",
            "okta.logs.read",
            "okta.authenticators.read", "okta.authenticators.manage",
            "okta.devices.read", "okta.devices.manage",
            "okta.trustedOrigins.read", "okta.trustedOrigins.manage",
            "okta.agentPools.read", "okta.agentPools.manage",
            "okta.networkZones.read", "okta.networkZones.manage",
            "okta.policies.read", "okta.policies.manage",
            "okta.roles.read", "okta.roles.manage",
            "okta.profileMappings.read", "okta.profileMappings.manage",
            "okta.schemas.read", "okta.schemas.manage",
            # Governance (Okta Identity Governance)
            "okta.governance.accessCertifications.read", "okta.governance.accessCertifications.manage",
            "okta.governance.accessRequests.read", "okta.governance.accessRequests.manage",
            "okta.governance.assignmentCandidates.read",
            "okta.governance.delegates.read", "okta.governance.delegates.manage",
            "okta.governance.entitlements.read", "okta.governance.entitlements.manage",
            "okta.governance.labels.read", "okta.governance.labels.manage",
            "okta.governance.operations.read",
            "okta.governance.principalSettings.read", "okta.governance.principalSettings.manage",
            "okta.governance.resourceOwner.read", "okta.governance.resourceOwner.manage",
            "okta.governance.riskRule.read", "okta.governance.riskRule.manage",
            "okta.governance.securityAccessReviews.admin.read", "okta.governance.securityAccessReviews.admin.manage",
            "okta.governance.securityAccessReviews.endUser.read", "okta.governance.securityAccessReviews.endUser.manage",
            "okta.governance.settings.read", "okta.governance.settings.manage",
            # Access Requests
            "okta.accessRequests.catalog.read",
            "okta.accessRequests.condition.read", "okta.accessRequests.condition.manage",
            "okta.accessRequests.request.read", "okta.accessRequests.request.manage",
            "okta.accessRequests.tasks.read", "okta.accessRequests.tasks.manage",
        ],
    }
    if _CLIENT_ID:
        metadata["client_id"] = _CLIENT_ID
    return json.dumps(metadata).encode()


class TokenExtractionMiddleware:
    """Raw ASGI middleware that handles MCP OAuth discovery and token extraction.

    Endpoints served:
      /.well-known/oauth-authorization-server  — RFC 8414 metadata
      /.well-known/openid-configuration        — OIDC discovery (Claude Desktop)
      /register    — RFC 7591 stub (returns pre-created client_id)
      /authorize   — Proxy: rewrites client's ephemeral redirect_uri to our fixed
                     /callback before forwarding to Okta
      /callback    — Receives Okta's code, bounces it back to client's original port
      /token       — Proxy: rewrites redirect_uri to match authorization request,
                     forwards to Okta's token endpoint, returns response

    On every /sse request:
      - Bearer token present → stored in _user_token_var for the lifespan.
      - No token → 401 + WWW-Authenticate: Bearer (triggers auth UX in clients).

    Uses raw ASGI (not BaseHTTPMiddleware) to avoid buffering SSE responses.
    """

    def __init__(self, app: Any) -> None:
        self.app = app
        self._oauth_metadata = _build_oauth_metadata()

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        path: str = scope.get("path", "")

        # ── OAuth / OIDC discovery ─────────────────────────────────────────────
        if path in ("/.well-known/oauth-authorization-server", "/.well-known/openid-configuration"):
            await self._send_json(send, 200, self._oauth_metadata)
            return

        # ── RFC 7591 Dynamic Client Registration ──────────────────────────────
        if path == "/register":
            body_chunks: list[bytes] = []
            while True:
                event = await receive()
                body_chunks.append(event.get("body", b""))
                if not event.get("more_body", False):
                    break
            raw = b"".join(body_chunks)
            try:
                req_body: dict = json.loads(raw) if raw else {}
            except Exception:
                req_body = {}

            response_body = json.dumps({
                "client_id": _CLIENT_ID,
                "client_id_issued_at": int(time.time()),
                "token_endpoint_auth_method": "none",
                "grant_types": req_body.get("grant_types", ["authorization_code", "refresh_token"]),
                "response_types": req_body.get("response_types", ["code"]),
                "redirect_uris": req_body.get("redirect_uris", [f"{_BASE_URL}/callback"]),
            }).encode()
            await self._send_json(send, 201, response_body)
            return

        # ── OAuth Proxy: /authorize ────────────────────────────────────────────
        # Store the client's ephemeral redirect_uri, replace it with our fixed
        # /callback, then redirect to Okta. PKCE params pass through unchanged.
        if path == "/authorize":
            qs = scope.get("query_string", b"").decode()
            params: dict[str, str] = {
                k: v[0] for k, v in parse_qs(qs, keep_blank_values=True).items()
            }

            original_redirect_uri = params.pop("redirect_uri", "")

            # Reject redirect_uris that aren't localhost — prevents code theft
            if not _is_safe_redirect_uri(original_redirect_uri):
                await self._send_json(
                    send, 400,
                    json.dumps({"error": "invalid_redirect_uri",
                                "error_description": "redirect_uri must target localhost"}).encode(),
                )
                return

            # Reject when state store is saturated (DoS guard)
            _prune_proxy_states()
            if len(_oauth_proxy_states) >= _PROXY_STATE_MAX:
                await self._send_json(
                    send, 503,
                    json.dumps({"error": "server_busy",
                                "error_description": "Too many pending authorization flows"}).encode(),
                )
                return

            # Ensure the token includes okta.users.read so the group membership
            # check can call /api/v1/users/me/groups after the PKCE exchange.
            existing_scopes = set(params.get("scope", "openid profile email").split())
            existing_scopes.update({
                "okta.users.read", "okta.users.manage",
                "okta.groups.read", "okta.groups.manage",
                "okta.apps.read", "okta.apps.manage",
                "okta.logs.read",
                "okta.authenticators.read", "okta.authenticators.manage",
                "okta.devices.read", "okta.devices.manage",
                "okta.trustedOrigins.read", "okta.trustedOrigins.manage",
                "okta.agentPools.read", "okta.agentPools.manage",
                "okta.networkZones.read", "okta.networkZones.manage",
                "okta.policies.read", "okta.policies.manage",
                "okta.roles.read", "okta.roles.manage",
                "okta.profileMappings.read", "okta.profileMappings.manage",
                "okta.schemas.read", "okta.schemas.manage",
                "okta.governance.accessCertifications.read", "okta.governance.accessCertifications.manage",
                "okta.governance.accessRequests.read", "okta.governance.accessRequests.manage",
                "okta.governance.assignmentCandidates.read",
                "okta.governance.delegates.read", "okta.governance.delegates.manage",
                "okta.governance.entitlements.read", "okta.governance.entitlements.manage",
                "okta.governance.labels.read", "okta.governance.labels.manage",
                "okta.governance.operations.read",
                "okta.governance.principalSettings.read", "okta.governance.principalSettings.manage",
                "okta.governance.resourceOwner.read", "okta.governance.resourceOwner.manage",
                "okta.governance.riskRule.read", "okta.governance.riskRule.manage",
                "okta.governance.securityAccessReviews.admin.read", "okta.governance.securityAccessReviews.admin.manage",
                "okta.governance.securityAccessReviews.endUser.read", "okta.governance.securityAccessReviews.endUser.manage",
                "okta.governance.settings.read", "okta.governance.settings.manage",
                "okta.accessRequests.catalog.read",
                "okta.accessRequests.condition.read", "okta.accessRequests.condition.manage",
                "okta.accessRequests.request.read", "okta.accessRequests.request.manage",
                "okta.accessRequests.tasks.read", "okta.accessRequests.tasks.manage",
            })
            params["scope"] = " ".join(sorted(existing_scopes))

            original_state = params.get("state", "")

            proxy_state = secrets.token_urlsafe(32)
            _oauth_proxy_states[proxy_state] = {
                "redirect_uri": original_redirect_uri,
                "state": original_state,
                "ts": str(time.time()),
            }

            params["redirect_uri"] = f"{_BASE_URL}/callback"
            params["state"] = proxy_state

            okta_url = f"{_ORG_URL}/oauth2/v1/authorize?{urlencode(params)}"
            await self._send_redirect(send, okta_url)
            return

        # ── OAuth Proxy: /callback ─────────────────────────────────────────────
        # Okta redirects here with the authorization code. Look up the stored proxy
        # state and bounce the code back to the client's original ephemeral port.
        if path == "/callback":
            qs = scope.get("query_string", b"").decode()
            params = {
                k: v[0] for k, v in parse_qs(qs, keep_blank_values=True).items()
            }

            proxy_state = params.get("state", "")
            _prune_proxy_states()
            stored = _oauth_proxy_states.pop(proxy_state, None)

            if not stored:
                await self._send_json(
                    send, 400,
                    json.dumps({"error": "invalid_state"}).encode(),
                )
                return

            # Paranoia check: stored redirect_uri must still be localhost
            if not _is_safe_redirect_uri(stored["redirect_uri"]):
                await self._send_json(
                    send, 400,
                    json.dumps({"error": "invalid_redirect_uri"}).encode(),
                )
                return

            params["state"] = stored["state"]
            client_redirect = f"{stored['redirect_uri']}?{urlencode(params)}"
            await self._send_redirect(send, client_redirect)
            return

        # ── OAuth Proxy: /token ────────────────────────────────────────────────
        # Claude Code CLI sends the code exchange here. We replace the client's
        # ephemeral redirect_uri with our fixed /callback (must match the value
        # used in /authorize) then forward to Okta's real token endpoint.
        if path == "/token":
            body_chunks = []
            while True:
                event = await receive()
                body_chunks.append(event.get("body", b""))
                if not event.get("more_body", False):
                    break
            raw = b"".join(body_chunks)

            form: dict[str, str] = {
                k: v[0] for k, v in parse_qs(raw.decode(), keep_blank_values=True).items()
            }
            # Replace client's ephemeral redirect_uri with the one Okta knows about.
            form["redirect_uri"] = f"{_BASE_URL}/callback"

            # Inject the full management scope set into the token exchange.
            # Claude Code CLI sends its own minimal scope (openid profile email) in
            # the token request body, which Okta honours and uses to limit the token.
            # We expand it to match what we sent in /authorize so Okta issues a token
            # with the management scopes the user is entitled to as an Okta admin.
            existing_scopes = set(form.get("scope", "openid profile email").split())
            existing_scopes.update({
                "okta.users.read", "okta.users.manage",
                "okta.groups.read", "okta.groups.manage",
                "okta.apps.read", "okta.apps.manage",
                "okta.logs.read",
                "okta.authenticators.read", "okta.authenticators.manage",
                "okta.devices.read", "okta.devices.manage",
                "okta.trustedOrigins.read", "okta.trustedOrigins.manage",
                "okta.agentPools.read", "okta.agentPools.manage",
                "okta.networkZones.read", "okta.networkZones.manage",
                "okta.policies.read", "okta.policies.manage",
                "okta.roles.read", "okta.roles.manage",
                "okta.profileMappings.read", "okta.profileMappings.manage",
                "okta.schemas.read", "okta.schemas.manage",
                "okta.governance.accessCertifications.read", "okta.governance.accessCertifications.manage",
                "okta.governance.accessRequests.read", "okta.governance.accessRequests.manage",
                "okta.governance.assignmentCandidates.read",
                "okta.governance.delegates.read", "okta.governance.delegates.manage",
                "okta.governance.entitlements.read", "okta.governance.entitlements.manage",
                "okta.governance.labels.read", "okta.governance.labels.manage",
                "okta.governance.operations.read",
                "okta.governance.principalSettings.read", "okta.governance.principalSettings.manage",
                "okta.governance.resourceOwner.read", "okta.governance.resourceOwner.manage",
                "okta.governance.riskRule.read", "okta.governance.riskRule.manage",
                "okta.governance.securityAccessReviews.admin.read", "okta.governance.securityAccessReviews.admin.manage",
                "okta.governance.securityAccessReviews.endUser.read", "okta.governance.securityAccessReviews.endUser.manage",
                "okta.governance.settings.read", "okta.governance.settings.manage",
                "okta.accessRequests.catalog.read",
                "okta.accessRequests.condition.read", "okta.accessRequests.condition.manage",
                "okta.accessRequests.request.read", "okta.accessRequests.request.manage",
                "okta.accessRequests.tasks.read", "okta.accessRequests.tasks.manage",
            })
            form["scope"] = " ".join(sorted(existing_scopes))

            okta_token_url = f"{_ORG_URL}/oauth2/v1/token"

            def _exchange() -> tuple[int, bytes, str]:
                resp = _requests.post(
                    okta_token_url,
                    data=form,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=15,
                )
                ct = resp.headers.get("content-type", "application/json")
                return resp.status_code, resp.content, ct

            status, body, content_type = await asyncio.to_thread(_exchange)
            await send({
                "type": "http.response.start",
                "status": status,
                "headers": [(b"content-type", content_type.encode())],
            })
            await send({"type": "http.response.body", "body": body, "more_body": False})
            return

        # ── SSE endpoint: require Bearer token ────────────────────────────────
        if path == "/sse" or path.endswith("/sse"):
            headers: dict[bytes, bytes] = dict(scope.get("headers", []))
            auth_bytes = headers.get(b"authorization", b"")
            auth = auth_bytes.decode("utf-8")

            if not auth.startswith("Bearer "):
                await self._send_json(
                    send,
                    401,
                    json.dumps({"error": "Authorization required"}).encode(),
                    extra_headers=[
                        (b"www-authenticate", b"Bearer"),
                        (b"content-type", b"application/json"),
                    ],
                )
                return

            _user_token_var.set(auth[7:])

        await self.app(scope, receive, send)

    @staticmethod
    async def _send_json(
        send: Callable,
        status: int,
        body: bytes,
        extra_headers: list[tuple[bytes, bytes]] | None = None,
    ) -> None:
        headers = [(b"content-type", b"application/json")]
        if extra_headers:
            header_dict = dict(headers)
            header_dict.update(dict(extra_headers))
            headers = list(header_dict.items())

        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body, "more_body": False})

    @staticmethod
    async def _send_redirect(send: Callable, location: str) -> None:
        await send({
            "type": "http.response.start",
            "status": 302,
            "headers": [(b"location", location.encode())],
        })
        await send({"type": "http.response.body", "body": b"", "more_body": False})
