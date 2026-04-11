"""Performance benchmarks for the core DevOps Maturity assessment engine.

These tests use pytest-benchmark to measure execution time of key functions and
ensure no performance regressions are introduced over time.
"""

from fastapi.testclient import TestClient

from src.core.badge import get_badge_url
from src.core.model import Criteria, UserResponse
from src.core.scorer import calculate_category_scores, calculate_score, score_to_level
from src.web.main import app

client = TestClient(app)

# ── Fixtures ───────────────────────────────────────────────────────────────────

LEVELS = ["WIP", "PASSING", "BRONZE", "SILVER", "GOLD"]


def _make_criteria(n: int = 25) -> list[Criteria]:
    categories = ["Basics", "Quality", "Security", "Supply Chain", "Analysis"]
    return [
        Criteria(
            id=f"D{i:03d}",
            category=categories[i % len(categories)],
            criteria=f"Criteria {i}",
            weight=1.0 if i % 2 == 0 else 0.5,
        )
        for i in range(n)
    ]


def _make_responses(criteria: list[Criteria], answer: bool = True) -> list[UserResponse]:
    return [UserResponse(id=c.id, answer=answer) for c in criteria]


# ── Scorer benchmarks ──────────────────────────────────────────────────────────


def test_benchmark_calculate_score(benchmark):
    criteria = _make_criteria(25)
    responses = _make_responses(criteria)
    result = benchmark(calculate_score, criteria, responses)
    assert result == 100.0


def test_benchmark_calculate_score_large(benchmark):
    criteria = _make_criteria(200)
    responses = _make_responses(criteria, answer=True)
    result = benchmark(calculate_score, criteria, responses)
    assert result == 100.0


def test_benchmark_calculate_category_scores(benchmark):
    criteria = _make_criteria(25)
    responses = _make_responses(criteria)
    result = benchmark(calculate_category_scores, criteria, responses)
    assert len(result) > 0


def test_benchmark_score_to_level(benchmark):
    result = benchmark(score_to_level, 75.0)
    assert result == "SILVER"


# ── Badge benchmarks ───────────────────────────────────────────────────────────


def test_benchmark_get_badge_url(benchmark):
    result = benchmark(get_badge_url, "GOLD")
    assert "GOLD" in result


def test_benchmark_get_badge_url_all_levels(benchmark):
    def _all_badge_urls():
        return [get_badge_url(level) for level in LEVELS]

    results = benchmark(_all_badge_urls)
    assert len(results) == len(LEVELS)


# ── HTTP endpoint benchmarks ───────────────────────────────────────────────────


def test_benchmark_home_page(benchmark):
    result = benchmark(client.get, "/")
    assert result.status_code == 200


def test_benchmark_assessments_page(benchmark):
    result = benchmark(client.get, "/assessments")
    assert result.status_code == 200


def test_benchmark_badge_svg(benchmark):
    result = benchmark(client.get, "/badge.svg")
    assert result.status_code == 200
