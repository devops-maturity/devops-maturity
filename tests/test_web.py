import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.web.main import app

client = TestClient(app, follow_redirects=False)


# ── Home page ──────────────────────────────────────────────────────────────────


def test_read_form():
    response = client.get("/")
    assert response.status_code == 200
    assert "form" in response.text.lower()


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
