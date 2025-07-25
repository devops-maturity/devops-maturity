import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.core.model import Base, Assessment, User, init_db


class TestDatabase:
    """Test database models and operations."""
    
    def setup_method(self):
        """Set up test database."""
        # Create a temporary in-memory database for testing
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        TestSession = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = TestSession()
    
    def teardown_method(self):
        """Clean up test database."""
        self.db.close()
    
    def test_create_assessment(self):
        """Test creating an assessment record."""
        assessment = Assessment(
            project_name="test-project",
            user_id=1,
            responses={"criteria1": True, "criteria2": False}
        )
        
        self.db.add(assessment)
        self.db.commit()
        
        # Verify assessment was created
        saved_assessment = self.db.query(Assessment).first()
        assert saved_assessment is not None
        assert saved_assessment.project_name == "test-project"
        assert saved_assessment.user_id == 1
        assert saved_assessment.responses == {"criteria1": True, "criteria2": False}
    
    def test_create_assessment_without_user(self):
        """Test creating an assessment without a user."""
        assessment = Assessment(
            project_name="anonymous-project",
            user_id=None,
            responses={"criteria1": True}
        )
        
        self.db.add(assessment)
        self.db.commit()
        
        # Verify assessment was created
        saved_assessment = self.db.query(Assessment).first()
        assert saved_assessment is not None
        assert saved_assessment.project_name == "anonymous-project"
        assert saved_assessment.user_id is None
    
    def test_create_user(self):
        """Test creating a user record."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        
        self.db.add(user)
        self.db.commit()
        
        # Verify user was created
        saved_user = self.db.query(User).first()
        assert saved_user is not None
        assert saved_user.username == "testuser"
        assert saved_user.email == "test@example.com"
        assert saved_user.password_hash == "hashed_password"
        assert saved_user.oauth_provider is None
        assert saved_user.oauth_id is None
    
    def test_create_oauth_user(self):
        """Test creating a user with OAuth credentials."""
        user = User(
            username="oauthuser",
            email="oauth@example.com",
            oauth_provider="google",
            oauth_id="12345"
        )
        
        self.db.add(user)
        self.db.commit()
        
        # Verify OAuth user was created
        saved_user = self.db.query(User).first()
        assert saved_user is not None
        assert saved_user.username == "oauthuser"
        assert saved_user.email == "oauth@example.com"
        assert saved_user.password_hash is None
        assert saved_user.oauth_provider == "google"
        assert saved_user.oauth_id == "12345"
    
    def test_user_username_unique(self):
        """Test that usernames must be unique."""
        user1 = User(username="duplicate", email="user1@example.com")
        user2 = User(username="duplicate", email="user2@example.com")
        
        self.db.add(user1)
        self.db.commit()
        
        # Adding second user with same username should fail
        self.db.add(user2)
        with pytest.raises(Exception):  # Should raise integrity error
            self.db.commit()
    
    def test_user_email_unique(self):
        """Test that email addresses must be unique."""
        user1 = User(username="user1", email="duplicate@example.com")
        user2 = User(username="user2", email="duplicate@example.com")
        
        self.db.add(user1)
        self.db.commit()
        
        # Adding second user with same email should fail
        self.db.add(user2)
        with pytest.raises(Exception):  # Should raise integrity error
            self.db.commit()
    
    def test_assessment_responses_json(self):
        """Test that assessment responses are stored as JSON."""
        complex_responses = {
            "criteria1": True,
            "criteria2": False,
            "criteria3": True,
            "nested": {"subcriteria": True}
        }
        
        assessment = Assessment(
            project_name="json-test",
            responses=complex_responses
        )
        
        self.db.add(assessment)
        self.db.commit()
        
        # Verify JSON storage and retrieval
        saved_assessment = self.db.query(Assessment).first()
        assert saved_assessment.responses == complex_responses
    
    def test_multiple_assessments_same_user(self):
        """Test that a user can have multiple assessments."""
        # Create a user first
        user = User(username="multiuser", email="multi@example.com")
        self.db.add(user)
        self.db.commit()
        
        # Create multiple assessments for the same user
        assessment1 = Assessment(
            project_name="project1",
            user_id=user.id,
            responses={"criteria1": True}
        )
        assessment2 = Assessment(
            project_name="project2", 
            user_id=user.id,
            responses={"criteria1": False}
        )
        
        self.db.add(assessment1)
        self.db.add(assessment2)
        self.db.commit()
        
        # Verify both assessments exist
        assessments = self.db.query(Assessment).filter(Assessment.user_id == user.id).all()
        assert len(assessments) == 2
        assert {a.project_name for a in assessments} == {"project1", "project2"}
    
    def test_init_db_function(self):
        """Test the init_db function."""
        # This should not raise any exceptions
        init_db()
        
        # Verify that the function can be called multiple times safely
        init_db()
        init_db()
    
    def test_assessment_without_project_name_fails(self):
        """Test that assessments require a project name."""
        assessment = Assessment(
            user_id=1,
            responses={"criteria1": True}
            # Missing project_name
        )
        
        self.db.add(assessment)
        with pytest.raises(Exception):  # Should raise integrity error
            self.db.commit()