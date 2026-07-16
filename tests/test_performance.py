"""Performance benchmarks for core DevOps Maturity functions.

These benchmarks use pytest-benchmark to measure the execution time of the
scoring, category-score calculation, badge-URL lookup, and criteria-loading
hot-paths so that regressions can be caught early.
"""

from src.config.loader import load_criteria_config
from src.core.badge import get_badge_url
from src.core.model import Criteria, UserResponse
from src.core.scorer import calculate_category_scores, calculate_score, score_to_level


# ── helpers ────────────────────────────────────────────────────────────────────


def _make_criteria(n: int = 20, weight: float = 1.0):
    return [
        Criteria(
            id=f"D{i:03d}",
            category=f"Cat{i % 5}",
            criteria=f"Criteria {i}",
            weight=weight,
        )
        for i in range(n)
    ]


def _make_responses(criteria, answer: bool = True):
    return [UserResponse(id=c.id, answer=answer) for c in criteria]


# ── calculate_score ────────────────────────────────────────────────────────────


def test_benchmark_calculate_score_small(benchmark):
    criteria = _make_criteria(10)
    responses = _make_responses(criteria)
    result = benchmark(calculate_score, criteria, responses)
    assert result == 100.0


def test_benchmark_calculate_score_large(benchmark):
    criteria = _make_criteria(100)
    responses = _make_responses(criteria, answer=False)
    result = benchmark(calculate_score, criteria, responses)
    assert result == 0.0


# ── calculate_category_scores ──────────────────────────────────────────────────


def test_benchmark_calculate_category_scores(benchmark):
    criteria = _make_criteria(20)
    responses = _make_responses(criteria)
    result = benchmark(calculate_category_scores, criteria, responses)
    assert len(result) == 5  # 5 categories (Cat0–Cat4)


# ── score_to_level ─────────────────────────────────────────────────────────────


def test_benchmark_score_to_level(benchmark):
    result = benchmark(score_to_level, 75.0)
    assert result == "SILVER"


# ── get_badge_url ──────────────────────────────────────────────────────────────


def test_benchmark_get_badge_url(benchmark):
    result = benchmark(get_badge_url, "GOLD")
    assert "GOLD" in result


# ── load_criteria_config ───────────────────────────────────────────────────────


def test_benchmark_load_criteria_config(benchmark):
    categories, criteria = benchmark(load_criteria_config)
    assert len(criteria) > 0
    assert len(categories) > 0
