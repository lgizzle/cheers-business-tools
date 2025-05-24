"""
Multi-Product Buying Calculator.
Analyzes the ROI of purchasing multiple related products at bulk discount pricing.
"""

import os
import json
import logging
import calculator
import validator
from allocation import get_allocation_strategy
from scenario_manager import ScenarioManager, ScenarioError
from exporter import MultiProductExporter, ExportError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/calculator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MultiProductCalculator:
    """
    Multi-Product Buying Calculator.
    Analyzes the ROI of purchasing multiple related products at bulk discount pricing.
    """

    def __init__(self):
        """Initialize the calculator with default parameters."""
        # Create component instances
        self.scenario_manager = ScenarioManager()
        self.exporter = MultiProductExporter()

        # Default parameters
        self.params = {
            "small_deal_minimum": 30,
            "bulk_deal_minimum": 60,
            "payment_terms": 30,
            "daily_interest_rate": 0.08 / 365  # 8% annual interest rate
        }

        # Initialize products list
        self.products = []

        # Initialize results
        self.results = None

    def set_params(self, params):
        """
        Set calculator parameters.

        Parameters:
        - params: Dictionary with parameter values

        Returns: Self for method chaining
        Raises: ValueError if params are invalid
        """
        try:
            # Validate parameters
            validated_params = validator.validate_calculator_params(params)

            # Update parameters
            self.params.update(validated_params)

            return self

        except validator.ValidationError as e:
            logger.error(f"Invalid parameters: {e}")
            raise ValueError(f"Invalid parameters: {e}")

    def add_product(self, product):
        """
        Add a product to the calculator.

        Parameters:
        - product: Dictionary with product data

        Returns: Self for method chaining
        Raises: ValueError if product is invalid
        """
        try:
            # Validate product
            validated_product = validator.validate_product(product)

            # Add product to list
            self.products.append(validated_product)

            return self

        except validator.ValidationError as e:
            logger.error(f"Invalid product: {e}")
            raise ValueError(f"Invalid product: {e}")

    def set_products(self, products):
        """
        Set multiple products at once.

        Parameters:
        - products: List of product dictionaries

        Returns: Self for method chaining
        Raises: ValueError if any product is invalid
        """
        try:
            # Clear existing products
            self.products = []

            # Add each product
            for product in products:
                self.add_product(product)

            return self

        except ValueError as e:
            logger.error(f"Error setting products: {e}")
            raise ValueError(f"Error setting products: {e}")

    def suggest_quantities(self, allocation_mode="proportional", min_days_stock=None):
        """
        Suggest bulk quantities for products based on the specified allocation mode.

        Parameters:
        - allocation_mode: Strategy for allocating quantities ('proportional', 'roi', 'minimum')
        - min_days_stock: Minimum days of stock required (optional)

        Returns: List of products with bulk_quantity values set
        Raises: ValueError if inputs are invalid
        """
        try:
            # Validate inputs
            if not self.products:
                raise ValueError("No products available")

            # Create allocation parameters
            allocation_params = {
                "bulk_deal_minimum": self.params["bulk_deal_minimum"],
                "payment_terms": self.params["payment_terms"]
            }

            # Add minimum days of stock if specified
            if min_days_stock is not None:
                allocation_params["min_days_stock"] = validator.validate_numeric(
                    min_days_stock, "Minimum days stock", min_value=0
                )

            # Get the appropriate allocation strategy
            strategy = get_allocation_strategy(allocation_mode)

            # Allocate quantities
            allocated_products = strategy.allocate(self.products, allocation_params)

            # Update products with allocated quantities
            for i, product in enumerate(self.products):
                product_name = product["product_name"]
                allocated = next(p for p in allocated_products if p["product_name"] == product_name)
                self.products[i]["bulk_quantity"] = allocated["bulk_quantity"]

            return self.products

        except Exception as e:
            logger.error(f"Error suggesting quantities: {e}")
            raise ValueError(f"Error suggesting quantities: {e}")

    def calculate(self):
        """
        Calculate all metrics for the current products and parameters.

        Returns: Dictionary with calculation results
        Raises: ValueError if calculation fails
        """
        try:
            # Validate inputs
            if not self.products:
                raise ValueError("No products available")

            # Validate bulk quantities
            validator.validate_bulk_quantities(
                self.products, self.params["bulk_deal_minimum"]
            )

            # Calculate metrics using the calculator module
            self.results = calculator.compute_scenario_metrics(self.products, self.params)

            return self.results

        except Exception as e:
            logger.error(f"Error calculating results: {e}")
            raise ValueError(f"Error calculating results: {e}")

    def save_scenario(self, scenario_name):
        """
        Save the current scenario.

        Parameters:
        - scenario_name: Name of the scenario

        Returns: True if saved successfully
        Raises: ValueError if save fails
        """
        try:
            # Create scenario data
            scenario_data = {
                "params": self.params,
                "products": self.products
            }

            # Save the scenario
            self.scenario_manager.save_scenario(scenario_name, scenario_data)

            logger.info(f"Saved scenario: {scenario_name}")
            return True

        except ScenarioError as e:
            logger.error(f"Error saving scenario: {e}")
            raise ValueError(f"Error saving scenario: {e}")

    def load_scenario(self, scenario_name):
        """
        Load a scenario.

        Parameters:
        - scenario_name: Name of the scenario to load

        Returns: Self for method chaining
        Raises: ValueError if load fails
        """
        try:
            # Load the scenario
            scenario_data = self.scenario_manager.load_scenario(scenario_name)

            # Update calculator with scenario data
            self.params = scenario_data["params"]
            self.products = scenario_data["products"]

            logger.info(f"Loaded scenario: {scenario_name}")
            return self

        except ScenarioError as e:
            logger.error(f"Error loading scenario: {e}")
            raise ValueError(f"Error loading scenario: {e}")

    def list_scenarios(self):
        """
        List available scenarios.

        Returns: List of scenario names
        """
        return self.scenario_manager.list_scenarios()

    def delete_scenario(self, scenario_name):
        """
        Delete a scenario.

        Parameters:
        - scenario_name: Name of the scenario to delete

        Returns: True if deleted, False if not found
        Raises: ValueError if delete fails
        """
        try:
            # Delete the scenario
            result = self.scenario_manager.delete_scenario(scenario_name)

            if result:
                logger.info(f"Deleted scenario: {scenario_name}")
            else:
                logger.warning(f"Scenario not found: {scenario_name}")

            return result

        except ScenarioError as e:
            logger.error(f"Error deleting scenario: {e}")
            raise ValueError(f"Error deleting scenario: {e}")

    def export_to_excel(self, scenario_name):
        """
        Export the calculated results to Excel.

        Parameters:
        - scenario_name: Name for the exported file

        Returns: Path to the output file
        Raises: ValueError if export fails
        """
        try:
            # Ensure results are available
            if not self.results:
                self.calculate()

            # Create scenario data
            scenario_data = {
                "params": self.params,
                "products": self.products
            }

            # Export to Excel
            file_path = self.exporter.export_to_excel(scenario_name, scenario_data, self.results)

            logger.info(f"Exported to Excel: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            raise ValueError(f"Error exporting to Excel: {e}")

    def export_debug_info(self, scenario_name):
        """
        Export debug information to JSON.

        Parameters:
        - scenario_name: Name for the exported file

        Returns: Path to the output file
        Raises: ValueError if export fails
        """
        try:
            # Ensure results are available
            if not self.results:
                self.calculate()

            # Create scenario data
            scenario_data = {
                "params": self.params,
                "products": self.products
            }

            # Export debug info
            file_path = self.exporter.export_debug_info(scenario_name, scenario_data, self.results)

            logger.info(f"Exported debug info: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Error exporting debug info: {e}")
            raise ValueError(f"Error exporting debug info: {e}")

# Ensure log directory exists
os.makedirs("logs", exist_ok=True)
