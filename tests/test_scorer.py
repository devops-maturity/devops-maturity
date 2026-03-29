import pytest
from src.core.model import Criteria, UserResponse
from src.core.scorer import calculate_score, score_to_level


@pytest.fixture
def sample_criteria():
    return [
        Criteria(id="D101", category="Basics", criteria="Branch Builds", weight=1.0),
        Criteria(id="D102", category="Basics", criteria="PR Builds", weight=1.0),
        Criteria(id="D201", category="Quality", criteria="Unit Testing", weight=1.0),
        Criteria(
            id="D202", category="Quality", criteria="Functional Testing", weight=1.0
        ),
    ]


class TestCalculateScore:
    def test_all_yes(self, sample_criteria):
        responses = [UserResponse(id=c.id, answer=True) for c in sample_criteria]
        assert calculate_score(sample_criteria, responses) == 100.0

    def test_all_no(self, sample_criteria):
        responses = [UserResponse(id=c.id, answer=False) for c in sample_criteria]
        assert calculate_score(sample_criteria, responses) == 0.0

    def test_half_yes(self, sample_criteria):
        responses = [
            UserResponse(id="D101", answer=True),
            UserResponse(id="D102", answer=True),
            UserResponse(id="D201", answer=False),
            UserResponse(id="D202", answer=False),
        ]
        assert calculate_score(sample_criteria, responses) == 50.0

    def test_empty_responses(self, sample_criteria):
        assert calculate_score(sample_criteria, []) == 0.0

    def test_empty_criteria(self):
        responses = [UserResponse(id="D101", answer=True)]
        assert calculate_score([], responses) == 0.0

    def test_weighted_criteria(self):
        criteria = [
            Criteria(id="A", category="X", criteria="High weight", weight=2.0),
            Criteria(id="B", category="X", criteria="Low weight", weight=1.0),
        ]
        responses = [
            UserResponse(id="A", answer=True),
            UserResponse(id="B", answer=False),
        ]
        score = calculate_score(criteria, responses)
        assert abs(score - (2.0 / 3.0) * 100) < 0.01

    def test_unknown_response_id_ignored(self, sample_criteria):
        responses = [
            UserResponse(id="UNKNOWN", answer=True),
            UserResponse(id="D101", answer=True),
            UserResponse(id="D102", answer=False),
            UserResponse(id="D201", answer=False),
            UserResponse(id="D202", answer=False),
        ]
        score = calculate_score(sample_criteria, responses)
        assert score == 25.0


class TestScoreToLevel:
    def test_wip(self):
        assert score_to_level(0) == "WIP"
        assert score_to_level(29.9) == "WIP"

    def test_passing(self):
        assert score_to_level(30) == "PASSING"
        assert score_to_level(49.9) == "PASSING"

    def test_bronze(self):
        assert score_to_level(50) == "BRONZE"
        assert score_to_level(69.9) == "BRONZE"

    def test_silver(self):
        assert score_to_level(70) == "SILVER"
        assert score_to_level(89.9) == "SILVER"

    def test_gold(self):
        assert score_to_level(90) == "GOLD"
        assert score_to_level(100) == "GOLD"
