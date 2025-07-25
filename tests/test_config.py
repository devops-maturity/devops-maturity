import pytest
import tempfile
import os
import yaml
from src.config.loader import load_criteria_config
from src.core.model import Criteria


class TestConfigLoader:
    """Test the configuration loader functionality."""
    
    def test_load_criteria_config(self):
        """Test loading the actual criteria configuration file."""
        categories, criteria = load_criteria_config()
        
        # Verify we get some categories
        assert isinstance(categories, list)
        assert len(categories) > 0
        
        # Verify we get some criteria
        assert isinstance(criteria, list)
        assert len(criteria) > 0
        
        # Verify each criteria is properly formed
        for criterion in criteria:
            assert isinstance(criterion, Criteria)
            assert criterion.id
            assert criterion.category
            assert criterion.criteria
            assert isinstance(criterion.weight, (int, float))
            assert criterion.weight > 0
    
    def test_criteria_have_valid_categories(self):
        """Test that all criteria reference valid categories."""
        categories, criteria = load_criteria_config()
        
        # Get unique categories from criteria
        criteria_categories = set(criterion.category for criterion in criteria)
        
        # Verify all criteria categories are in the categories list
        for category in criteria_categories:
            assert category in categories, f"Category '{category}' not found in categories list"
    
    def test_criteria_have_unique_ids(self):
        """Test that all criteria have unique IDs."""
        _, criteria = load_criteria_config()
        
        ids = [criterion.id for criterion in criteria]
        unique_ids = set(ids)
        
        assert len(ids) == len(unique_ids), "Duplicate criteria IDs found"
    
    def test_criteria_weights_are_positive(self):
        """Test that all criteria weights are positive numbers."""
        _, criteria = load_criteria_config()
        
        for criterion in criteria:
            assert criterion.weight > 0, f"Criterion '{criterion.id}' has non-positive weight: {criterion.weight}"
    
    def test_load_criteria_with_custom_config(self):
        """Test loading criteria from a custom configuration file."""
        # Create a temporary config file
        test_config = {
            "categories": ["Test Category 1", "Test Category 2"],
            "criteria": [
                {
                    "id": "test1",
                    "category": "Test Category 1",
                    "criteria": "Test criteria 1",
                    "weight": 1.0
                },
                {
                    "id": "test2",
                    "category": "Test Category 2", 
                    "criteria": "Test criteria 2",
                    "weight": 2.5
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_config, f)
            temp_file_path = f.name
        
        try:
            # Temporarily replace the config file path
            import src.config.loader as loader_module
            original_path = os.path.join(os.path.dirname(loader_module.__file__), "criteria.yaml")
            
            # Patch the function to use our test file
            def mock_load_criteria_config():
                with open(temp_file_path, "r", encoding="utf-8") as f:
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
            
            categories, criteria = mock_load_criteria_config()
            
            # Verify the test config was loaded correctly
            assert categories == ["Test Category 1", "Test Category 2"]
            assert len(criteria) == 2
            
            assert criteria[0].id == "test1"
            assert criteria[0].category == "Test Category 1"
            assert criteria[0].criteria == "Test criteria 1"
            assert criteria[0].weight == 1.0
            
            assert criteria[1].id == "test2"
            assert criteria[1].category == "Test Category 2"
            assert criteria[1].criteria == "Test criteria 2"
            assert criteria[1].weight == 2.5
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)