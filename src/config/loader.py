import yaml
import os
from typing import List
from core.model import Criteria


def load_criteria_config() -> tuple[List[str], List[Criteria]]:
    """Load categories and criteria from YAML config file."""
    config_path = os.path.join(os.path.dirname(__file__), "criteria.yaml")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    categories = config["categories"]
    criteria = [
        Criteria(
            id=item["id"],
            category=item["category"],
            criteria=item["criteria"],
            weight=item["weight"],
        )
        for item in config["criteria"]
    ]

    return categories, criteria
