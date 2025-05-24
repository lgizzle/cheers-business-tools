#!/usr/bin/env python3
"""
Test script to verify the new after-terms ROI calculation methodology.
Tests the specific case mentioned in the instructions:
- ROI = 100%
- DaysAtRisk = 45
- Expected Annual ROI ≈ 811%
"""

from multi_product_calculator import MultiProductBuyingCalculator
import json
import pprint

def test_after_terms_calculation():
    """Test the after-terms ROI calculation with the specific test case."""

    # Create a product that will result in ~45 days at risk
    # With 30-day payment terms, we need bulk inventory that lasts ~75 days total
    # So if we want 45 days at risk: bulk_cases_left / daily_cases = 45

    # Let's use: 75 cases bulk, daily velocity of 1 case/day, 30-day payment terms
    # This gives us: cases_sold_during_terms = 30, bulk_cases_left = 45, days_at_risk = 45

    product = {
        'name': 'Test Product - After Terms',
        'priceSmall': 20.0,    # Higher price difference to get 100% ROI
        'priceBulk': 10.0,     # Lower bulk price for better ROI
        'bottlesPerCase': 12,
        'bulkCases': 75,       # 75 cases total
        'annualCases': 365,    # 1 case per day velocity
        'onHandCases': 0,
    }

    # Create parameters with 30-day payment terms
    params = {
        'dealSizeCases': 75,
        'minDaysStock': 30,
        'paymentTermsDays': 30,  # 30-day payment terms
        'smallDealMinimum': 30,
    }

    # Create calculator
    calculator = MultiProductBuyingCalculator()

    # Calculate ROI
    result = calculator.compute_line_item_roi(product, params)

    # Print result
    print("==== After-Terms ROI Calculation Test ====")
    pprint.pprint(result)

    # Print key metrics for verification
    print("\n==== Test Case Verification ====")
    print(f"Cases Sold During Terms: {result['debug']['casesSoldDuringTerms']}")
    print(f"Bulk Cases Left (After Terms): {result['debug']['bulkCasesLeft']}")
    print(f"Days At Risk: {result['debug']['daysAtRisk']}")
    print(f"Base ROI: {result['roi']*100:.2f}%")
    print(f"Annual ROI Multiplier: {result['annualROIMultiplier']:.2f}")
    print(f"Annualized ROI: {result['annualizedRoi']*100:.2f}%")

    # Expected calculations:
    print(f"\n==== Expected vs Actual ====")
    expected_days_at_risk = 45
    expected_annual_multiplier = 365 / 45
    print(f"Expected Days At Risk: {expected_days_at_risk}")
    print(f"Expected Annual ROI Multiplier: {expected_annual_multiplier:.2f}")

    # Check if we're close to the test case
    days_at_risk = result['debug']['daysAtRisk']
    annual_multiplier = result['annualROIMultiplier']
    annualized_roi_pct = result['annualizedRoi'] * 100

    print(f"\nActual Days At Risk: {days_at_risk}")
    print(f"Actual Annual ROI Multiplier: {annual_multiplier:.2f}")
    print(f"Actual Annualized ROI: {annualized_roi_pct:.2f}%")

    # Test if we get something close to 811% with 100% ROI and 45 days at risk
    if abs(days_at_risk - 45) < 5:  # Within 5 days
        test_annual_roi = 1.0 * (365 / days_at_risk) * 100  # 100% ROI * multiplier
        print(f"\nTest calculation with actual days at risk:")
        print(f"100% × (365 ÷ {days_at_risk:.1f}) = {test_annual_roi:.1f}%")

    return result

if __name__ == "__main__":
    test_after_terms_calculation()
