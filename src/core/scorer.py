from typing import Dict, List
from .model import Criteria, UserResponse


def calculate_score(criteria: List[Criteria], responses: List[UserResponse]) -> float:
    total = 0.0
    max_score = 0.0
    response_map = {r.id: r.answer for r in responses}

    for c in criteria:
        max_score += c.weight
        if response_map.get(c.id):
            total += c.weight

    return (total / max_score) * 100 if max_score else 0.0


def calculate_category_scores(
    criteria: List[Criteria], responses: List[UserResponse]
) -> Dict[str, float]:
    """Return a score (0–100) for each category."""
    response_map = {r.id: r.answer for r in responses}
    totals: Dict[str, float] = {}
    maxes: Dict[str, float] = {}

    for c in criteria:
        maxes[c.category] = maxes.get(c.category, 0.0) + c.weight
        if response_map.get(c.id):
            totals[c.category] = totals.get(c.category, 0.0) + c.weight

    return {cat: (totals.get(cat, 0.0) / maxes[cat]) * 100 for cat in maxes}


def score_to_level(score: float) -> str:
    if score < 30:
        return "WIP"
    elif score < 50:
        return "PASSING"
    elif score < 70:
        return "BRONZE"
    elif score < 90:
        return "SILVER"
    else:
        return "GOLD"
