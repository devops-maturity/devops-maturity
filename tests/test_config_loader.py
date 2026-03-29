from src.config.loader import load_criteria_config


class TestLoadCriteriaConfig:
    def test_returns_tuple(self):
        result = load_criteria_config()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_categories_is_list(self):
        categories, _ = load_criteria_config()
        assert isinstance(categories, list)
        assert len(categories) > 0

    def test_criteria_is_list(self):
        _, criteria = load_criteria_config()
        assert isinstance(criteria, list)
        assert len(criteria) > 0

    def test_criteria_are_criteria_objects(self):
        _, criteria = load_criteria_config()
        for c in criteria:
            assert type(c).__name__ == "Criteria"

    def test_criteria_have_required_fields(self):
        _, criteria = load_criteria_config()
        for c in criteria:
            assert c.id
            assert c.category
            assert c.criteria
            assert c.weight > 0

    def test_criteria_categories_are_in_categories_list(self):
        categories, criteria = load_criteria_config()
        for c in criteria:
            assert c.category in categories

    def test_criteria_ids_are_unique(self):
        _, criteria = load_criteria_config()
        ids = [c.id for c in criteria]
        assert len(ids) == len(set(ids))
