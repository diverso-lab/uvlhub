# -----------------------------
# Test doubles (no external IO)
# -----------------------------


class DummyOAuthClient:
    def __init__(self, behavior=None):
        self.behavior = behavior or {}

    def authorize_redirect(self, redirect_uri):
        if self.behavior.get("authorize_redirect_raises"):
            raise RuntimeError("authorize_redirect failed")
        # Return a Flask redirect response to simulate provider redirect
        from flask import redirect

        return redirect("https://orcid.org/oauth/authorize?dummy=1")

    def authorize_access_token(self):
        if self.behavior.get("authorize_access_token_raises"):
            raise RuntimeError("state mismatch")
        return {"access_token": "dummy-token"}


class DummyOrcidService:
    """
    This matches the interface used by your routes:
      - .orcid_client.authorize_redirect(...)
      - .orcid_client.authorize_access_token()
      - .get_orcid_user_info(token) -> (data, err)
      - .get_or_create_user(user_info) -> (user, err)
    """

    def __init__(self, behavior=None):
        self.behavior = behavior or {}
        self.orcid_client = DummyOAuthClient(self.behavior)

    def get_orcid_user_info(self, token):
        return self.behavior.get("userinfo_return", ({"sub": "0000-0000-0000-0000"}, None))

    def get_or_create_user(self, user_info):
        return self.behavior.get("user_return", (object(), None))


# -----------------------------
# Helpers
# -----------------------------


def _inject_orcid_service(monkeypatch, service_instance):
    """
    Your code sets `current_app.orcid_service = OrcidService()` in a before_app_request hook.
    We override that by patching the OrcidService symbol used in routes so it returns our dummy.

    Adjust the import path below if your module path differs.
    """
    import app.modules.orcid.routes as orcid_routes

    monkeypatch.setattr(orcid_routes, "OrcidService", lambda: service_instance)


def _patch_login_user(monkeypatch):
    """
    Optionally patch flask_login.login_user to avoid depending on your login manager internals.
    If you want to assert it was called, we capture calls.
    """
    import app.modules.orcid.routes as orcid_routes

    calls = {"count": 0, "user": None}

    def fake_login_user(user):
        calls["count"] += 1
        calls["user"] = user
        return True

    monkeypatch.setattr(orcid_routes, "login_user", fake_login_user)
    return calls


def _get_flashed_messages(test_client):
    """
    Read flashed messages from the session.
    Flask stores flashes under '_flashes' as a list of (category, message).
    """
    with test_client.session_transaction() as sess:
        return sess.get("_flashes", []) or []


# -----------------------------
# Tests
# -----------------------------


def test_orcid_login_redirects_to_provider(test_client, monkeypatch):
    dummy = DummyOrcidService()
    _inject_orcid_service(monkeypatch, dummy)

    resp = test_client.get("/orcid/login", follow_redirects=False)

    assert resp.status_code in (301, 302)
    location = resp.headers.get("Location", "")
    assert "https://orcid.org/oauth/authorize" in location


def test_orcid_login_failure_flashes_danger(test_client, monkeypatch):
    dummy = DummyOrcidService({"authorize_redirect_raises": True})
    _inject_orcid_service(monkeypatch, dummy)

    resp = test_client.get("/orcid/login", follow_redirects=False)

    # Must not be a 500
    assert resp.status_code in (301, 302, 400, 401)

    flashes = _get_flashed_messages(test_client)
    # We expect at least one "danger" flash
    assert any(category == "danger" for category, _ in flashes)


def test_orcid_authorize_state_mismatch_flashes_danger(test_client, monkeypatch):
    dummy = DummyOrcidService({"authorize_access_token_raises": True})
    _inject_orcid_service(monkeypatch, dummy)

    resp = test_client.get("/orcid/authorize", follow_redirects=False)

    assert resp.status_code in (301, 302, 400, 401)
    flashes = _get_flashed_messages(test_client)
    assert any(category == "danger" for category, _ in flashes)


def test_orcid_authorize_userinfo_error_flashes_danger(test_client, monkeypatch):
    dummy = DummyOrcidService({"userinfo_return": (None, "ORCID user information request failed. Please try again.")})
    _inject_orcid_service(monkeypatch, dummy)

    resp = test_client.get("/orcid/authorize", follow_redirects=False)

    assert resp.status_code in (301, 302, 400, 401)
    flashes = _get_flashed_messages(test_client)
    assert any(category == "danger" and "ORCID" in message for category, message in flashes)


def test_orcid_authorize_user_creation_error_flashes_danger(test_client, monkeypatch):
    dummy = DummyOrcidService(
        {
            "userinfo_return": ({"sub": "0000-0000-0000-0000"}, None),
            "user_return": (None, "Could not create your account due to a database error. Please try again."),
        }
    )
    _inject_orcid_service(monkeypatch, dummy)

    resp = test_client.get("/orcid/authorize", follow_redirects=False)

    assert resp.status_code in (301, 302, 400, 401)
    flashes = _get_flashed_messages(test_client)
    assert any(category == "danger" and "Could not create your account" in message for category, message in flashes)


def test_orcid_authorize_success_calls_login_user_and_redirects(test_client, monkeypatch):
    dummy = DummyOrcidService(
        {
            "userinfo_return": ({"sub": "0000-0000-0000-0000"}, None),
            "user_return": (object(), None),
        }
    )
    _inject_orcid_service(monkeypatch, dummy)

    calls = _patch_login_user(monkeypatch)

    resp = test_client.get("/orcid/authorize", follow_redirects=False)

    assert calls["count"] == 1
    assert calls["user"] is not None

    # Should redirect to home (adjust if your code redirects elsewhere)
    assert resp.status_code in (301, 302)
    location = resp.headers.get("Location", "")
    assert location  # non-empty redirect target


def test_orcid_authorize_never_500_on_known_failures(test_client, monkeypatch):
    """
    Regression test: the intermittent issue you described is usually login_user(None) or unhandled exceptions.
    This ensures common failure modes never produce HTTP 500.
    """
    scenarios = [
        DummyOrcidService({"authorize_access_token_raises": True}),
        DummyOrcidService({"userinfo_return": (None, "userinfo failed")}),
        DummyOrcidService(
            {"userinfo_return": ({"sub": "0000-0000-0000-0000"}, None), "user_return": (None, "db failed")}
        ),
    ]

    for dummy in scenarios:
        _inject_orcid_service(monkeypatch, dummy)
        resp = test_client.get("/orcid/authorize", follow_redirects=False)
        assert resp.status_code != 500
