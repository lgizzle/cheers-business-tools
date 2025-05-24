import sys
import os
import json
import numpy as np
from multi_product_calculator import MultiProductBuyingCalculator

def print_header(title):
    """Print a formatted header for test sections."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)

def test_allocation_modes():
    """Test different allocation modes with the same product set."""
    print_header("TESTING DIFFERENT ALLOCATION MODES")

    # Create a calculator instance
    calc = MultiProductBuyingCalculator()

    # Set parameters
    calc.set_parameters(small_deal_minimum=30, bulk_deal_minimum=60, payment_terms=30)

    # Create a standard test dataset with realistic values
    calc.clear_products()
    calc.add_product("Jack Daniels 750ml", current_price=25.00, bulk_price=22.50,
                     cases_on_hand=10, cases_per_year=120, bottles_per_case=12)
    calc.add_product("Jack Daniels 1.75L", current_price=40.00, bulk_price=36.50,
                     cases_on_hand=5, cases_per_year=80, bottles_per_case=6)
    calc.add_product("Jack Daniels Honey 750ml", current_price=27.00, bulk_price=24.50,
                     cases_on_hand=8, cases_per_year=90, bottles_per_case=12)
    calc.add_product("Gentleman Jack 750ml", current_price=40.00, bulk_price=36.00,
                     cases_on_hand=3, cases_per_year=40, bottles_per_case=12)
    calc.add_product("Jack Daniels 375ml", current_price=18.00, bulk_price=16.00,
                     cases_on_hand=6, cases_per_year=60, bottles_per_case=24)

    # Test "minimum" mode (efficiency-based)
    print("\nTesting 'minimum' allocation mode:")
    quantities = calc.suggest_quantities(allocation_mode="minimum")
    print(f"Suggested quantities (minimum mode): {json.dumps(quantities, indent=2)}")
    print(f"Total allocated: {sum(quantities.values())} cases")

    # Set the suggested quantities
    for product in calc.products:
        product["bulk_quantity"] = quantities[product["product_name"]]

    # Calculate and print results
    results = calc.calculate()
    print(f"Total savings: ${results['summary']['total_savings']:.2f}")
    print(f"ROI: {results['summary']['roi']:.2%}")

    # Test "maintain" mode
    print("\nTesting 'maintain' allocation mode:")
    quantities = calc.suggest_quantities(allocation_mode="maintain")
    print(f"Suggested quantities (maintain mode): {json.dumps(quantities, indent=2)}")
    print(f"Total allocated: {sum(quantities.values())} cases")

    # Set the suggested quantities
    for product in calc.products:
        product["bulk_quantity"] = quantities[product["product_name"]]

    # Calculate and print results
    results = calc.calculate()
    print(f"Total savings: ${results['summary']['total_savings']:.2f}")
    print(f"ROI: {results['summary']['roi']:.2%}")

    # Test "ROI" mode with minimum days stock
    print("\nTesting 'roi' allocation mode with min_days_stock=14:")
    quantities = calc.suggest_quantities(allocation_mode="roi", min_days_stock=14)
    print(f"Suggested quantities (ROI mode): {json.dumps(quantities, indent=2)}")
    print(f"Total allocated: {sum(quantities.values())} cases")

    # Set the suggested quantities
    for product in calc.products:
        product["bulk_quantity"] = quantities[product["product_name"]]

    # Calculate and print results
    results = calc.calculate()
    print(f"Total savings: ${results['summary']['total_savings']:.2f}")
    print(f"ROI: {results['summary']['roi']:.2%}")

    return results

def test_edge_cases():
    """Test edge cases like high inventory or uneven sales distribution."""
    print_header("TESTING EDGE CASES")

    # Create a calculator instance
    calc = MultiProductBuyingCalculator()

    # Set parameters
    calc.set_parameters(small_deal_minimum=30, bulk_deal_minimum=60, payment_terms=30)

    # Test case 1: All products already have high inventory
    print("\nTest case 1: High existing inventory")
    calc.clear_products()
    calc.add_product("Product A", current_price=25.00, bulk_price=22.50,
                     cases_on_hand=60, cases_per_year=120, bottles_per_case=12)
    calc.add_product("Product B", current_price=40.00, bulk_price=36.50,
                     cases_on_hand=50, cases_per_year=80, bottles_per_case=6)
    calc.add_product("Product C", current_price=27.00, bulk_price=24.50,
                     cases_on_hand=45, cases_per_year=90, bottles_per_case=12)

    quantities = calc.suggest_quantities(allocation_mode="roi", min_days_stock=14)
    print(f"Suggested quantities: {json.dumps(quantities, indent=2)}")
    print(f"Total allocated: {sum(quantities.values())} cases")

    # Test case 2: Very uneven sales distribution
    print("\nTest case 2: Uneven sales distribution")
    calc.clear_products()
    calc.add_product("Fast Mover", current_price=25.00, bulk_price=22.50,
                     cases_on_hand=10, cases_per_year=500, bottles_per_case=12)
    calc.add_product("Medium Mover", current_price=40.00, bulk_price=36.50,
                     cases_on_hand=5, cases_per_year=100, bottles_per_case=6)
    calc.add_product("Slow Mover", current_price=27.00, bulk_price=24.50,
                     cases_on_hand=8, cases_per_year=20, bottles_per_case=12)

    quantities = calc.suggest_quantities(allocation_mode="roi", min_days_stock=14)
    print(f"Suggested quantities: {json.dumps(quantities, indent=2)}")
    print(f"Total allocated: {sum(quantities.values())} cases")

    # Test case 3: No sales data for some products
    print("\nTest case 3: Missing sales data")
    calc.clear_products()
    calc.add_product("Product with Sales", current_price=25.00, bulk_price=22.50,
                     cases_on_hand=10, cases_per_year=100, bottles_per_case=12)
    calc.add_product("Product without Sales", current_price=40.00, bulk_price=36.50,
                     cases_on_hand=5, cases_per_year=0, bottles_per_case=6)
    calc.add_product("Another with Sales", current_price=27.00, bulk_price=24.50,
                     cases_on_hand=8, cases_per_year=80, bottles_per_case=12)

    quantities = calc.suggest_quantities(allocation_mode="roi", min_days_stock=14)
    print(f"Suggested quantities: {json.dumps(quantities, indent=2)}")
    print(f"Total allocated: {sum(quantities.values())} cases")

    return quantities

def test_optimization_methods():
    """Test that the linear programming optimization is working correctly."""
    print_header("TESTING OPTIMIZATION METHODS")

    # Create a calculator instance
    calc = MultiProductBuyingCalculator()

    # Set parameters
    calc.set_parameters(small_deal_minimum=30, bulk_deal_minimum=60, payment_terms=30)

    # Create a test dataset with products having different ROI potential
    calc.clear_products()
    calc.add_product("High ROI Product", current_price=50.00, bulk_price=40.00,
                     cases_on_hand=5, cases_per_year=100, bottles_per_case=12)
    calc.add_product("Medium ROI Product", current_price=30.00, bulk_price=25.00,
                     cases_on_hand=8, cases_per_year=120, bottles_per_case=12)
    calc.add_product("Low ROI Product", current_price=20.00, bulk_price=18.00,
                     cases_on_hand=10, cases_per_year=150, bottles_per_case=12)

    # Test ROI mode
    quantities = calc.suggest_quantities(allocation_mode="roi", min_days_stock=14)
    print(f"Suggested quantities: {json.dumps(quantities, indent=2)}")
    print(f"Total allocated: {sum(quantities.values())} cases")

    # Set the suggested quantities
    for product in calc.products:
        product["bulk_quantity"] = quantities[product["product_name"]]

    # Calculate and print results
    results = calc.calculate()
    print(f"Total savings: ${results['summary']['total_savings']:.2f}")
    print(f"ROI: {results['summary']['roi']:.2%}")

    # Verify that the highest ROI product got the most allocation (if constraints allow)
    print("\nVerifying ROI-based allocation priority:")
    for product in results["products"]:
        if "roi" in product and "bulk_quantity" in product:
            print(f"{product['product_name']}: ROI={product['roi']:.2%}, Allocated={product['bulk_quantity']} cases")

    return results

def test_custom_scenario():
    """Test a custom scenario with specific requirements."""
    print_header("TESTING CUSTOM SCENARIO")

    # Create a calculator instance
    calc = MultiProductBuyingCalculator()

    # Set parameters - use a larger bulk minimum for testing
    calc.set_parameters(small_deal_minimum=50, bulk_deal_minimum=100, payment_terms=45)

    # Create a custom test dataset
    calc.clear_products()
    # Add 10 products with varying prices, inventory, and sales rates
    for i in range(1, 11):
        # Vary parameters to create interesting test cases
        current_price = 20.00 + (i * 2)
        bulk_price = current_price * (0.85 + (i % 3) * 0.03)  # 15-21% discount
        cases_on_hand = i * 2 if i % 3 == 0 else i
        cases_per_year = 50 + (i * 15)
        bottles_per_case = 6 if i % 2 == 0 else 12

        calc.add_product(f"Product {i}", current_price=current_price, bulk_price=bulk_price,
                        cases_on_hand=cases_on_hand, cases_per_year=cases_per_year,
                        bottles_per_case=bottles_per_case)

    # Test ROI mode with a high minimum days stock
    quantities = calc.suggest_quantities(allocation_mode="roi", min_days_stock=30)
    print(f"Suggested quantities: {json.dumps(quantities, indent=2)}")
    print(f"Total allocated: {sum(quantities.values())} cases")

    # Set the suggested quantities
    for product in calc.products:
        product["bulk_quantity"] = quantities[product["product_name"]]

    # Calculate and print results
    results = calc.calculate()
    print(f"Total savings: ${results['summary']['total_savings']:.2f}")
    print(f"ROI: {results['summary']['roi']:.2%}")

    # Check days of stock after purchase for each product
    print("\nDays of stock after purchase:")
    for product in results["products"]:
        print(f"{product['product_name']}: {product['days_of_stock_after_deal']:.1f} days")

    return results

def test_serialization():
    """Test serialization to ensure no JSON issues with NumPy types."""
    print_header("TESTING JSON SERIALIZATION")

    # Create a calculator instance and add some products
    calc = MultiProductBuyingCalculator()
    calc.set_parameters(small_deal_minimum=30, bulk_deal_minimum=60, payment_terms=30)

    calc.add_product("Test Product", current_price=25.00, bulk_price=22.50,
                    cases_on_hand=10, cases_per_year=120, bottles_per_case=12,
                    bulk_quantity=20)

    # Get calculation results
    results = calc.calculate()

    # Try to serialize to JSON
    try:
        json_data = json.dumps(results)
        print("JSON serialization successful")
    except TypeError as e:
        print(f"JSON serialization failed: {str(e)}")

    # Also test serializing the suggested quantities
    quantities = calc.suggest_quantities(allocation_mode="roi")
    try:
        json_data = json.dumps(quantities)
        print("Quantities JSON serialization successful")
    except TypeError as e:
        print(f"Quantities JSON serialization failed: {str(e)}")

    return results

def main():
    """Run all tests."""
    print("\nRunning Multi-Product Calculator Tests")
    print("======================================")

    # Run all test functions
    allocation_results = test_allocation_modes()
    edge_case_results = test_edge_cases()
    optimization_results = test_optimization_methods()
    custom_results = test_custom_scenario()
    serialization_results = test_serialization()

    print("\nAll tests completed!")

if __name__ == "__main__":
    main()
