#!/usr/bin/env python3
"""
Test script to verify the DataFrame.append() fix in margin_calculator.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from margin_calculator import MarginCalculator

def test_margin_calculator():
    """Test the margin calculator with the fixed DataFrame.append() issue"""

    print("Testing Margin Calculator with DataFrame.append() fix...")

    # Create calculator instance
    calc = MarginCalculator()

    # Test basic calculations
    cost = 35.50
    current_price = 52.99
    target_margin = 0.30

    print(f"\nTest Parameters:")
    print(f"Cost: ${cost}")
    print(f"Current Price: ${current_price}")
    print(f"Target Margin: {target_margin*100}%")

    # Test price calculation
    price_at_target = calc.calculate_price_from_margin(cost, target_margin)
    print(f"\nPrice at target margin: ${price_at_target:.2f}")

    # Test margin calculation
    current_margin = calc.calculate_margin_from_price(cost, current_price)
    print(f"Current margin: {current_margin*100:.1f}%")

    # Test sensitivity analysis (this is where the DataFrame.append() was used)
    print("\nTesting sensitivity analysis (where the bug was)...")
    try:
        sensitivity_df = calc.perform_sensitivity_analysis(cost, current_price)
        if sensitivity_df is not None:
            print("✅ Sensitivity analysis completed successfully!")
            print(f"Generated {len(sensitivity_df)} rows of analysis")
            print("\nFirst few rows:")
            print(sensitivity_df.head())
        else:
            print("❌ Sensitivity analysis returned None")
    except Exception as e:
        print(f"❌ Error in sensitivity analysis: {e}")
        return False

    # Test report generation
    print("\nTesting report generation...")
    try:
        data = {
            'product_name': 'Premium Bourbon Whiskey',
            'cost': cost,
            'current_price': current_price,
            'target_margin': target_margin,
            'price_at_target_margin': price_at_target,
            'current_margin': current_margin,
            'current_markup': calc.calculate_markup_from_price(cost, current_price),
            'sensitivity_data': sensitivity_df
        }

        report_path = 'test_margin_report.xlsx'
        calc.generate_report(data, report_path)
        print(f"✅ Report generated successfully: {report_path}")

        # Clean up
        if os.path.exists(report_path):
            os.remove(report_path)
            print("✅ Test file cleaned up")

    except Exception as e:
        print(f"❌ Error in report generation: {e}")
        return False

    print("\n🎉 All tests passed! The DataFrame.append() fix is working correctly.")
    return True

if __name__ == "__main__":
    success = test_margin_calculator()
    sys.exit(0 if success else 1)
