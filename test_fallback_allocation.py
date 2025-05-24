import json
import numpy as np
from multi_product_calculator import MultiProductBuyingCalculator

def print_header(title):
    """Print a formatted header for test sections."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)

def test_fallback_allocation():
    """Test the fallback allocation method that's used when linear programming fails."""
    print_header("TESTING FALLBACK ALLOCATION")

    # Create a calculator instance
    calc = MultiProductBuyingCalculator()

    # Set parameters - use a high bulk minimum to force fallback
    calc.set_parameters(small_deal_minimum=75, bulk_deal_minimum=150, payment_terms=30)

    # Create test products with constrained inventory limits
    calc.clear_products()
    calc.add_product("Product 1", current_price=10, bulk_price=7.5, bottles_per_case=12,
                   cases_on_hand=3, cases_per_year=90)   # Max additional ~20 cases to stay under 90 days
    calc.add_product("Product 2", current_price=12, bulk_price=9, bottles_per_case=12,
                   cases_on_hand=3, cases_per_year=100)  # Max additional ~22 cases to stay under 90 days
    calc.add_product("Product 3", current_price=14, bulk_price=10.5, bottles_per_case=12,
                   cases_on_hand=3, cases_per_year=110)  # Max additional ~25 cases to stay under 90 days
    calc.add_product("Product 4", current_price=16, bulk_price=12, bottles_per_case=12,
                   cases_on_hand=3, cases_per_year=120)  # Max additional ~27 cases to stay under 90 days
    calc.add_product("Product 5", current_price=18, bulk_price=13.5, bottles_per_case=12,
                   cases_on_hand=3, cases_per_year=130)  # Max additional ~30 cases to stay under 90 days

    # Test with ROI-based allocation with a target that can't be fully satisfied
    quantities = calc.suggest_quantities(allocation_mode="roi", min_days_stock=14)

    # Print the results
    formatted_quantities = {k: int(v) if hasattr(v, 'item') else v for k, v in quantities.items()}
    print(f"Suggested quantities: {json.dumps(formatted_quantities, indent=2)}")
    print(f"Total allocated: {sum(quantities.values())} cases (target: {calc.bulk_deal_minimum})")

    # Verify that allocation follows ROI order
    # First, calculate ROI for each product
    roi_values = {}
    for product in calc.products:
        name = product['product_name']
        cp = product['current_price']
        bp = product['bulk_price']
        bottles = product['bottles_per_case']
        savings_per_case = (cp - bp) * bottles
        price_per_case = bp * bottles
        daily_interest = 0.08 / 365
        holding_cost = price_per_case * daily_interest * calc.payment_terms
        roi = (savings_per_case - holding_cost) / price_per_case * 100  # as percentage
        roi_values[name] = roi
        print(f"{name}: ROI={roi:.2f}%, Allocation={quantities.get(name, 0)} cases")

    # Sort products by ROI
    sorted_products = sorted(roi_values.items(), key=lambda x: x[1], reverse=True)

    # Check if higher ROI products got higher or equal allocation compared to lower ROI products
    allocation_follows_roi = True
    for i in range(len(sorted_products)-1):
        higher_roi_product = sorted_products[i][0]
        lower_roi_product = sorted_products[i+1][0]
        if quantities.get(higher_roi_product, 0) < quantities.get(lower_roi_product, 0):
            allocation_follows_roi = False
            print(f"❌ ROI order violation: {higher_roi_product} (ROI={sorted_products[i][1]:.2f}%) got fewer cases than {lower_roi_product} (ROI={sorted_products[i+1][1]:.2f}%)")

    if allocation_follows_roi:
        print("✅ PASSED: Allocation follows ROI order")
    else:
        print("❌ FAILED: Allocation does not strictly follow ROI order")

    # Check if minimum stock requirements are met
    min_days = 14
    all_min_days_met = True
    print(f"\nVerifying minimum days of stock requirement ({min_days} days):")
    for product in calc.products:
        name = product['product_name']
        daily_cases = product['daily_cases']
        current_stock = product['cases_on_hand']
        new_stock = current_stock + quantities.get(name, 0)

        # Calculate days of stock
        if daily_cases > 0:
            current_days = current_stock / daily_cases
            new_days = new_stock / daily_cases
            print(f"{name}: Before={current_days:.1f} days, After={new_days:.1f} days")

            if new_days < min_days:
                all_min_days_met = False
                print(f"❌ {name} does not meet minimum days requirement")
            else:
                print(f"✅ {name} meets minimum days requirement")

    if all_min_days_met:
        print("\n✅ PASSED: All products meet minimum days requirement")
    else:
        print("\n❌ FAILED: Not all products meet minimum days requirement")

    # Check if any product exceeds maximum inventory
    all_within_max = True
    max_days = 90
    print(f"\nVerifying maximum inventory constraint ({max_days} days):")
    for product in calc.products:
        name = product['product_name']
        daily_cases = product['daily_cases']
        current_stock = product['cases_on_hand']
        new_stock = current_stock + quantities.get(name, 0)

        # Calculate days of stock
        if daily_cases > 0:
            new_days = new_stock / daily_cases
            print(f"{name}: {new_days:.1f} days of stock after allocation")

            if new_days > max_days:
                all_within_max = False
                print(f"❌ {name} exceeds maximum inventory constraint")
            else:
                print(f"✅ {name} within maximum inventory constraint")

    if all_within_max:
        print("\n✅ PASSED: All products are within maximum inventory constraint")
    else:
        print("\n❌ FAILED: Some products exceed maximum inventory constraint")

    return quantities, roi_values

def main():
    """Run the fallback allocation test."""
    print("\nRunning Fallback Allocation Tests")
    print("================================\n")

    try:
        test_fallback_allocation()
    except Exception as e:
        print(f"Error in fallback allocation test: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
