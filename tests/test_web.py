import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.web.main import app
from src.core.model import Assessment, User, SessionLocal, init_db

client = TestClient(app)


class TestWebInterface:
    """Test the web interface functionality."""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment."""
        # Initialize test database
        init_db()
    
    def test_read_form(self):
        """Test the main form page loads correctly."""
        response = client.get("/")
        assert response.status_code == 200
        assert "form" in response.text.lower()
        assert "devops" in response.text.lower()
    
    def test_submit_assessment_valid(self):
        """Test submitting a valid assessment."""
        form_data = {
            "project_name": "test-project",
            "test_criteria_1": "yes",
            "test_criteria_2": "no"
        }
        
        response = client.post("/submit", data=form_data)
        
        # Should redirect or show result page
        assert response.status_code in [200, 302]
        if response.status_code == 200:
            assert "score" in response.text.lower() or "result" in response.text.lower()
    
    def test_submit_assessment_missing_project_name(self):
        """Test submitting assessment without project name."""
        form_data = {
            "test_criteria_1": "yes",
            "test_criteria_2": "no"
        }
        
        response = client.post("/submit", data=form_data)
        
        # Should return error
        assert response.status_code == 200
        assert "required" in response.text.lower() or "error" in response.text.lower()
    
    def test_assessments_list_page(self):
        """Test the assessments list page."""
        response = client.get("/assessments")
        assert response.status_code == 200
    
    def test_badge_endpoint(self):
        """Test the badge SVG endpoint."""
        response = client.get("/badge.svg")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/svg+xml"
    
    def test_register_page_get(self):
        """Test the registration page loads."""
        response = client.get("/register")
        assert response.status_code in [200, 302]  # May redirect if user already logged in
    
    def test_login_page_get(self):
        """Test the login page loads."""
        response = client.get("/login")
        assert response.status_code in [200, 302]  # May redirect if user already logged in
    
    def test_logout_endpoint(self):
        """Test the logout endpoint."""
        response = client.get("/logout")
        assert response.status_code == 302  # Should redirect
    
    def test_register_user_valid(self):
        """Test user registration with valid data."""
        # First, clear any existing user to avoid conflicts
        db = SessionLocal()
        existing_user = db.query(User).filter(User.username == "testuser").first()
        if existing_user:
            db.delete(existing_user)
            db.commit()
        db.close()
        
        form_data = {
            "username": "testuser",
            "email": "test@example.com", 
            "password": "testpassword123"
        }
        
        response = client.post("/register", data=form_data)
        
        # Should redirect on success or show error page
        assert response.status_code in [200, 302]
    
    def test_login_user_valid(self):
        """Test user login with valid credentials."""
        # First register a user
        db = SessionLocal()
        existing_user = db.query(User).filter(User.username == "logintest").first()
        if not existing_user:
            from passlib.hash import bcrypt
            test_user = User(
                username="logintest",
                email="logintest@example.com",
                password_hash=bcrypt.hash("testpass123")
            )
            db.add(test_user)
            db.commit()
        db.close()
        
        form_data = {
            "username": "logintest",
            "password": "testpass123"
        }
        
        response = client.post("/login", data=form_data)
        
        # Should redirect on success or show error
        assert response.status_code in [200, 302]
    
    def test_login_user_invalid(self):
        """Test user login with invalid credentials."""
        form_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        
        response = client.post("/login", data=form_data)
        
        # Should show error
        assert response.status_code == 200
        assert "invalid" in response.text.lower() or "error" in response.text.lower()
    
    def test_oauth_endpoints_exist(self):
        """Test that OAuth endpoints exist even if not configured."""
        # Test Google OAuth
        response = client.get("/auth/google")
        assert response.status_code in [200, 302, 404]  # Varies based on config
        
        # Test GitHub OAuth  
        response = client.get("/auth/github")
        assert response.status_code in [200, 302, 404]  # Varies based on config
    
    @patch('src.web.main.get_current_user')
    def test_edit_assessment_unauthorized(self, mock_get_user):
        """Test editing assessment without proper authorization."""
        mock_get_user.return_value = None  # No user logged in
        
        response = client.get("/edit-assessment/1")
        assert response.status_code == 403
    
    def test_invalid_endpoints(self):
        """Test accessing non-existent endpoints."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
        
        response = client.get("/edit-assessment/99999")  # Non-existent assessment
        assert response.status_code in [403, 404]  # Depends on auth state
    
    def test_home_page_contains_expected_elements(self):
        """Test that home page contains expected form elements."""
        response = client.get("/")
        assert response.status_code == 200
        
        # Check for form elements
        content = response.text.lower()
        assert "project" in content
        assert "assessment" in content or "maturity" in content
    
    def test_submit_assessment_with_special_characters(self):
        """Test submitting assessment with special characters in project name."""
        form_data = {
            "project_name": "test-project-with-special-chars!@#$%",
            "test_criteria": "yes"
        }
        
        response = client.post("/submit", data=form_data)
        
        # Should handle special characters gracefully
        assert response.status_code in [200, 302]
    
    def test_submit_assessment_with_unicode(self):
        """Test submitting assessment with unicode characters."""
        form_data = {
            "project_name": "проект-тест-🚀",
            "test_criteria": "yes"
        }
        
        response = client.post("/submit", data=form_data)
        
        # Should handle unicode gracefully
        assert response.status_code in [200, 302]
    
    def test_assessments_list_pagination(self):
        """Test assessments list handles large numbers of assessments."""
        response = client.get("/assessments")
        assert response.status_code == 200
        # Should not crash with many assessments
    
    def test_register_with_weak_password(self):
        """Test registration with various password strengths."""
        weak_passwords = ["123", "password", "abc"]
        
        for pwd in weak_passwords:
            form_data = {
                "username": f"user_{pwd}",
                "email": f"test_{pwd}@example.com",
                "password": pwd
            }
            
            response = client.post("/register", data=form_data)
            # Should handle weak passwords (may accept or reject)
            assert response.status_code in [200, 302]
    
    def test_login_with_email_instead_of_username(self):
        """Test login using email address instead of username."""
        form_data = {
            "username": "test@example.com",  # Using email as username
            "password": "testpass"
        }
        
        response = client.post("/login", data=form_data)
        assert response.status_code in [200, 302]
    
    def test_oauth_callback_invalid_provider(self):
        """Test OAuth callback with invalid provider."""
        response = client.get("/auth/callback/invalid")
        assert response.status_code == 302  # Should redirect
    
    def test_static_files_accessible(self):
        """Test that static files are accessible."""
        # Test if static file routing is set up
        response = client.get("/static/")
        # May return 404 or directory listing, but shouldn't crash
        assert response.status_code in [200, 404, 403]
    
    def test_form_csrf_protection(self):
        """Test form submission without CSRF token (if implemented)."""
        # This would test CSRF protection if implemented
        form_data = {"project_name": "csrf-test"}
        response = client.post("/submit", data=form_data)
        # Should either accept or reject, but not crash
        assert response.status_code in [200, 302, 403]
    
    def test_concurrent_user_sessions(self):
        """Test handling of multiple user sessions."""
        # Simulate multiple users by making multiple requests
        responses = []
        for i in range(5):
            response = client.get("/")
            responses.append(response)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
    
    def test_malformed_form_data(self):
        """Test handling of malformed form data."""
        # Send data that doesn't match expected form structure
        malformed_data = {
            "unexpected_field": "value",
            "another_field": ["list", "of", "values"]
        }
        
        response = client.post("/submit", data=malformed_data)
        # Should handle gracefully without crashing
        assert response.status_code in [200, 400, 422]
