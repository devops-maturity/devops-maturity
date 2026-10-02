import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.responses import RedirectResponse
from fastapi.testclient import TestClient

from src.web.main import app

client = TestClient(app, follow_redirects=False)


# ── Home page ──────────────────────────────────────────────────────────────────


def test_read_form():
    response = client.get("/")
    assert response.status_code == 200
    assert "form" in response.text.lower()


def test_read_form_highlights_value_and_cli_path():
    response = client.get("/")
    assert response.status_code == 200
    assert "Turn a long DevOps checklist into a clear next action" in response.text
    assert "pip install devops-maturity" in response.text
    assert "Get my maturity score" in response.text
    assert "https://devops-maturity.github.io/devops-maturity/" in response.text


# ── Auth pages ─────────────────────────────────────────────────────────────────


def test_login_page():
    response = client.get("/login")
    assert response.status_code == 200
    assert "login" in response.text.lower()


def test_register_page():
    response = client.get("/register")
    assert response.status_code == 200
    assert "register" in response.text.lower()


def test_logout_redirects_to_login():
    response = client.get("/logout")
    assert response.status_code in (302, 303, 307)
    assert "/login" in response.headers.get("location", "")


def test_register_new_user():
    unique = uuid.uuid4().hex[:8]
    with patch("src.web.main.bcrypt") as mock_bcrypt:
        mock_bcrypt.hash.return_value = "hashed_password"
        response = client.post(
            "/register",
            data={
                "username": f"user_{unique}",
                "email": f"user_{unique}@example.com",
                "password": "testpassword123",
            },
        )
    # Successful registration redirects to "/"
    assert response.status_code in (302, 303, 307)


def test_register_duplicate_user():
    unique = uuid.uuid4().hex[:8]
    data = {
        "username": f"dup_{unique}",
        "email": f"dup_{unique}@example.com",
        "password": "testpassword123",
    }
    with patch("src.web.main.bcrypt") as mock_bcrypt:
        mock_bcrypt.hash.return_value = "hashed_password"
        client.post("/register", data=data)
        # Second registration with same credentials should fail
        response = client.post("/register", data=data)
    assert response.status_code == 200
    assert "already exists" in response.text.lower()


def test_login_invalid_credentials():
    response = client.post(
        "/login",
        data={"username": "nonexistent_user_xyz", "password": "wrongpass"},
    )
    assert response.status_code == 200
    assert "invalid" in response.text.lower()


def test_login_valid_credentials():
    unique = uuid.uuid4().hex[:8]
    username = f"logintest_{unique}"
    password = "securepassword"
    with patch("src.web.main.bcrypt") as mock_bcrypt:
        mock_bcrypt.hash.return_value = "hashed_password"
        mock_bcrypt.verify.return_value = True
        client.post(
            "/register",
            data={
                "username": username,
                "email": f"{username}@example.com",
                "password": password,
            },
        )
        response = client.post(
            "/login", data={"username": username, "password": password}
        )
    assert response.status_code in (302, 303, 307)


# ── OAuth login ────────────────────────────────────────────────────────────────


def test_oauth_login_unconfigured_provider():
    """When OAuth is not configured, /auth/<provider> redirects with error."""
    response = client.get("/auth/google")
    assert response.status_code in (302, 303, 307)
    location = response.headers.get("location", "")
    assert "oauth_not_configured" in location or "/login" in location


def test_oauth_login_invalid_provider():
    response = client.get("/auth/unknownprovider")
    assert response.status_code in (302, 303, 307)
    assert "/login" in response.headers.get("location", "")


def test_oauth_callback_invalid_provider():
    response = client.get("/auth/callback/unknownprovider")
    assert response.status_code in (302, 303, 307)
    assert "/login" in response.headers.get("location", "")


def test_oauth_callback_unconfigured_provider():
    response = client.get("/auth/callback/github")
    assert response.status_code in (302, 303, 307)
    location = response.headers.get("location", "")
    assert "oauth_not_configured" in location or "/login" in location


# ── Assessment submission ──────────────────────────────────────────────────────


def test_submit_missing_project_name():
    response = client.post("/submit", data={"D101": "yes"})
    assert response.status_code == 200
    assert "required" in response.text.lower()


