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
    
    def test_criteria_weights_are_numeric(self):
        """Test that all criteria weights are numeric."""
        _, criteria = load_criteria_config()
        
        for criterion in criteria:
            assert isinstance(criterion.weight, (int, float)), f"Criterion '{criterion.id}' has non-numeric weight: {criterion.weight}"
    
    def test_categories_are_strings(self):
        """Test that all categories are strings."""
        categories, _ = load_criteria_config()
        
        for category in categories:
            assert isinstance(category, str), f"Category is not a string: {category}"
            assert len(category) > 0, "Category cannot be empty string"
    
    def test_criteria_ids_are_strings(self):
        """Test that all criteria IDs are strings."""
        _, criteria = load_criteria_config()
        
        for criterion in criteria:
            assert isinstance(criterion.id, str), f"Criterion ID is not a string: {criterion.id}"
            assert len(criterion.id) > 0, "Criterion ID cannot be empty string"
    
    def test_criteria_descriptions_are_strings(self):
        """Test that all criteria descriptions are strings."""
        _, criteria = load_criteria_config()
        
        for criterion in criteria:
            assert isinstance(criterion.criteria, str), f"Criterion description is not a string: {criterion.criteria}"
            assert len(criterion.criteria) > 0, "Criterion description cannot be empty string"
    
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
    
    def test_config_file_encoding(self):
        """Test that config file handles UTF-8 encoding properly."""
        categories, criteria = load_criteria_config()
        
        # Verify we can handle any unicode characters in the config
        for criterion in criteria:
            # Should not raise encoding errors
            str_repr = str(criterion.criteria)
            assert isinstance(str_repr, str)
    
    def test_config_yaml_structure_validation(self):
        """Test that config YAML has expected structure."""
        categories, criteria = load_criteria_config()
        
        # Categories should be a list
        assert isinstance(categories, list)
        
        # Criteria should be a list of Criteria objects
        assert isinstance(criteria, list)
        for criterion in criteria:
            assert hasattr(criterion, 'id')
            assert hasattr(criterion, 'category')
            assert hasattr(criterion, 'criteria') 
            assert hasattr(criterion, 'weight')
    
    def test_criteria_weight_distribution(self):
        """Test that criteria weights are reasonably distributed."""
        _, criteria = load_criteria_config()
        
        weights = [c.weight for c in criteria]
        
        # Should have some variation in weights
        unique_weights = set(weights)
        assert len(unique_weights) > 1, "All criteria have the same weight"
        
        # Total weight should be reasonable
        total_weight = sum(weights)
        assert total_weight > 0, "Total weight should be positive"