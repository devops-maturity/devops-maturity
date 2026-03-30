from src.config.loader import load_criteria_config


def test_load_criteria_config_returns_lists():
    categories, criteria = load_criteria_config()
    assert isinstance(categories, list)
    assert isinstance(criteria, list)


def test_load_criteria_config_non_empty():
    categories, criteria = load_criteria_config()
    assert len(categories) > 0
    assert len(criteria) > 0


def test_load_criteria_config_expected_categories():
    categories, _ = load_criteria_config()
    assert "Basics" in categories
    assert "Quality" in categories
    assert "Security" in categories


def test_load_criteria_config_criteria_fields():
    _, criteria = load_criteria_config()
    for c in criteria:
        assert c.id
        assert c.category
        assert c.criteria
        assert c.weight > 0


def test_load_criteria_config_categories_match_criteria():
    """Every criterion's category must be one of the declared categories."""
    categories, criteria = load_criteria_config()
    for c in criteria:
        assert c.category in categories, (
            f"Criterion {c.id} has unknown category '{c.category}'"
        )
