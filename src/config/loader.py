import os

import yaml

from core.model import Criteria


def load_criteria_config() -> tuple[list[str], list[Criteria]]:
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
            description=item.get("description", ""),
        )
        for item in config["criteria"]
    ]

    return categories, criteria
