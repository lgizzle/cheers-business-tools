#!/usr/bin/env python3
"""
Simple test script to verify ROI calculation changes.
"""

from multi_product_calculator import MultiProductBuyingCalculator
import json
import pprint

def test_roi_calculation():
    """Test the ROI calculation with simple values."""
    # Create a product with simple values
    product = {
        'name': 'Test Product',
        'priceSmall': 10.0,
        'priceBulk': 8.0,
        'bottlesPerCase': 12,
        'bulkCases': 60,
        'annualCases': 360,  # 1 case per day
        'onHandCases': 0,
    }

    # Create parameters
    params = {
        'dealSizeCases': 60,
        'minDaysStock': 30,
        'paymentTermsDays': 30,
        'smallDealMinimum': 30,
    }

    # Create calculator
    calculator = MultiProductBuyingCalculator()

    # Calculate ROI
    result = calculator.compute_line_item_roi(product, params)

    # Print result
    print("==== ROI Calculation Result ====")
    pprint.pprint(result)

    # Print key metrics
    print("\n==== Key Metrics ====")
    print(f"Small Deal Cases: {result['smallDealCases']}")
    print(f"Cases Sold During Terms: {result['debug']['casesSoldDuringTerms']}")
    print(f"Small Cases Left: {result['debug']['smallCasesLeft']}")
    print(f"Bulk Cases Left: {result['debug']['bulkCasesLeft']}")
    print(f"Small Dollar Value: ${result['debug']['smallDollarValue']:.2f}")
    print(f"Bulk Dollar Value: ${result['debug']['bulkDollarValue']:.2f}")
    print(f"Average Small Investment: ${result['avgInvSmall']:.2f}")
    print(f"Average Bulk Investment: ${result['avgInvBulk']:.2f}")
    print(f"Delta Investment: ${result['deltaInvestment']:.2f}")
    print(f"Savings: ${result['savings']:.2f}")
    print(f"ROI: {result['roi']*100:.2f}%")
    print(f"Annualized ROI: {result['annualizedRoi']*100:.2f}%")
    print(f"Days to Deplete Bulk: {result['daysToDepleteBulk']:.1f}")

    # Raw data for manual verification
    print("\n==== Raw Data for Manual Verification ====")
    print(f"Daily Cases: {result['debug']['dailyVelocity']}")
    print(f"Total Savings: Q₂ × B × (P₁-P₂) = 60 × 12 × ($10-$8) = ${result['savings']:.2f}")
    print(f"Cases Sold During Terms: daily_cases × payment_terms_days = {result['debug']['dailyVelocity']:.2f} × 30 = {result['debug']['casesSoldDuringTerms']:.2f}")
    print(f"Small Cases Left: small_deal_cases - cases_sold_during_terms = {result['smallDealCases']} - {result['debug']['casesSoldDuringTerms']:.2f} = {result['debug']['smallCasesLeft']:.2f}")
    print(f"Bulk Cases Left: bulk_cases - cases_sold_during_terms = {product['bulkCases']} - {result['debug']['casesSoldDuringTerms']:.2f} = {result['debug']['bulkCasesLeft']:.2f}")
    print(f"Small Dollar Value: small_cases_left × price_small × bottles_per_case = {result['debug']['smallCasesLeft']:.2f} × ${product['priceSmall']} × {product['bottlesPerCase']} = ${result['debug']['smallDollarValue']:.2f}")
    print(f"Bulk Dollar Value: bulk_cases_left × price_bulk × bottles_per_case = {result['debug']['bulkCasesLeft']:.2f} × ${product['priceBulk']} × {product['bottlesPerCase']} = ${result['debug']['bulkDollarValue']:.2f}")
    print(f"Average Small Investment: small_dollar_value / 2 = ${result['debug']['smallDollarValue']:.2f} / 2 = ${result['avgInvSmall']:.2f}")
    print(f"Average Bulk Investment: bulk_dollar_value / 2 = ${result['debug']['bulkDollarValue']:.2f} / 2 = ${result['avgInvBulk']:.2f}")
    print(f"Delta Investment: avg_dollar_bulk - avg_dollar_small = ${result['avgInvBulk']:.2f} - ${result['avgInvSmall']:.2f} = ${result['deltaInvestment']:.2f}")
    print(f"ROI: savings / delta_investment = ${result['savings']:.2f} / ${result['deltaInvestment']:.2f} = {result['roi']*100:.2f}%")

if __name__ == "__main__":
    test_roi_calculation()
