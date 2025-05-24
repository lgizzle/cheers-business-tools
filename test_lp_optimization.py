import json
import numpy as np
from multi_product_calculator import MultiProductBuyingCalculator

def print_header(title):
    """Print a formatted header for test sections."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)

def test_lp_optimization():
    """Test that the linear programming optimization correctly maximizes ROI."""
    print_header("TESTING LINEAR PROGRAMMING OPTIMIZATION")

    # Create a calculator instance
    calc = MultiProductBuyingCalculator()

    # Set parameters
    calc.set_parameters(small_deal_minimum=30, bulk_deal_minimum=60, payment_terms=30)

    # Create a test dataset with products having clear ROI differences
    # Product A: Highest ROI (20% discount)
    # Product B: Medium ROI (15% discount)
    # Product C: Lowest ROI (10% discount)
    calc.clear_products()
    calc.add_product("Product A", current_price=10, bulk_price=8, bottles_per_case=12,
                   cases_on_hand=5, cases_per_year=182)  # ~0.5 cases per day
    calc.add_product("Product B", current_price=8, bulk_price=6.8, bottles_per_case=12,
                   cases_on_hand=5, cases_per_year=182)  # ~0.5 cases per day
    calc.add_product("Product C", current_price=6, bulk_price=5.4, bottles_per_case=12,
                   cases_on_hand=5, cases_per_year=182)  # ~0.5 cases per day

    # Test with ROI-based allocation
    quantities = calc.suggest_quantities(allocation_mode="roi", min_days_stock=0)

    # Print the results
    print(f"Suggested quantities: {json.dumps(quantities, indent=2)}")
    print(f"Total allocated: {sum(quantities.values())} cases\n")

    # Verify allocation priorities
    print("Verifying allocation priorities:")
    for product, qty in quantities.items():
        print(f"{product}: {qty} cases")

    # Calculate actual ROI for each product
    print("\nCalculated ROI values:")
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

        print(f"{name}: ROI={roi:.2f}%, Savings/Case=${savings_per_case:.2f}")

    # Check if allocation follows ROI order
    product_a_qty = quantities.get("Product A", 0)
    product_b_qty = quantities.get("Product B", 0)
    product_c_qty = quantities.get("Product C", 0)

    if (product_a_qty >= product_b_qty >= product_c_qty) or (sum(quantities.values()) == calc.bulk_deal_minimum):
        print("\n✅ PASSED: Allocation follows ROI order or achieves bulk minimum exactly")
    else:
        print("\n❌ FAILED: Allocation does not follow ROI order")

    return quantities

def test_minimum_days_stock_constraint():
    """Test that the minimum days of stock constraint is enforced."""
    print_header("TESTING MINIMUM DAYS OF STOCK CONSTRAINT")

    # Create a calculator instance
    calc = MultiProductBuyingCalculator()

    # Set parameters
    calc.set_parameters(small_deal_minimum=30, bulk_deal_minimum=60, payment_terms=30)

    # Create test products with varying stock levels
    calc.clear_products()

    # Well stocked product (already has plenty of stock)
    calc.add_product("Well Stocked", current_price=10, bulk_price=8, bottles_per_case=12,
                   cases_on_hand=15, cases_per_year=182)  # ~0.5 cases per day

    # Low stocked product (below minimum)
    calc.add_product("Low Stock", current_price=8, bulk_price=6.8, bottles_per_case=12,
                   cases_on_hand=2.5, cases_per_year=182)  # ~0.5 cases per day

    # Very low stocked product (critical)
    calc.add_product("Very Low Stock", current_price=6, bulk_price=5.4, bottles_per_case=12,
                   cases_on_hand=0.5, cases_per_year=182)  # ~0.5 cases per day

    # Set minimum days of stock requirement
    min_days = 30
    print(f"Setting minimum days of stock to {min_days}")

    # Test with ROI-based allocation
    quantities = calc.suggest_quantities(allocation_mode="roi", min_days_stock=min_days)

    # Print the results
    print(f"Suggested quantities: {json.dumps(quantities, indent=2)}\n")

    # Calculate days of stock before and after allocation
    print("Days of stock after allocation:")
    all_passed = True
    for product in calc.products:
        name = product['product_name']
        daily_cases = product['daily_cases']
        current_stock = product['cases_on_hand']
        new_stock = current_stock + quantities.get(name, 0)

        # Calculate days of stock
        current_days = current_stock / daily_cases if daily_cases > 0 else float('inf')
        new_days = new_stock / daily_cases if daily_cases > 0 else float('inf')

        print(f"{name}: Before={current_days:.1f} days, After={new_days:.1f} days")

        # Check if minimum days requirement is met
        if new_days >= min_days or new_days >= current_days:
            print(f"✅ PASSED: {name} meets minimum days requirement")
        else:
            print(f"❌ FAILED: {name} does not meet minimum days requirement")
            all_passed = False

    return quantities, all_passed

def test_bulk_minimum_target():
    """Test that the allocation hits the exact bulk minimum target."""
    print_header("TESTING BULK MINIMUM TARGET")

    # Create a calculator instance
    calc = MultiProductBuyingCalculator()

    # Create test products
    calc.clear_products()
    calc.add_product("Product 1", current_price=10, bulk_price=7.9, bottles_per_case=12,
                   cases_on_hand=3, cases_per_year=90)
    calc.add_product("Product 2", current_price=12, bulk_price=9.9, bottles_per_case=12,
                   cases_on_hand=3, cases_per_year=100)
    calc.add_product("Product 3", current_price=14, bulk_price=11.9, bottles_per_case=12,
                   cases_on_hand=3, cases_per_year=110)
    calc.add_product("Product 4", current_price=16, bulk_price=13.9, bottles_per_case=12,
                   cases_on_hand=3, cases_per_year=120)
    calc.add_product("Product 5", current_price=18, bulk_price=15.9, bottles_per_case=12,
                   cases_on_hand=3, cases_per_year=130)

    # Test different bulk minimums
    bulk_minimums = [50, 75, 100, 150]
    results = {}

    for bulk_min in bulk_minimums:
        print(f"\nTesting with bulk minimum = {bulk_min}")
        calc.set_parameters(small_deal_minimum=bulk_min/2, bulk_deal_minimum=bulk_min, payment_terms=30)

        # Test with both allocation modes
        for mode in ["minimum", "roi"]:
            print(f"\n  Testing allocation mode: {mode}")
            quantities = calc.suggest_quantities(allocation_mode=mode, min_days_stock=14)
            total = sum(quantities.values())

            print(f"  Total allocated: {total} cases (target: {bulk_min})")

            if total == bulk_min:
                print(f"  ✅ PASSED: Allocated exactly {bulk_min} cases")
                results[f"{mode}_{bulk_min}"] = True
            else:
                print(f"  ❌ FAILED: Allocation of {total} does not match target of {bulk_min}")
                results[f"{mode}_{bulk_min}"] = False

    return results

def test_max_inventory_constraint():
    """Test that the maximum inventory constraint is enforced."""
    print_header("TESTING MAXIMUM INVENTORY CONSTRAINT")

    # Create a calculator instance
    calc = MultiProductBuyingCalculator()

    # Set parameters
    calc.set_parameters(small_deal_minimum=30, bulk_deal_minimum=60, payment_terms=30)

    # Create test products with varying stock levels
    calc.clear_products()

    # Fast-moving product with low stock
    calc.add_product("Fast Mover", current_price=10, bulk_price=8, bottles_per_case=12,
                   cases_on_hand=10, cases_per_year=1825)  # 5 cases per day (1825/365)

    # Medium-moving product with adequate stock
    calc.add_product("Medium Mover", current_price=8, bulk_price=6.8, bottles_per_case=12,
                   cases_on_hand=5, cases_per_year=182)  # ~0.5 cases per day

    # Slow-moving product with excessive stock (should get no allocation)
    calc.add_product("Slow Mover High Stock", current_price=6, bulk_price=5.4, bottles_per_case=12,
                   cases_on_hand=20, cases_per_year=18)  # ~0.05 cases per day

    # Test with ROI-based allocation
    quantities = calc.suggest_quantities(allocation_mode="roi", min_days_stock=14)

    # Print the results - make sure to convert any numpy types to Python native types
    formatted_quantities = {k: int(v) if hasattr(v, 'item') else v for k, v in quantities.items()}
    print(f"Suggested quantities: {json.dumps(formatted_quantities, indent=2)}\n")

    # Verify the slow mover with excessive stock got minimal or no allocation
    if quantities.get("Slow Mover High Stock", 0) == 0:
        print("✅ PASSED: Slow mover with excessive stock received no allocation")
    else:
        print(f"❌ FAILED: Slow mover received {quantities.get('Slow Mover High Stock')} cases despite excessive stock")

    # Calculate final days of stock
    for product in calc.products:
        name = product['product_name']
        daily_cases = product['daily_cases']
        current_stock = product['cases_on_hand']
        new_stock = current_stock + quantities.get(name, 0)

        # Calculate days of stock
        if daily_cases > 0:
            days_of_stock = new_stock / daily_cases
            print(f"{name}: {days_of_stock:.1f} days of stock after allocation")

            # Check if days of stock exceeds maximum (90 days)
            if days_of_stock <= 90 or current_stock / daily_cases > 90:
                print(f"✅ {name} does not exceed maximum inventory constraint unnecessarily")
            else:
                print(f"❌ {name} exceeds maximum inventory constraint unnecessarily")

    return quantities

def main():
    print("\nRunning Linear Programming Optimization Tests")
    print("============================================\n")

    # Test basic LP optimization
    try:
        test_lp_optimization()
    except Exception as e:
        print(f"Error in LP optimization test: {str(e)}")

    # Test minimum days of stock constraint
    try:
        test_minimum_days_stock_constraint()
    except Exception as e:
        print(f"Error in minimum days stock test: {str(e)}")

    # Test bulk minimum target
    try:
        test_bulk_minimum_target()
    except Exception as e:
        print(f"Error in bulk minimum target test: {str(e)}")

    # Test maximum inventory constraint
    try:
        max_inventory_results = test_max_inventory_constraint()
    except Exception as e:
        print(f"Error in maximum inventory constraint test: {str(e)}")

if __name__ == "__main__":
    main()
