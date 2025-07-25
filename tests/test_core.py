import pytest
from src.core.model import Criteria, UserResponse
from src.core.scorer import calculate_score, score_to_level
from src.core.badge import get_badge_url


class TestScorer:
    """Test the scoring functionality."""
    
    def setup_method(self):
        """Set up test data."""
        self.criteria = [
            Criteria(id="test1", category="Test", criteria="Test criteria 1", weight=1.0),
            Criteria(id="test2", category="Test", criteria="Test criteria 2", weight=2.0),
            Criteria(id="test3", category="Test", criteria="Test criteria 3", weight=1.5),
        ]
    
    def test_calculate_score_all_yes(self):
        """Test score calculation when all answers are yes."""
        responses = [
            UserResponse(id="test1", answer=True),
            UserResponse(id="test2", answer=True),
            UserResponse(id="test3", answer=True),
        ]
        score = calculate_score(self.criteria, responses)
        assert score == 100.0
    
    def test_calculate_score_all_no(self):
        """Test score calculation when all answers are no."""
        responses = [
            UserResponse(id="test1", answer=False),
            UserResponse(id="test2", answer=False),
            UserResponse(id="test3", answer=False),
        ]
        score = calculate_score(self.criteria, responses)
        assert score == 0.0
    
    def test_calculate_score_partial(self):
        """Test score calculation with partial positive answers."""
        responses = [
            UserResponse(id="test1", answer=True),   # 1.0 weight
            UserResponse(id="test2", answer=False),  # 2.0 weight (not counted)
            UserResponse(id="test3", answer=True),   # 1.5 weight
        ]
        # Total weight = 4.5, achieved = 2.5
        # Score = (2.5 / 4.5) * 100 = 55.56
        score = calculate_score(self.criteria, responses)
        assert abs(score - 55.555555555555556) < 0.001
    
    def test_calculate_score_empty_criteria(self):
        """Test score calculation with empty criteria list."""
        responses = []
        score = calculate_score([], responses)
        assert score == 0.0
    
    def test_calculate_score_missing_responses(self):
        """Test score calculation when some responses are missing."""
        responses = [
            UserResponse(id="test1", answer=True),
            # test2 and test3 missing
        ]
        # Only test1 contributes: 1.0 out of 4.5 total
        score = calculate_score(self.criteria, responses)
        assert abs(score - 22.222222222222225) < 0.001
    
    def test_score_to_level_wip(self):
        """Test level assignment for WIP range."""
        assert score_to_level(0) == "WIP"
        assert score_to_level(15) == "WIP"
        assert score_to_level(29.9) == "WIP"
    
    def test_score_to_level_passing(self):
        """Test level assignment for PASSING range."""
        assert score_to_level(30) == "PASSING"
        assert score_to_level(40) == "PASSING"
        assert score_to_level(49.9) == "PASSING"
    
    def test_score_to_level_bronze(self):
        """Test level assignment for BRONZE range."""
        assert score_to_level(50) == "BRONZE"
        assert score_to_level(60) == "BRONZE"
        assert score_to_level(69.9) == "BRONZE"
    
    def test_score_to_level_silver(self):
        """Test level assignment for SILVER range."""
        assert score_to_level(70) == "SILVER"
        assert score_to_level(80) == "SILVER"
        assert score_to_level(89.9) == "SILVER"
    
    def test_score_to_level_boundary_values(self):
        """Test level assignment for exact boundary values."""
        assert score_to_level(29.99999) == "WIP"
        assert score_to_level(30.0) == "PASSING"
        assert score_to_level(49.99999) == "PASSING"
        assert score_to_level(50.0) == "BRONZE"
        assert score_to_level(69.99999) == "BRONZE"
        assert score_to_level(70.0) == "SILVER"
        assert score_to_level(89.99999) == "SILVER"
        assert score_to_level(90.0) == "GOLD"
    
    def test_calculate_score_edge_case_weights(self):
        """Test score calculation with various weight combinations."""
        criteria = [
            Criteria(id="heavy", category="Test", criteria="Heavy weight", weight=10.0),
            Criteria(id="light", category="Test", criteria="Light weight", weight=0.1),
            Criteria(id="medium", category="Test", criteria="Medium weight", weight=1.0),
        ]
        
        # Only heavy weight answered yes
        responses = [
            UserResponse(id="heavy", answer=True),
            UserResponse(id="light", answer=False),
            UserResponse(id="medium", answer=False),
        ]
        # Score should be (10.0 / 11.1) * 100 ≈ 90.09
        score = calculate_score(criteria, responses)
        assert 90.0 < score < 91.0
    
    def test_calculate_score_with_duplicate_responses(self):
        """Test score calculation when responses contain duplicates."""
        criteria = [
            Criteria(id="test1", category="Test", criteria="Test 1", weight=1.0),
            Criteria(id="test2", category="Test", criteria="Test 2", weight=1.0),
        ]
        
        responses = [
            UserResponse(id="test1", answer=True),
            UserResponse(id="test1", answer=False),  # Duplicate - last one should win
            UserResponse(id="test2", answer=True),
        ]
        # Score calculation uses dict mapping, so last value for test1 (False) should be used
        # Expected: (0 + 1) / 2 * 100 = 50
        score = calculate_score(criteria, responses)
        assert score == 50.0
    
    def test_calculate_score_extreme_weights(self):
        """Test score calculation with extreme weight values."""
        criteria = [
            Criteria(id="tiny", category="Test", criteria="Tiny weight", weight=0.000001),
            Criteria(id="huge", category="Test", criteria="Huge weight", weight=1000000.0),
        ]
        
        responses = [
            UserResponse(id="tiny", answer=True),
            UserResponse(id="huge", answer=False),
        ]
        # Score should be very close to 0 due to huge weight not being achieved
        score = calculate_score(criteria, responses)
        assert score < 0.01
    
    def test_score_to_level_negative_scores(self):
        """Test level assignment for negative scores (edge case)."""
        assert score_to_level(-10) == "WIP"
        assert score_to_level(-0.1) == "WIP"
    
    def test_score_to_level_over_100(self):
        """Test level assignment for scores over 100 (edge case)."""
        assert score_to_level(150) == "GOLD"
        assert score_to_level(100.1) == "GOLD"


