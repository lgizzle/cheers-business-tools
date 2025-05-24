"""
Scenario management module for the multi-product calculator.
Provides functions for loading, saving, and managing scenarios.
"""

import os
import json
import logging
from validator import validate_product, validate_calculator_params, ValidationError

# Set up logging
logger = logging.getLogger(__name__)

class ScenarioError(Exception):
    """Custom exception for scenario management errors."""
    pass

class ScenarioManager:
    """Manages the saving, loading, and validation of calculator scenarios."""

    def __init__(self, scenarios_dir="scenarios"):
        """
        Initialize the scenario manager.

        Parameters:
        - scenarios_dir: Directory to store scenario files
        """
        self.scenarios_dir = scenarios_dir
        self._ensure_scenarios_dir()

    def _ensure_scenarios_dir(self):
        """Ensure the scenarios directory exists."""
        if not os.path.exists(self.scenarios_dir):
            os.makedirs(self.scenarios_dir)
            logger.info(f"Created scenarios directory: {self.scenarios_dir}")

    def list_scenarios(self):
        """
        List all available scenarios.

        Returns: List of scenario names
        """
        self._ensure_scenarios_dir()
        scenarios = []

        for filename in os.listdir(self.scenarios_dir):
            if filename.endswith(".json"):
                scenario_name = filename[:-5]  # Remove .json extension
                scenarios.append(scenario_name)

        return scenarios

    def load_scenario(self, scenario_name):
        """
        Load a scenario from file.

        Parameters:
        - scenario_name: Name of the scenario to load

        Returns: Dictionary with scenario data
        Raises ScenarioError if scenario not found or invalid
        """
        # Ensure valid scenario name
        if not scenario_name or not isinstance(scenario_name, str):
            raise ScenarioError("Invalid scenario name")

        # Sanitize scenario name to prevent directory traversal
        scenario_name = os.path.basename(scenario_name)

        # Construct path to scenario file
        file_path = os.path.join(self.scenarios_dir, f"{scenario_name}.json")

        # Check if file exists
        if not os.path.exists(file_path):
            raise ScenarioError(f"Scenario '{scenario_name}' not found")

        try:
            # Load scenario from file
            with open(file_path, 'r') as f:
                scenario_data = json.load(f)

            # Validate scenario data
            self._validate_scenario(scenario_data)

            return scenario_data

        except json.JSONDecodeError as e:
            raise ScenarioError(f"Invalid JSON in scenario file: {e}")

        except ValidationError as e:
            raise ScenarioError(f"Invalid scenario data: {e}")

        except Exception as e:
            raise ScenarioError(f"Error loading scenario: {e}")

    def save_scenario(self, scenario_name, scenario_data):
        """
        Save a scenario to file.

        Parameters:
        - scenario_name: Name of the scenario
        - scenario_data: Dictionary with scenario data

        Raises ScenarioError if scenario name invalid or data invalid
        """
        # Ensure valid scenario name
        if not scenario_name or not isinstance(scenario_name, str):
            raise ScenarioError("Invalid scenario name")

        # Sanitize scenario name to prevent directory traversal
        scenario_name = os.path.basename(scenario_name)

        # Validate scenario data
        try:
            self._validate_scenario(scenario_data)
        except ValidationError as e:
            raise ScenarioError(f"Invalid scenario data: {e}")

        # Ensure scenarios directory exists
        self._ensure_scenarios_dir()

        # Construct path to scenario file
        file_path = os.path.join(self.scenarios_dir, f"{scenario_name}.json")

        try:
            # Convert numpy types to native Python types for JSON serialization
            sanitized_data = self._sanitize_for_json(scenario_data)

            # Save scenario to file
            with open(file_path, 'w') as f:
                json.dump(sanitized_data, f, indent=2)

            logger.info(f"Saved scenario '{scenario_name}'")

            return True

        except Exception as e:
            raise ScenarioError(f"Error saving scenario: {e}")

    def delete_scenario(self, scenario_name):
        """
        Delete a scenario.

        Parameters:
        - scenario_name: Name of the scenario to delete

        Returns: True if deleted, False if not found
        Raises ScenarioError if error occurs
        """
        # Ensure valid scenario name
        if not scenario_name or not isinstance(scenario_name, str):
            raise ScenarioError("Invalid scenario name")

        # Sanitize scenario name to prevent directory traversal
        scenario_name = os.path.basename(scenario_name)

        # Construct path to scenario file
        file_path = os.path.join(self.scenarios_dir, f"{scenario_name}.json")

        # Check if file exists
        if not os.path.exists(file_path):
            return False

        try:
            # Delete the file
            os.remove(file_path)
            logger.info(f"Deleted scenario '{scenario_name}'")
            return True

        except Exception as e:
            raise ScenarioError(f"Error deleting scenario: {e}")

    def _validate_scenario(self, scenario_data):
        """
        Validate scenario data.

        Parameters:
        - scenario_data: Dictionary with scenario data

        Raises ValidationError if data is invalid
        """
        # Check if scenario data is a dictionary
        if not isinstance(scenario_data, dict):
            raise ValidationError("Scenario data must be a dictionary")

        # Check required fields
        required_fields = ["params", "products"]
        for field in required_fields:
            if field not in scenario_data:
                raise ValidationError(f"Missing required field: {field}")

        # Validate parameters
        params = scenario_data["params"]
        validate_calculator_params(params)

        # Validate products
        products = scenario_data["products"]
        if not isinstance(products, list):
            raise ValidationError("Products must be a list")

        if not products:
            raise ValidationError("At least one product is required")

        # Validate each product
        for i, product in enumerate(products):
            try:
                validate_product(product)
            except ValidationError as e:
                raise ValidationError(f"Invalid product at index {i}: {e}")

    def _sanitize_for_json(self, data):
        """
        Sanitize data for JSON serialization.

        Parameters:
        - data: Data to sanitize

        Returns: Sanitized data
        """
        if isinstance(data, dict):
            return {k: self._sanitize_for_json(v) for k, v in data.items()}

        elif isinstance(data, list):
            return [self._sanitize_for_json(item) for item in data]

        elif hasattr(data, 'item'):  # numpy types have .item() method
            try:
                return data.item()
            except:
                return data

        elif isinstance(data, (int, float, str, bool, type(None))):
            return data

        else:
            return str(data)  # Convert any other types to string
