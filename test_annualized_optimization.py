#!/usr/bin/env python3
"""
Test script to verify that optimization now uses annualized ROI
"""

import json
from multi_product_calculator import MultiProductBuyingCalculator

def test_annualized_roi_optimization():
    """Test that optimization now uses annualized ROI for decision making"""

    print("Testing Annualized ROI Optimization")
    print("=" * 50)

    # Create calculator instance
    calc = MultiProductBuyingCalculator()

    # Create test data with products that have different ROI vs Annualized ROI characteristics
    test_data = {
        'products': [
            {
                'id': 1,
                'name': 'Fast Moving Product',
                'current_price': 10.00,
                'bulk_price': 8.50,
                'on_hand': 2,
                'annual_cases': 365,  # 1 case per day - very fast moving
                'bottles_per_case': 12,
                'bulk_quantity': 20
            },
            {
                'id': 2,
                'name': 'Slow Moving Product',
                'current_price': 10.00,
                'bulk_price': 8.00,  # Better discount but slower moving
                'on_hand': 2,
                'annual_cases': 73,   # 0.2 cases per day - slow moving
                'bottles_per_case': 12,
                'bulk_quantity': 20
            },
            {
                'id': 3,
                'name': 'Medium Moving Product',
                'current_price': 10.00,
                'bulk_price': 8.75,
                'on_hand': 2,
                'annual_cases': 182,  # 0.5 cases per day - medium moving
                'bottles_per_case': 12,
                'bulk_quantity': 20
            }
        ],
        'parameters': {
            'dealSizeCases': 60,
            'minDaysStock': 21,
            'paymentTermsDays': 15,
            'smallDealCases': 15,
            'iterations': 5
        }
    }

    print("Initial Product Setup:")
    for product in test_data['products']:
        print(f"  {product['name']}: {product['bulk_quantity']} cases")

    # Calculate initial metrics to see ROI vs Annualized ROI differences
    print("\nInitial ROI Analysis:")
    for product in test_data['products']:
        metrics = calc.compute_line_item_roi(product, test_data['parameters'])
        regular_roi = metrics.get('roi', 0)
        annualized_roi = metrics.get('annualizedRoi', 0)
        print(f"  {product['name']}:")
        print(f"    Regular ROI: {regular_roi:.4f} ({regular_roi*100:.2f}%)")
        print(f"    Annualized ROI: {annualized_roi:.4f} ({annualized_roi*100:.2f}%)")
        print(f"    Ratio (Ann/Reg): {annualized_roi/regular_roi:.2f}x" if regular_roi > 0 else "    Ratio: N/A")

    # Run optimization
    print("\nRunning Optimization...")
    results = calc.optimize(test_data)

    print(f"\nOptimization Results:")
    print(f"  Total Iterations: {results.get('totalIterations', 0)}")
    print(f"  Portfolio ROI: {results.get('portfolioROI', 0):.4f} ({results.get('portfolioROI', 0)*100:.2f}%)")

    print("\nFinal Product Allocation:")
    for product in results['products']:
        bulk_qty = product.get('bulk_quantity', 0)
        metrics = product.get('metrics', {})
        regular_roi = metrics.get('roi', 0)
        annualized_roi = metrics.get('annualizedRoi', 0)
        print(f"  {product['name']}: {bulk_qty} cases")
        print(f"    Regular ROI: {regular_roi:.4f} ({regular_roi*100:.2f}%)")
        print(f"    Annualized ROI: {annualized_roi:.4f} ({annualized_roi*100:.2f}%)")

    # Show optimization history
    history = results.get('history', [])
    if history:
        print("\nOptimization History:")
        for entry in history:
            iteration = entry.get('iteration', 0)
            total_roi = entry.get('totalROI', 0)
            swapped = entry.get('swapped', {})

            if iteration == 0:
                print(f"  Iteration {iteration}: Initial allocation (ROI: {total_roi:.4f})")
            else:
                from_product = swapped.get('from', '')
                to_product = swapped.get('to', '')
                print(f"  Iteration {iteration}: Moved 1 case from {from_product} to {to_product} (ROI: {total_roi:.4f})")

    print("\n" + "=" * 50)
    print("Test completed! Check if optimization decisions make sense based on annualized ROI.")

if __name__ == "__main__":
    test_annualized_roi_optimization()
