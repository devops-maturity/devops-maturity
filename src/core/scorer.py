from typing import List
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
