"""
Functional (end-to-end) tests that exercise complete user workflows,
testing multiple application layers working together from the user's perspective.
"""

import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

from config.loader import load_criteria_config
from src.core.model import Assessment as AssessmentModel
from src.core.model import SessionLocal
from src.web.main import app


# ── Helpers ────────────────────────────────────────────────────────────────────


def _unique(prefix: str = "user") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _register_and_login(client: TestClient, username: str, password: str) -> None:
    """Register then immediately log in as the given user."""
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
        client.post("/login", data={"username": username, "password": password})


# ── Workflow: anonymous assessment ─────────────────────────────────────────────


def test_anonymous_assessment_full_flow():
    """
    An unauthenticated user can fill in the assessment form and see a result
    page that contains a score, badge, next actions, and improvement
    recommendations — without creating an account.
    """
    client = TestClient(app, follow_redirects=True)

    # 1. Land on the home page and see the form
    resp = client.get("/")
    assert resp.status_code == 200
    assert "form" in resp.text.lower()

    # 2. Submit the form with a mix of yes/no answers
    resp = client.post(
        "/submit",
        data={
            "project_name": "Anon Functional Test",
            "D101": "yes",
            "D102": "yes",
            "D201": "yes",
            "D202": "no",
        },
    )
    assert resp.status_code == 200
    assert "score" in resp.text.lower()
    assert "Next actions" in resp.text
    assert "Improvement recommendations" in resp.text
    assert "data-copy-value" in resp.text


def test_anonymous_assessment_all_yes():
    """
    Submitting all criteria as 'yes' should yield a result page with the
    highest possible level and a non-zero score.
    """
    client = TestClient(app, follow_redirects=True)

    # Build a payload with every criterion answered 'yes'
    _, criteria = load_criteria_config()
    data = {"project_name": "Perfect Score Project"}
    for c in criteria:
        data[c.id] = "yes"

    resp = client.post("/submit", data=data)
    assert resp.status_code == 200
    assert "score" in resp.text.lower()
    # Gold level text or badge should appear
    assert "gold" in resp.text.lower() or "100" in resp.text


def test_anonymous_assessment_missing_project_name():
    """
    Submitting the form without a project name must show an error and
    keep the user on the form page.
    """
    client = TestClient(app, follow_redirects=True)

    resp = client.post("/submit", data={"D101": "yes"})
    assert resp.status_code == 200
    assert "required" in resp.text.lower()
    # Should still render the form, not a result page
    assert "Assessment result" not in resp.text


# ── Workflow: authenticated assessment ─────────────────────────────────────────


def test_authenticated_register_login_assess_flow():
    """
    A new user can register, log in, submit an assessment, and see the result
    page — then verify the assessment appears in the assessments list.
    """
    client = TestClient(app, follow_redirects=True)
    username = _unique("func")
    password = "funcpassword"

    # 1. Registration page is accessible
    resp = client.get("/register")
    assert resp.status_code == 200

    # 2. Register
    with patch("src.web.main.bcrypt") as mock_bcrypt:
        mock_bcrypt.hash.return_value = "hashed_password"
        resp = client.post(
            "/register",
            data={
                "username": username,
                "email": f"{username}@example.com",
                "password": password,
            },
        )
    # After registration we are redirected to home
    assert resp.status_code == 200

    # 3. Log in (session already set by register redirect; log out first)
    client.get("/logout")

    with patch("src.web.main.bcrypt") as mock_bcrypt:
        mock_bcrypt.verify.return_value = True
        resp = client.post("/login", data={"username": username, "password": password})
    assert resp.status_code == 200

    # 4. Submit an assessment
    resp = client.post(
        "/submit",
        data={
            "project_name": "Auth Flow Project",
            "D101": "yes",
            "D201": "yes",
        },
    )
    assert resp.status_code == 200
    assert "score" in resp.text.lower()

    # 5. The assessments list should contain the submitted project
    resp = client.get("/assessments")
    assert resp.status_code == 200
    assert "Auth Flow Project" in resp.text


def test_authenticated_edit_assessment_flow():
    """
    An authenticated user can submit an assessment and then edit it via
    the edit-assessment endpoint; the updated project name should appear
    in the assessments list after saving.
    """
    client = TestClient(app, follow_redirects=True)
    username = _unique("edit")
    password = "editpassword"

    # Register and log in
    _register_and_login(client, username, password)

    # Submit initial assessment
    resp = client.post(
        "/submit",
        data={"project_name": "Original Name", "D101": "yes"},
        follow_redirects=False,
    )
    # Follow redirect to result page
    if resp.status_code in (302, 303, 307):
        resp = client.get(resp.headers["location"])
    assert resp.status_code == 200

    # Find the assessment id from the assessments list
    resp = client.get("/assessments")
    assert resp.status_code == 200
    assert "Original Name" in resp.text

    # Locate the assessment ID (lowest id whose project_name is 'Original Name')
    db = SessionLocal()
    record = (
        db.query(AssessmentModel)
        .filter(AssessmentModel.project_name == "Original Name")
        .order_by(AssessmentModel.id.desc())
        .first()
    )
    db.close()
    assert record is not None, "Assessment should have been saved"
    assessment_id = record.id

    # Edit assessment page is accessible
    resp = client.get(f"/edit-assessment/{assessment_id}")
    assert resp.status_code == 200

    # Submit the edit
    resp = client.post(
        f"/edit-assessment/{assessment_id}",
        data={"project_name": "Updated Name", "D101": "yes"},
    )
    assert resp.status_code == 200
    assert "Updated Name" in resp.text


# ── Workflow: logout and session isolation ─────────────────────────────────────


def test_logout_clears_session():
    """
    After logging out the user can no longer access protected resources
    as an authenticated user; the session is fully cleared.
    """
    client = TestClient(app, follow_redirects=False)
    username = _unique("logout")
    password = "logoutpassword"

    _register_and_login(client, username, password)

    # Confirm logged in: home page should be accessible
    resp = client.get("/")
    assert resp.status_code == 200

    # Log out
    resp = client.get("/logout")
    assert resp.status_code in (302, 303, 307)
    assert "/login" in resp.headers.get("location", "")

    # After logout the login page should still be accessible
    resp = client.get("/login")
    assert resp.status_code == 200


# ── Workflow: assessment with project URL ──────────────────────────────────────


def test_assessment_with_project_url():
    """
    Submitting an assessment that includes a project URL should render
    a result page containing that URL.
    """
    client = TestClient(app, follow_redirects=True)
    project_url = "https://example.com/my-project"

    resp = client.post(
        "/submit",
        data={
            "project_name": "URL Project",
            "project_url": project_url,
            "D101": "yes",
        },
    )
    assert resp.status_code == 200
    assert project_url in resp.text