def test_submit_with_project_name():
    response = client.post(
        "/submit",
        data={"project_name": "My Project", "D101": "yes", "D201": "no"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    # result.html shows score and badge
    assert "score" in response.text.lower()


def test_submit_result_includes_next_actions_and_badge_copy():
    response = client.post(
        "/submit",
        data={"project_name": "Result UX Project", "D101": "yes", "D201": "no"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Next actions" in response.text
    assert "Improvement recommendations" in response.text
    assert "data-copy-value" in response.text


def test_submit_all_no():
    response = client.post(
        "/submit",
        data={"project_name": "Empty Project"},
        follow_redirects=True,
    )
    assert response.status_code == 200


# ── Assessments list ───────────────────────────────────────────────────────────


def test_list_assessments_page():
    response = client.get("/assessments")
    assert response.status_code == 200


# ── Badge ──────────────────────────────────────────────────────────────────────


def test_badge_svg_endpoint():
    response = client.get("/badge.svg")
    assert response.status_code == 200
    assert "svg" in response.headers.get("content-type", "").lower()


# ── Health check ───────────────────────────────────────────────────────────────


def test_healthz_endpoint():
    response = client.get("/healthz")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "version" in payload


# ── Edit assessment ────────────────────────────────────────────────────────────


def test_edit_assessment_not_found():
    response = client.get("/edit-assessment/999999")
    assert response.status_code == 404


# ── Login page query-string error ─────────────────────────────────────────────


def test_login_page_oauth_error_message():
    # Use a fresh client to avoid session state from prior tests
    fresh_client = TestClient(app, follow_redirects=False)
    response = fresh_client.get("/login?error=oauth_not_configured")
    assert response.status_code == 200
    assert "not configured" in response.text.lower()


# ── Helpers ────────────────────────────────────────────────────────────────────


def _new_client():
    """A client with its own (empty) cookie jar, i.e. its own session."""
    return TestClient(app, follow_redirects=False)


def _register(test_client, prefix="user"):
    """Register (and thereby log in) a fresh user; returns the username."""
    username = f"{prefix}_{uuid.uuid4().hex[:8]}"
    with patch("src.web.main.bcrypt") as mock_bcrypt:
        mock_bcrypt.hash.return_value = "hashed_password"
        response = test_client.post(
            "/register",
            data={
                "username": username,
                "email": f"{username}@example.com",
                "password": "irrelevant",
            },
        )
    assert response.status_code == 302
    return username


def _db_session():
    from core.model import SessionLocal

    return SessionLocal()


def _assessment(project_name):
    from core.model import Assessment

    db = _db_session()
    try:
        return db.query(Assessment).filter_by(project_name=project_name).one()
    finally:
        db.close()


def _user(username):
    from core.model import User

    db = _db_session()
    try:
        return db.query(User).filter_by(username=username).one_or_none()
    finally:
        db.close()


def _submit(test_client, project_name=None, **answers):
    project_name = project_name or f"project-{uuid.uuid4().hex[:8]}"
    response = test_client.post(
        "/submit", data={"project_name": project_name, **answers}
    )
    assert response.status_code == 200
    return _assessment(project_name)


# ── Session-aware pages ────────────────────────────────────────────────────────


def test_register_and_login_pages_redirect_when_logged_in():
    c = _new_client()
    username = _register(c)
    for path in ("/register", "/login"):
        response = c.get(path)
        assert response.status_code == 302
        assert response.headers["location"] == "/"
    assert f"Welcome, {username}" in c.get("/").text


def test_logout_clears_the_session():
    c = _new_client()
    _register(c)
    assert c.get("/logout").status_code == 302
    response = c.get("/login")
    assert response.status_code == 200
    assert "Welcome," not in response.text


def test_login_by_email_sets_session():
    c = _new_client()
    username = _register(c)
    c.get("/logout")
    with patch("src.web.main.bcrypt") as mock_bcrypt:
        mock_bcrypt.verify.return_value = True
        response = c.post(
            "/login",
            data={"username": f"{username}@example.com", "password": "irrelevant"},
        )
    assert response.status_code == 302
    mock_bcrypt.verify.assert_called_once_with("irrelevant", "hashed_password")
    assert f"Welcome, {username}" in c.get("/").text


def test_login_wrong_password_is_rejected():
    c = _new_client()
    username = _register(c)
    c.get("/logout")
    with patch("src.web.main.bcrypt") as mock_bcrypt:
        mock_bcrypt.verify.return_value = False
        response = c.post("/login", data={"username": username, "password": "bad"})
    assert response.status_code == 200
    assert "Invalid credentials." in response.text


def test_login_oauth_only_account_without_password_is_rejected():
    from core.model import User

    username = f"oauthonly_{uuid.uuid4().hex[:8]}"
    db = _db_session()
    db.add(User(username=username, email=f"{username}@example.com"))
    db.commit()
    db.close()

    with patch("src.web.main.bcrypt") as mock_bcrypt:
        response = _new_client().post(
            "/login", data={"username": username, "password": "anything"}
        )
    assert response.status_code == 200
    assert "Invalid credentials." in response.text
    mock_bcrypt.verify.assert_not_called()


# ── Assessment submission and listing ──────────────────────────────────────────


def test_submit_all_yes_scores_gold_and_links_project():
    from src.config.loader import load_criteria_config

    _, criteria = load_criteria_config()
    response = client.post(
        "/submit",
        data={
            "project_name": "Gold Project",
            "project_url": "https://example.com/gold",
            **{c.id: "yes" for c in criteria},
        },
    )
    assert response.status_code == 200
    assert "100.0%" in response.text
    assert "GOLD" in response.text
    assert "DevOps%20Maturity-GOLD" in response.text
    assert '<a href="https://example.com/gold"' in response.text
    assert "All configured practices are in place." in response.text


def test_submit_escapes_user_supplied_project_name():
    response = client.post(
        "/submit", data={"project_name": "<script>alert(1)</script>"}
    )
    assert response.status_code == 200
    assert "<script>alert(1)</script>" not in response.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in response.text


def test_submit_anonymous_assessment_has_no_owner():
    saved = _submit(_new_client(), D101="yes")
    assert saved.user_id is None
    assert saved.project_url is None
    assert saved.responses == {"D101": True}


def test_submit_logged_in_assessment_belongs_to_user():
    c = _new_client()
    username = _register(c)
    saved = _submit(c, D101="yes", D201="no")
    assert saved.user_id == _user(username).id
    assert saved.responses == {"D101": True, "D201": False}


def test_assessments_page_shows_owner_details_and_edit_link():
    owner = _new_client()
    username = _register(owner, prefix="owner")
    saved = _submit(owner, D101="yes", D201="no")

    page = owner.get("/assessments").text
    assert saved.project_name in page
    assert username in page
    assert f'href="/edit-assessment/{saved.id}"' in page
    assert "Branch Builds" in page
    assert "In place" in page and "Not yet" in page

    # Other visitors see the assessment but not the edit link.
    anonymous_page = _new_client().get("/assessments").text
    assert saved.project_name in anonymous_page
    assert f'href="/edit-assessment/{saved.id}"' not in anonymous_page


def test_assessments_page_marks_anonymous_assessments():
    saved = _submit(_new_client())
    page = _new_client().get("/assessments").text
    assert saved.project_name in page
    assert "Anonymous" in page


# ── Edit assessment ────────────────────────────────────────────────────────────


@pytest.fixture()
def owned_assessment():
    """(owner client, assessment) for an assessment created by a fresh user."""
    owner = _new_client()
    _register(owner, prefix="editor")
    saved = _submit(owner, D101="yes", D201="no")
    return owner, saved


def test_edit_form_prefills_current_answers(owned_assessment):
    owner, saved = owned_assessment
    response = owner.get(f"/edit-assessment/{saved.id}")
    assert response.status_code == 200
    assert f'value="{saved.project_name}"' in response.text
    assert 'id="D101-yes" checked' in response.text
    assert 'id="D201-no" checked' in response.text


def test_edit_form_forbidden_for_anonymous_and_other_users(owned_assessment):
    _, saved = owned_assessment
    assert _new_client().get(f"/edit-assessment/{saved.id}").status_code == 403

    intruder = _new_client()
    _register(intruder, prefix="intruder")
    assert intruder.get(f"/edit-assessment/{saved.id}").status_code == 403


def test_edit_submit_not_found():
    c = _new_client()
    _register(c)
    response = c.post("/edit-assessment/999999", data={"project_name": "x"})
    assert response.status_code == 404


def test_edit_submit_forbidden_for_other_users(owned_assessment):
    _, saved = owned_assessment
    anonymous = _new_client().post(
        f"/edit-assessment/{saved.id}", data={"project_name": "hijacked"}
    )
    assert anonymous.status_code == 403

    intruder = _new_client()
    _register(intruder, prefix="intruder")
    response = intruder.post(
        f"/edit-assessment/{saved.id}", data={"project_name": "hijacked"}
    )
    assert response.status_code == 403
    assert _assessment(saved.project_name).responses == saved.responses


def test_edit_submit_requires_project_name(owned_assessment):
    owner, saved = owned_assessment
    response = owner.post(f"/edit-assessment/{saved.id}", data={"D101": "no"})
    assert response.status_code == 200
    assert "Project Name is required." in response.text
    assert _assessment(saved.project_name).responses == saved.responses


def test_edit_submit_updates_assessment(owned_assessment):
    owner, saved = owned_assessment
    new_name = f"renamed-{uuid.uuid4().hex[:8]}"
    response = owner.post(
        f"/edit-assessment/{saved.id}",
        data={
            "project_name": new_name,
            "project_url": "",
            "D101": "no",
            "D201": "yes",
        },
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/assessments"

    updated = _assessment(new_name)
    assert updated.id == saved.id
    assert updated.project_url is None
    assert updated.responses == {"D101": False, "D201": True}


# ── OAuth ──────────────────────────────────────────────────────────────────────


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class _FakeOAuthClient:
    """Offline stand-in for an authlib Starlette OAuth client."""

    def __init__(self, token=None, api=None):
        self.token = token or {"access_token": "test-access-token"}
        self.api = api or {}
        self.calls = []

    async def authorize_redirect(self, request, redirect_uri):
        self.calls.append(("authorize_redirect", str(redirect_uri)))
        return RedirectResponse("https://provider.example/authorize", status_code=302)

    async def authorize_access_token(self, request):
        self.calls.append(("authorize_access_token",))
        return self.token

    async def get(self, path, token=None):
        self.calls.append(("get", path, token))
        return _FakeResponse(self.api[path])


@pytest.fixture()
def fake_oauth(monkeypatch):
    """Enable GitHub OAuth and route it to a fake client."""
    monkeypatch.setenv("GITHUB_CLIENT_ID", "test-github-client-id")
    monkeypatch.setenv("GITHUB_CLIENT_SECRET", "test-github-client-secret")

    def install(fake_client):
        registry = MagicMock()
        registry.create_client.return_value = fake_client
        monkeypatch.setattr("src.web.main.oauth", registry)
        return registry

    return install


def test_is_oauth_provider_enabled(monkeypatch):
    from src.web.main import is_oauth_provider_enabled

    for var in (
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "GITHUB_CLIENT_ID",
        "GITHUB_CLIENT_SECRET",
    ):
        monkeypatch.delenv(var, raising=False)
    assert is_oauth_provider_enabled("google") is False
    assert is_oauth_provider_enabled("github") is False

    monkeypatch.setenv("GOOGLE_CLIENT_ID", "id-only")
    assert is_oauth_provider_enabled("google") is False
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "secret")
    assert is_oauth_provider_enabled("google") is True

    monkeypatch.setenv("GITHUB_CLIENT_ID", "id")
    monkeypatch.setenv("GITHUB_CLIENT_SECRET", "secret")
    assert is_oauth_provider_enabled("github") is True
    assert is_oauth_provider_enabled("gitlab") is False


def test_login_and_register_pages_show_configured_oauth_buttons(monkeypatch):
    monkeypatch.setenv("GITHUB_CLIENT_ID", "id")
    monkeypatch.setenv("GITHUB_CLIENT_SECRET", "secret")
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    for path in ("/login", "/register"):
        page = _new_client().get(path).text
        assert 'href="/auth/github"' in page
        assert 'href="/auth/google"' not in page


def test_oauth_login_redirects_to_provider(fake_oauth):
    fake_client = _FakeOAuthClient()
    registry = fake_oauth(fake_client)
    response = _new_client().get("/auth/github")
    assert response.status_code == 302
    assert response.headers["location"] == "https://provider.example/authorize"
    registry.create_client.assert_called_once_with("github")
    assert fake_client.calls == [
        ("authorize_redirect", "http://testserver/auth/callback/github")
    ]


def test_oauth_callback_github_creates_user_and_logs_in(fake_oauth):
    login = f"gh_{uuid.uuid4().hex[:8]}"
    fake_client = _FakeOAuthClient(
        api={"user": {"login": login, "id": 4242, "email": f"{login}@example.com"}}
    )
    fake_oauth(fake_client)
    c = _new_client()

    response = c.get("/auth/callback/github?code=abc&state=xyz")

    assert response.status_code == 302
    assert response.headers["location"] == "/"
    user = _user(login)
    assert user.email == f"{login}@example.com"
    assert user.oauth_provider == "github"
    assert user.oauth_id == "4242"
    assert user.password_hash is None
    assert f"Welcome, {login}" in c.get("/").text
    # The public e-mail was present, so the e-mail endpoint is not queried.
    assert ("get", "user/emails", fake_client.token) not in fake_client.calls


def test_oauth_callback_github_falls_back_to_primary_email(fake_oauth):
    login = f"gh_{uuid.uuid4().hex[:8]}"
    fake_client = _FakeOAuthClient(
        api={
            "user": {"login": login, "id": 5151, "email": None},
            "user/emails": [
                {"email": f"{login}-secondary@example.com", "primary": False},
                {"email": f"{login}-primary@example.com", "primary": True},
            ],
        }
    )
    fake_oauth(fake_client)

    response = _new_client().get("/auth/callback/github?code=abc&state=xyz")

    assert response.status_code == 302
    assert _user(login).email == f"{login}-primary@example.com"
    assert ("get", "user/emails", fake_client.token) in fake_client.calls


def test_oauth_callback_github_reuses_existing_oauth_user(fake_oauth):
    login = f"gh_{uuid.uuid4().hex[:8]}"
    profile = {"login": login, "id": 777, "email": f"{login}@example.com"}
    fake_oauth(_FakeOAuthClient(api={"user": profile}))
    assert _new_client().get("/auth/callback/github").status_code == 302
    first = _user(login)

    c = _new_client()
    assert c.get("/auth/callback/github").status_code == 302
    assert _user(login).id == first.id
    assert f"Welcome, {login}" in c.get("/").text


def test_oauth_callback_github_links_existing_account_by_email(fake_oauth):
    local = _new_client()
    username = _register(local, prefix="local")
    fake_oauth(
        _FakeOAuthClient(
            api={
                "user": {
                    "login": f"gh-{username}",
                    "id": 9090,
                    "email": f"{username}@example.com",
                }
            }
        )
    )

    c = _new_client()
    assert c.get("/auth/callback/github").status_code == 302

    linked = _user(username)
    assert linked.oauth_provider == "github"
    assert linked.oauth_id == "9090"
    assert _user(f"gh-{username}") is None
    assert f"Welcome, {username}" in c.get("/").text


def test_oauth_clients_registered_when_credentials_configured(monkeypatch):
    """Executing the module with OAuth credentials registers both providers."""
    import importlib.util

    import src.web.main as web_main

    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-google-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-google-client-secret")
    monkeypatch.setenv("GITHUB_CLIENT_ID", "test-github-client-id")
    monkeypatch.setenv("GITHUB_CLIENT_SECRET", "test-github-client-secret")
    spec = importlib.util.spec_from_file_location(
        "_web_main_with_oauth", web_main.__file__
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    google = module.oauth.create_client("google")
    github = module.oauth.create_client("github")
    assert google.client_id == "test-google-client-id"
    assert github.client_id == "test-github-client-id"
    assert github.authorize_url == "https://github.com/login/oauth/authorize"
    assert github.access_token_url == "https://github.com/login/oauth/access_token"
