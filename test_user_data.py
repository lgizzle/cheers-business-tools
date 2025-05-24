#!/usr/bin/env python3
"""
Test script with the exact data from the user's screenshot to verify the fix.
"""

from multi_product_calculator import MultiProductBuyingCalculator

def test_user_exact_data():
    """Test with the exact same data from the user's screenshot."""

    calculator = MultiProductBuyingCalculator()

    # Exact data from the screenshot
    products = [
        {'name': 'Single Malt Scotch', 'priceSmall': 69.99, 'priceBulk': 59.99, 'bottlesPerCase': 12, 'bulkCases': 6, 'annualCases': 73, 'onHandCases': 10},
        {'name': 'Bourbon Whiskey', 'priceSmall': 44.99, 'priceBulk': 36.99, 'bottlesPerCase': 12, 'bulkCases': 20, 'annualCases': 175, 'onHandCases': 15},
        {'name': 'Irish Whiskey', 'priceSmall': 39.99, 'priceBulk': 32.99, 'bottlesPerCase': 12, 'bulkCases': 7, 'annualCases': 84, 'onHandCases': 12},
        {'name': 'Single Malt Scotch', 'priceSmall': 69.99, 'priceBulk': 59.99, 'bottlesPerCase': 12, 'bulkCases': 12, 'annualCases': 146, 'onHandCases': 10},
        {'name': 'Bourbon Whiskey', 'priceSmall': 44.99, 'priceBulk': 36.99, 'bottlesPerCase': 12, 'bulkCases': 20, 'annualCases': 175, 'onHandCases': 15},
        {'name': 'Irish Whiskey', 'priceSmall': 39.99, 'priceBulk': 32.99, 'bottlesPerCase': 12, 'bulkCases': 15, 'annualCases': 162, 'onHandCases': 12}
    ]

    params = {
        'dealSizeCases': 80,
        'minDaysStock': 30,
        'paymentTermsDays': 30,
        'smallDealMinimum': 30
    }

    print("==== User's Exact Data Test ====")

    # Test backend calculation
    result = calculator.calculate({'products': products, 'parameters': params})

    print(f"Portfolio ROI: {result['portfolioROI']*100:.2f}%")
    print(f"Portfolio ROI Multiplier: {result['portfolioROIMultiplier']:.2f}")
    print(f"Weighted Avg Days At Risk: {result.get('weightedAvgDaysAtRisk', 'NOT FOUND')}")

    # Expected from screenshot: ROI: 58.86%, Multiplier: 6.24, Annualized: 367.02%
    expected_annualized = result['portfolioROI'] * result['portfolioROIMultiplier'] * 100
    print(f"Calculated Annualized ROI: {expected_annualized:.2f}%")

    # Also test individual products to see their investment amounts
    print(f"\n==== Individual Product Analysis ====")
    total_investment = 0
    weighted_days_sum = 0

    for i, product in enumerate(products):
        roi_result = calculator.compute_line_item_roi(product, params)
        delta_investment = roi_result.get('deltaInvestment', 0)
        days_at_risk = roi_result.get('debug', {}).get('daysAtRisk', 0)

        print(f"{product['name']}: Investment=${delta_investment:.2f}, Days At Risk={days_at_risk:.1f}")

        if delta_investment > 0:
            total_investment += delta_investment
            weighted_days_sum += days_at_risk * delta_investment

    manual_weighted_days = weighted_days_sum / total_investment if total_investment > 0 else 0
    manual_multiplier = 365 / manual_weighted_days if manual_weighted_days > 0 else 0

    print(f"\n==== Manual Verification ====")
    print(f"Total Investment: ${total_investment:.2f}")
    print(f"Manual Weighted Avg Days At Risk: {manual_weighted_days:.2f}")
    print(f"Manual Annual ROI Multiplier: {manual_multiplier:.2f}")

    # Compare with what the function returned
    print(f"\n==== Comparison ====")
    print(f"Function returned multiplier: {result['portfolioROIMultiplier']:.2f}")
    print(f"Manual calculated multiplier: {manual_multiplier:.2f}")
    print(f"Match: {abs(result['portfolioROIMultiplier'] - manual_multiplier) < 0.01}")

if __name__ == "__main__":
    test_user_exact_data()