class TestBadge:
    """Test the badge URL functionality."""
    
    def test_get_badge_url_wip(self):
        """Test badge URL for WIP level."""
        url = get_badge_url("WIP")
        assert url == "https://img.shields.io/badge/DevOps%20Maturity-WIP-red.svg"
    
    def test_get_badge_url_passing(self):
        """Test badge URL for PASSING level."""
        url = get_badge_url("PASSING")
        assert url == "https://img.shields.io/badge/DevOps%20Maturity-PASSING-green.svg"
    
    def test_get_badge_url_bronze(self):
        """Test badge URL for BRONZE level."""
        url = get_badge_url("BRONZE")
        assert url == "https://img.shields.io/badge/DevOps%20Maturity-BRONZE-yellow.svg"
    
    def test_get_badge_url_silver(self):
        """Test badge URL for SILVER level."""
        url = get_badge_url("SILVER")
        assert url == "https://img.shields.io/badge/DevOps%20Maturity-SILVER-silver.svg"
    
    def test_get_badge_url_gold(self):
        """Test badge URL for GOLD level."""
        url = get_badge_url("GOLD")
        assert url == "https://img.shields.io/badge/DevOps%20Maturity-GOLD-gold.svg"
    
    def test_get_badge_url_case_insensitive(self):
        """Test badge URL with lowercase input."""
        url = get_badge_url("gold")
        assert url == "https://img.shields.io/badge/DevOps%20Maturity-GOLD-gold.svg"
        
        url = get_badge_url("Bronze")
        assert url == "https://img.shields.io/badge/DevOps%20Maturity-BRONZE-yellow.svg"
    
    def test_get_badge_url_with_none(self):
        """Test badge URL with None input."""
        url = get_badge_url(None)
        assert url == "https://img.shields.io/badge/DevOps%20Maturity-WIP-red.svg"
    
    def test_get_badge_url_with_numeric_input(self):
        """Test badge URL with numeric input."""
        url = get_badge_url(123)
        assert url == "https://img.shields.io/badge/DevOps%20Maturity-WIP-red.svg"
    
    def test_get_badge_url_with_whitespace(self):
        """Test badge URL with whitespace."""
        url = get_badge_url("  GOLD  ")
        assert url == "https://img.shields.io/badge/DevOps%20Maturity-WIP-red.svg"  # Exact match required
    
    def test_badge_url_format_validation(self):
        """Test that all badge URLs follow expected format."""
        levels = ["WIP", "PASSING", "BRONZE", "SILVER", "GOLD"]
        for level in levels:
            url = get_badge_url(level)
            assert url.startswith("https://img.shields.io/badge/DevOps%20Maturity-")
            assert url.endswith(".svg")
            assert level in url


class TestModels:
    """Test the data models."""
    
    def test_criteria_model(self):
        """Test Criteria model creation and validation."""
        criteria = Criteria(
            id="test_id",
            category="Test Category",
            criteria="Test criteria description",
            weight=2.5
        )
        assert criteria.id == "test_id"
        assert criteria.category == "Test Category"
        assert criteria.criteria == "Test criteria description"
        assert criteria.weight == 2.5
    
    def test_user_response_validation(self):
        """Test UserResponse model with various inputs."""
        # Test with boolean True
        response = UserResponse(id="test", answer=True)
        assert response.answer is True
        
        # Test with boolean False
        response = UserResponse(id="test", answer=False)
        assert response.answer is False
    
    def test_criteria_model_validation(self):
        """Test Criteria model with edge case values."""
        # Test with minimum valid weight
        criteria = Criteria(id="test", category="Test", criteria="Test", weight=0.01)
        assert criteria.weight == 0.01
        
        # Test with large weight
        criteria = Criteria(id="test", category="Test", criteria="Test", weight=1000.0)
        assert criteria.weight == 1000.0
    
    def test_models_string_representation(self):
        """Test string representation of models."""
        criteria = Criteria(id="test", category="Test", criteria="Test criteria", weight=1.0)
        # Should not raise errors when converted to string
        str_repr = str(criteria)
        assert "test" in str_repr.lower()
        
        response = UserResponse(id="test", answer=True)
        str_repr = str(response)
        assert "test" in str_repr.lower()