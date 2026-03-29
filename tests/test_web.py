import pytest
from fastapi.testclient import TestClient
from src.web.main import app
from src.config.loader import load_criteria_config

client = TestClient(app)

_, criteria = load_criteria_config()


def make_full_submission(project_name="Test Project", all_yes=False):
    """Build a form payload with all criteria answered."""
    data = {"project_name": project_name}
    for c in criteria:
        data[c.id] = "yes" if all_yes else "no"
    return data


class TestReadForm:
    def test_get_homepage(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "form" in response.text.lower()

    def test_homepage_contains_criteria(self):
        response = client.get("/")
        assert response.status_code == 200
        # At least one criterion ID should appear in the form
        assert criteria[0].id in response.text


class TestSubmit:
    def test_submit_all_no(self):
        data = make_full_submission(project_name="My Project", all_yes=False)
        response = client.post("/submit", data=data)
        assert response.status_code == 200
        assert "score" in response.text.lower() or "level" in response.text.lower() or "wip" in response.text.lower()

    def test_submit_all_yes(self):
        data = make_full_submission(project_name="Gold Project", all_yes=True)
        response = client.post("/submit", data=data)
        assert response.status_code == 200
        assert "GOLD" in response.text or "100" in response.text

    def test_submit_missing_project_name(self):
        data = {c.id: "no" for c in criteria}
        response = client.post("/submit", data=data)
        assert response.status_code == 200
        assert "required" in response.text.lower() or "project" in response.text.lower()

    def test_submit_saves_assessment(self):
        data = make_full_submission(project_name="Saved Project", all_yes=False)
        response = client.post("/submit", data=data)
        assert response.status_code == 200

        # Check it appears in assessments list
        list_response = client.get("/assessments")
        assert list_response.status_code == 200
        assert "Saved Project" in list_response.text


class TestAssessments:
    def test_list_assessments(self):
        response = client.get("/assessments")
        assert response.status_code == 200

    def test_assessments_page_html(self):
        response = client.get("/assessments")
        assert "text/html" in response.headers["content-type"]


class TestBadge:
    def test_get_badge_svg(self):
        response = client.get("/badge.svg")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/svg+xml"


class TestRegister:
    def test_get_register_form(self):
        response = client.get("/register")
        assert response.status_code == 200
        assert "register" in response.text.lower() or "username" in response.text.lower()

    def test_register_new_user(self):
        response = client.post(
            "/register",
            data={"username": "testuser_unique", "email": "testunique@example.com", "password": "secret"},
            follow_redirects=False,
        )
        assert response.status_code in (200, 302)

    def test_register_duplicate_user(self):
        # Register once
        client.post(
            "/register",
            data={"username": "dupeuser", "email": "dupe@example.com", "password": "secret"},
            follow_redirects=False,
        )
        # Register again with same username
        response = client.post(
            "/register",
            data={"username": "dupeuser", "email": "dupe2@example.com", "password": "secret"},
            follow_redirects=False,
        )
        assert response.status_code in (200, 302)


class TestLogin:
    def test_get_login_form(self):
        response = client.get("/login")
        assert response.status_code == 200
        assert "login" in response.text.lower() or "username" in response.text.lower()

    def test_login_invalid_credentials(self):
        response = client.post(
            "/login",
            data={"username": "nonexistent", "password": "wrong"},
            follow_redirects=False,
        )
        assert response.status_code in (200, 302)
        # When rendering the login page after failed credentials, the template
        # requires oauth_providers — verify no template error occurred
        if response.status_code == 200:
            assert "invalid" in response.text.lower() or "login" in response.text.lower()

    def test_login_valid_credentials(self):
        # First register a user
        client.post(
            "/register",
            data={"username": "loginuser", "email": "login@example.com", "password": "mypassword"},
            follow_redirects=False,
        )
        # Then login
        response = client.post(
            "/login",
            data={"username": "loginuser", "password": "mypassword"},
            follow_redirects=False,
        )
        assert response.status_code in (200, 302)


class TestLogout:
    def test_logout_redirects(self):
        response = client.get("/logout", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers.get("location", "")


class TestOAuthRoutes:
    def test_oauth_login_unknown_provider(self):
        response = client.get("/auth/unknown", follow_redirects=False)
        assert response.status_code in (302, 307)

    def test_oauth_login_unconfigured_google(self):
        response = client.get("/auth/google", follow_redirects=False)
        # Should redirect to /login?error=oauth_not_configured when not configured
        assert response.status_code in (302, 307)

    def test_oauth_login_unconfigured_github(self):
        response = client.get("/auth/github", follow_redirects=False)
        assert response.status_code in (302, 307)

    def test_oauth_callback_unknown_provider(self):
        response = client.get("/auth/callback/unknown", follow_redirects=False)
        assert response.status_code in (302, 307)

    def test_login_oauth_not_configured_error(self):
        response = client.get("/login?error=oauth_not_configured")
        assert response.status_code == 200
        assert "not configured" in response.text.lower()

