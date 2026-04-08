from src.core.scorer import calculate_score, calculate_category_scores, score_to_level
from src.core.model import Criteria, UserResponse


def _make_criteria(n=4, weight=1.0):
    return [
        Criteria(id=f"D{i}", category="Test", criteria=f"Criteria {i}", weight=weight)
        for i in range(n)
    ]


def _make_responses(ids, answer=True):
    return [UserResponse(id=id_, answer=answer) for id_ in ids]


# ── calculate_score ────────────────────────────────────────────────────────────


def test_calculate_score_all_yes():
    criteria = _make_criteria(4)
    responses = _make_responses(["D0", "D1", "D2", "D3"])
    assert calculate_score(criteria, responses) == 100.0


def test_calculate_score_all_no():
    criteria = _make_criteria(4)
    responses = _make_responses(["D0", "D1", "D2", "D3"], answer=False)
    assert calculate_score(criteria, responses) == 0.0


def test_calculate_score_half():
    criteria = _make_criteria(4)
    responses = _make_responses(["D0", "D1"], answer=True) + _make_responses(
        ["D2", "D3"], answer=False
    )
    assert calculate_score(criteria, responses) == 50.0


def test_calculate_score_empty():
    assert calculate_score([], []) == 0.0


def test_calculate_score_weighted():
    criteria = [
        Criteria(id="D1", category="Test", criteria="C1", weight=2.0),
        Criteria(id="D2", category="Test", criteria="C2", weight=1.0),
    ]
    responses = [
        UserResponse(id="D1", answer=True),
        UserResponse(id="D2", answer=False),
    ]
    # 2 / (2 + 1) * 100 ≈ 66.67
    assert abs(calculate_score(criteria, responses) - 66.67) < 0.01


def test_calculate_score_no_matching_responses():
    criteria = _make_criteria(2)
    # responses for IDs that don't exist in criteria
    responses = _make_responses(["X1", "X2"], answer=True)
    assert calculate_score(criteria, responses) == 0.0


# ── score_to_level ─────────────────────────────────────────────────────────────


def test_score_to_level_wip():
    assert score_to_level(0) == "WIP"
    assert score_to_level(29.9) == "WIP"


def test_score_to_level_passing():
    assert score_to_level(30) == "PASSING"
    assert score_to_level(49.9) == "PASSING"


def test_score_to_level_bronze():
    assert score_to_level(50) == "BRONZE"
    assert score_to_level(69.9) == "BRONZE"


def test_score_to_level_silver():
    assert score_to_level(70) == "SILVER"
    assert score_to_level(89.9) == "SILVER"


def test_score_to_level_gold():
    assert score_to_level(90) == "GOLD"
    assert score_to_level(100) == "GOLD"


# ── calculate_category_scores ──────────────────────────────────────────────────


def _make_multi_category_criteria():
    return [
        Criteria(id="A1", category="Alpha", criteria="A1", weight=1.0),
        Criteria(id="A2", category="Alpha", criteria="A2", weight=1.0),
        Criteria(id="B1", category="Beta", criteria="B1", weight=1.0),
        Criteria(id="B2", category="Beta", criteria="B2", weight=0.5),
    ]


def test_category_scores_all_yes():
    criteria = _make_multi_category_criteria()
    responses = _make_responses(["A1", "A2", "B1", "B2"])
    scores = calculate_category_scores(criteria, responses)
    assert scores["Alpha"] == 100.0
    assert scores["Beta"] == 100.0


def test_category_scores_all_no():
    criteria = _make_multi_category_criteria()
    responses = _make_responses(["A1", "A2", "B1", "B2"], answer=False)
    scores = calculate_category_scores(criteria, responses)
    assert scores["Alpha"] == 0.0
    assert scores["Beta"] == 0.0


def test_category_scores_partial():
    criteria = _make_multi_category_criteria()
    responses = [
        UserResponse(id="A1", answer=True),
        UserResponse(id="A2", answer=False),
        UserResponse(id="B1", answer=True),
        UserResponse(id="B2", answer=False),
    ]
    scores = calculate_category_scores(criteria, responses)
    assert scores["Alpha"] == 50.0
    # B1 weight=1.0, B2 weight=0.5 => 1.0 / 1.5 * 100 ≈ 66.67
    assert abs(scores["Beta"] - 66.67) < 0.01


def test_category_scores_keys_match_categories():
    criteria = _make_multi_category_criteria()
    responses = _make_responses(["A1", "A2", "B1", "B2"])
    scores = calculate_category_scores(criteria, responses)
    assert set(scores.keys()) == {"Alpha", "Beta"}


def test_category_scores_empty():
    scores = calculate_category_scores([], [])
    assert scores == {}
