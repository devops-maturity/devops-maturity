from fastapi.testclient import TestClient
from src.web.main import app

client = TestClient(app)


def test_read_form():
    response = client.get("/")
    assert response.status_code == 200
    assert "form" in response.text.lower()
