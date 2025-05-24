#!/usr/bin/env python3
"""
Test script to verify portfolio-level investment-weighted days at risk calculation.
"""

from multi_product_calculator import MultiProductBuyingCalculator
import json
import pprint

def test_portfolio_weighting():
    """Test the investment-weighted portfolio calculation."""

    # Create two products with different investment amounts and days at risk
    products = [
        {
            'name': 'Product A - High Investment',
            'priceSmall': 20.0,
            'priceBulk': 15.0,
            'bottlesPerCase': 12,
            'bulkCases': 60,     # Large allocation
            'annualCases': 365,  # 1 case/day
            'onHandCases': 0,
        },
        {
            'name': 'Product B - Low Investment',
            'priceSmall': 15.0,
            'priceBulk': 14.0,
            'bottlesPerCase': 12,
            'bulkCases': 40,     # Smaller allocation
            'annualCases': 365,  # 1 case/day
            'onHandCases': 0,
        }
    ]

    # Create parameters with 30-day payment terms
    params = {
        'dealSizeCases': 100,
        'minDaysStock': 30,
        'paymentTermsDays': 30,
        'smallDealMinimum': 30,
    }

    # Create calculator
    calculator = MultiProductBuyingCalculator()

    # Calculate individual product metrics first
    print("==== Individual Product Calculations ====")
    product_results = []
    total_investment = 0
    weighted_days_sum = 0

    for product in products:
        result = calculator.compute_line_item_roi(product, params)
        product_results.append(result)

        delta_investment = result['deltaInvestment']
        days_at_risk = result['debug']['daysAtRisk']

        print(f"\n{product['name']}:")
        print(f"  Delta Investment: ${delta_investment:,.2f}")
        print(f"  Days At Risk: {days_at_risk}")
        print(f"  ROI: {result['roi']*100:.2f}%")
        print(f"  Annual ROI Multiplier: {result['annualROIMultiplier']:.2f}")
        print(f"  Annualized ROI: {result['annualizedRoi']*100:.2f}%")

        # Manual calculation for verification
        if delta_investment > 0:
            total_investment += delta_investment
            weighted_days_sum += days_at_risk * delta_investment

    # Calculate expected portfolio metrics manually
    expected_weighted_days = weighted_days_sum / total_investment if total_investment > 0 else 0
    expected_multiplier = 365 / expected_weighted_days if expected_weighted_days > 0 else 0

    print(f"\n==== Manual Portfolio Calculation ====")
    print(f"Total Investment: ${total_investment:,.2f}")
    print(f"Weighted Days Sum: {weighted_days_sum:,.2f}")
    print(f"Expected Weighted Avg Days At Risk: {expected_weighted_days:.2f}")
    print(f"Expected Annual ROI Multiplier: {expected_multiplier:.2f}")

    # Now test the portfolio calculation
    portfolio_metrics = calculator.calculate_portfolio_roi(products, params)

    print(f"\n==== Calculator Portfolio Results ====")
    print(f"Portfolio ROI: {portfolio_metrics['roi']*100:.2f}%")
    print(f"Raw Deal Cycles/Year: {portfolio_metrics['dealCyclesPerYear']:.2f}")
    print(f"Annual ROI Multiplier: {portfolio_metrics['annualROIMultiplier']:.2f}")
    print(f"Weighted Avg Days At Risk: {portfolio_metrics['weightedAvgDaysAtRisk']:.2f}")

    # Verify the results match
    print(f"\n==== Verification ====")
    multiplier_match = abs(portfolio_metrics['annualROIMultiplier'] - expected_multiplier) < 0.01
    days_match = abs(portfolio_metrics['weightedAvgDaysAtRisk'] - expected_weighted_days) < 0.01

    print(f"Annual ROI Multiplier matches: {multiplier_match}")
    print(f"Weighted Days At Risk matches: {days_match}")

    if multiplier_match and days_match:
        print("✅ Portfolio weighting calculation is CORRECT!")
    else:
        print("❌ Portfolio weighting calculation has issues!")

    return portfolio_metrics

if __name__ == "__main__":
    test_portfolio_weighting()
