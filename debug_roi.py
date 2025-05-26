#!/usr/bin/env python3
"""
Debug script to understand ROI calculation
"""

from multi_product_calculator import MultiProductBuyingCalculator

def debug_roi_calculation():
    """Debug the ROI calculation to see why it's returning zero"""

    calc = MultiProductBuyingCalculator()

    # Simple test product
    product = {
        'id': 1,
        'name': 'Test Product',
        'current_price': 10.00,
        'bulk_price': 8.00,
        'on_hand': 2,
        'annual_cases': 100,
        'bottles_per_case': 12,
        'bulk_quantity': 10
    }

    params = {
        'dealSizeCases': 30,
        'minDaysStock': 21,
        'paymentTermsDays': 15,
        'smallDealCases': 10
    }

    print("Debug ROI Calculation")
    print("=" * 40)
    print(f"Product: {product['name']}")
    print(f"Price Small: ${product['current_price']:.2f}")
    print(f"Price Bulk: ${product['bulk_price']:.2f}")
    print(f"On Hand: {product['on_hand']} cases")
    print(f"Annual Cases: {product['annual_cases']} cases")
    print(f"Bulk Quantity: {product['bulk_quantity']} cases")
    print(f"Payment Terms: {params['paymentTermsDays']} days")
    print()

    # Manual calculation check
    savings_per_bottle = product['current_price'] - product['bulk_price']
    total_savings_expected = product['bulk_quantity'] * product['bottles_per_case'] * savings_per_bottle
    print(f"Expected Savings Calculation:")
    print(f"  Savings per bottle: ${savings_per_bottle:.2f}")
    print(f"  Total savings: {product['bulk_quantity']} cases × {product['bottles_per_case']} bottles × ${savings_per_bottle:.2f} = ${total_savings_expected:.2f}")
    print()

    # Calculate ROI metrics
    metrics = calc.compute_line_item_roi(product, params)

    print("ROI Metrics:")
    for key, value in metrics.items():
        if key == 'debug':
            print(f"  {key}:")
            for debug_key, debug_value in value.items():
                print(f"    {debug_key}: {debug_value}")
        else:
            print(f"  {key}: {value}")

    print()
    print("Analysis:")
    if metrics.get('savings', 0) == 0:
        print("❌ Savings is 0 - this is the problem!")
    else:
        print(f"✅ Savings: ${metrics.get('savings', 0):.2f}")

    if metrics.get('deltaInvestment', 0) == 0:
        print("❌ Delta Investment is 0 - no capital at risk!")
    else:
        print(f"✅ Delta Investment: ${metrics.get('deltaInvestment', 0):.2f}")

if __name__ == "__main__":
    debug_roi_calculation()
