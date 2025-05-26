#!/usr/bin/env python3
"""
Test to verify that optimization uses annualized ROI for decision making
"""

import json
import requests

def test_annualized_roi_optimization():
    """Test that optimization uses annualized ROI for decisions"""

    print("Testing Annualized ROI Optimization Fix")
    print("=" * 50)

    # Create test data where regular ROI and annualized ROI would lead to different decisions
    test_data = {
        'products': [
            {
                'id': 'product-1',
                'product_name': 'Product A - High Regular ROI, Low Annualized',
                'current_price': 10.00,
                'bulk_price': 8.00,  # 20% discount
                'on_hand': 2,
                'annual_cases': 50,   # Slow moving = low annualized ROI
                'bottles_per_case': 12,
                'bulk_quantity': 30
            },
            {
                'id': 'product-2',
                'product_name': 'Product B - Lower Regular ROI, High Annualized',
                'current_price': 10.00,
                'bulk_price': 8.50,  # 15% discount (lower than A)
                'on_hand': 2,
                'annual_cases': 200,  # Fast moving = high annualized ROI
                'bottles_per_case': 12,
                'bulk_quantity': 30
            },
            {
                'id': 'product-3',
                'product_name': 'Product C - Medium',
                'current_price': 10.00,
                'bulk_price': 8.25,
                'on_hand': 2,
                'annual_cases': 100,
                'bottles_per_case': 12,
                'bulk_quantity': 40
            }
        ],
        'parameters': {
            'dealSizeCases': 100,
            'minDaysStock': 21,
            'paymentTermsDays': 15,  # Short terms to show annualized effect
            'smallDealCases': 25,
            'iterations': 5
        }
    }

    # Calculate initial results
    print("Step 1: Calculate initial results...")
    calc_response = requests.post('http://localhost:8080/api/calculate-multi-product-deal',
                                json=test_data)

    if calc_response.status_code == 200:
        calc_results = calc_response.json()
        print("Initial calculation successful!")

        # Show the ROI vs Annualized ROI for each product
        print("\nProduct ROI Analysis:")
        for product in calc_results['products']:
            metrics = product.get('metrics', {})
            if 'error' not in metrics:
                roi = metrics.get('roi', 0) * 100
                multiplier = metrics.get('annualROIMultiplier', 0)
                annualized_roi = roi * multiplier
                print(f"  {product['product_name'][:20]}...")
                print(f"    Regular ROI: {roi:.2f}%")
                print(f"    Multiplier: {multiplier:.2f}x")
                print(f"    Annualized ROI: {annualized_roi:.2f}%")
                print()

        # Run optimization
        print("Step 2: Run optimization...")
        opt_response = requests.post('http://localhost:8080/api/optimize-multi-product-deal',
                                   json=test_data)

        if opt_response.status_code == 200:
            opt_results = opt_response.json()
            print("Optimization successful!")

            # Check if optimization made changes
            history = opt_results.get('history', [])
            if len(history) > 1:
                print(f"\nOptimization made {len(history)-1} changes:")
                for i, iteration in enumerate(history):
                    if i == 0:
                        print(f"  Initial: {iteration['totalROI']*100:.2f}% ROI")
                    else:
                        change = (iteration['totalROI'] - history[i-1]['totalROI']) * 100
                        print(f"  Iteration {i}: {iteration['totalROI']*100:.2f}% ROI (change: +{change:.3f}%)")

                # The key test: if optimization is using annualized ROI,
                # it should prefer Product B over Product A despite lower regular ROI
                print("\n" + "="*50)
                print("ANALYSIS:")
                print("If optimization uses REGULAR ROI:")
                print("  - Should prefer Product A (20% discount)")
                print("If optimization uses ANNUALIZED ROI:")
                print("  - Should prefer Product B (faster moving)")
                print("="*50)

            else:
                print("No optimization changes made")
        else:
            print(f"Optimization failed: {opt_response.status_code}")
            print(opt_response.text)
    else:
        print(f"Calculation failed: {calc_response.status_code}")
        print(calc_response.text)

if __name__ == "__main__":
    test_annualized_roi_optimization()

