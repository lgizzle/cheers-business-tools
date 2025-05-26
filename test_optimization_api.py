#!/usr/bin/env python3
"""
Test script to verify optimization API is working with annualized ROI
"""

import json
import requests

def test_optimization_api():
    """Test the optimization API with realistic data"""

    print("Testing Optimization API with Annualized ROI")
    print("=" * 60)

    # Create realistic test data
    test_data = {
        'products': [
            {
                'id': 'product-1',
                'product_name': 'Fast Moving Vodka',
                'current_price': 15.99,
                'bulk_price': 13.99,
                'on_hand': 3,
                'annual_cases': 120,  # Fast moving
                'bottles_per_case': 12,
                'bulk_quantity': 25
            },
            {
                'id': 'product-2',
                'product_name': 'Slow Moving Premium',
                'current_price': 25.99,
                'bulk_price': 22.99,  # Better discount
                'on_hand': 2,
                'annual_cases': 36,   # Slow moving
                'bottles_per_case': 12,
                'bulk_quantity': 25
            },
            {
                'id': 'product-3',
                'product_name': 'Medium Moving Whiskey',
                'current_price': 19.99,
                'bulk_price': 17.99,
                'on_hand': 4,
                'annual_cases': 72,   # Medium moving
                'bottles_per_case': 12,
                'bulk_quantity': 25
            }
        ],
        'parameters': {
            'dealSizeCases': 75,
            'minDaysStock': 21,
            'paymentTermsDays': 15,  # Short terms to see ROI
            'smallDealCases': 20,
            'iterations': 10
        }
    }

    print("Initial Setup:")
    print(f"  Deal Size: {test_data['parameters']['dealSizeCases']} cases")
    print(f"  Payment Terms: {test_data['parameters']['paymentTermsDays']} days")
    print(f"  Optimization Iterations: {test_data['parameters']['iterations']}")
    print()

    print("Products:")
    for product in test_data['products']:
        print(f"  {product['product_name']}: {product['bulk_quantity']} cases")
        print(f"    Annual Cases: {product['annual_cases']}")
        print(f"    Price: ${product['current_price']:.2f} → ${product['bulk_price']:.2f}")
        discount = ((product['current_price'] - product['bulk_price']) / product['current_price']) * 100
        print(f"    Discount: {discount:.1f}%")
    print()

    # First, calculate initial results
    print("Step 1: Calculate Initial Results")
    try:
        response = requests.post('http://localhost:8080/api/calculate-multi-product-deal',
                               json=test_data,
                               headers={'Content-Type': 'application/json'})

        if response.status_code == 200:
            initial_results = response.json()
            if initial_results.get('success'):
                print(f"  ✅ Initial Portfolio ROI: {initial_results['results']['portfolioROI']:.4f} ({initial_results['results']['portfolioROI']*100:.2f}%)")
                print(f"  ✅ Initial Annualized ROI: {initial_results['results']['portfolioROI'] * initial_results['results']['portfolioROIMultiplier']:.4f}")
            else:
                print(f"  ❌ Calculation failed: {initial_results.get('error', 'Unknown error')}")
                return
        else:
            print(f"  ❌ HTTP Error: {response.status_code}")
            return
    except Exception as e:
        print(f"  ❌ Request failed: {e}")
        return

    print()

    # Now run optimization
    print("Step 2: Run Optimization")
    try:
        response = requests.post('http://localhost:8080/api/optimize-multi-product-deal',
                               json=test_data,
                               headers={'Content-Type': 'application/json'})

        if response.status_code == 200:
            optimization_results = response.json()
            if optimization_results.get('success'):
                results = optimization_results['results']
                print(f"  ✅ Optimization completed!")
                print(f"  ✅ Total Iterations: {results.get('totalIterations', 0)}")
                print(f"  ✅ Final Portfolio ROI: {results['portfolioROI']:.4f} ({results['portfolioROI']*100:.2f}%)")
                print(f"  ✅ Final Annualized ROI: {results['portfolioROI'] * results['portfolioROIMultiplier']:.4f}")

                # Show optimization history
                history = results.get('history', [])
                if len(history) > 1:
                    print(f"\n  Optimization History:")
                    for entry in history:
                        iteration = entry.get('iteration', 0)
                        total_roi = entry.get('totalROI', 0)
                        swapped = entry.get('swapped', {})

                        if iteration == 0:
                            print(f"    Iteration {iteration}: Initial allocation (ROI: {total_roi:.4f})")
                        else:
                            from_product = swapped.get('from', '')
                            to_product = swapped.get('to', '')
                            print(f"    Iteration {iteration}: Moved 1 case from {from_product} to {to_product} (ROI: {total_roi:.4f})")

                # Show final allocation
                print(f"\n  Final Product Allocation:")
                for product in results['products']:
                    bulk_qty = product.get('bulk_quantity', 0)
                    metrics = product.get('metrics', {})
                    regular_roi = metrics.get('roi', 0)
                    annualized_roi = metrics.get('annualizedRoi', 0)
                    print(f"    {product['product_name']}: {bulk_qty} cases")
                    print(f"      Regular ROI: {regular_roi:.4f} ({regular_roi*100:.2f}%)")
                    print(f"      Annualized ROI: {annualized_roi:.4f} ({annualized_roi*100:.2f}%)")

                # Check if optimization made improvements
                initial_roi = initial_results['results']['portfolioROI']
                final_roi = results['portfolioROI']
                improvement = final_roi - initial_roi

                print(f"\n  Analysis:")
                if improvement > 0:
                    print(f"    ✅ Optimization improved ROI by {improvement:.4f} ({improvement*100:.2f} percentage points)")
                elif improvement == 0:
                    print(f"    ℹ️  No improvement found (already optimal)")
                else:
                    print(f"    ❌ ROI decreased by {abs(improvement):.4f} (this shouldn't happen!)")

            else:
                print(f"  ❌ Optimization failed: {optimization_results.get('error', 'Unknown error')}")
        else:
            print(f"  ❌ HTTP Error: {response.status_code}")
            print(f"  Response: {response.text}")
    except Exception as e:
        print(f"  ❌ Request failed: {e}")

    print("\n" + "=" * 60)
    print("Test completed!")

if __name__ == "__main__":
    test_optimization_api()
