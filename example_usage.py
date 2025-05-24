"""
Example usage of the Multi-Product Buying Calculator.
"""

from multi_product_calculator_new import MultiProductCalculator

def main():
    """Main function to demonstrate the calculator."""
    # Create calculator
    calculator = MultiProductCalculator()

    # Set parameters
    calculator.set_params({
        "small_deal_minimum": 30,
        "bulk_deal_minimum": 60,
        "payment_terms": 30
    })

    # Add products
    products = [
        {
            "product_name": "Jack Daniels 750ml",
            "current_price": 25.0,
            "bulk_price": 23.5,
            "cases_on_hand": 5,
            "cases_per_year": 60,
            "bottles_per_case": 12
        },
        {
            "product_name": "Jack Daniels 1.75L",
            "current_price": 45.0,
            "bulk_price": 42.0,
            "cases_on_hand": 2,
            "cases_per_year": 80,
            "bottles_per_case": 6
        },
        {
            "product_name": "Jack Daniels 375ml",
            "current_price": 14.0,
            "bulk_price": 13.0,
            "cases_on_hand": 0,
            "cases_per_year": 60,
            "bottles_per_case": 24
        },
        {
            "product_name": "Jack Daniels Honey 750ml",
            "current_price": 27.0,
            "bulk_price": 25.5,
            "cases_on_hand": 0,
            "cases_per_year": 90,
            "bottles_per_case": 12
        },
        {
            "product_name": "Gentleman Jack 750ml",
            "current_price": 32.0,
            "bulk_price": 30.0,
            "cases_on_hand": 1,
            "cases_per_year": 40,
            "bottles_per_case": 12
        }
    ]

    calculator.set_products(products)

    # Try different allocation strategies
    print("\nUsing proportional allocation:")
    proportional_result = calculator.suggest_quantities("proportional")
    print_products_summary(proportional_result)

    print("\nUsing ROI-based allocation:")
    roi_result = calculator.suggest_quantities("roi")
    print_products_summary(roi_result)

    print("\nUsing proportional allocation with minimum 14 days of stock:")
    min_stock_result = calculator.suggest_quantities("proportional", min_days_stock=14)
    print_products_summary(min_stock_result)

    # Calculate metrics
    print("\nCalculating metrics:")
    results = calculator.calculate()

    # Print summary results
    print("\nSummary Results:")
    print(f"Peak Additional Investment: ${results['total_peak_investment']:.2f}")
    print(f"Average Investment: ${results['total_average_investment']:.2f}")
    print(f"Total Savings: ${results['total_savings']:.2f}")
    print(f"Overall ROI: {results['overall_roi'] * 100:.2f}%")
    print(f"Annualized ROI: {results['overall_annual_roi'] * 100:.2f}%")

    # Print product metrics
    print("\nProduct Metrics:")
    for pm in results["product_metrics"]:
        print(f"{pm['product_name']}:")
        print(f"  Savings Per Case: ${pm['savings_per_case']:.2f}")
        print(f"  Total Savings: ${pm['total_savings']:.2f}")
        print(f"  ROI: {pm['roi'] * 100:.2f}%")
        print(f"  Days of Stock After Purchase: {pm['days_of_stock_after']:.1f}")

    # Save scenario
    calculator.save_scenario("Jack Daniels Demo")

    # Export to Excel
    excel_path = calculator.export_to_excel("Jack Daniels Demo")
    print(f"\nExported to Excel: {excel_path}")

    # Export debug info
    debug_path = calculator.export_debug_info("Jack Daniels Demo")
    print(f"Exported debug info: {debug_path}")

def print_products_summary(products):
    """Print a summary of the products with their bulk quantities."""
    total_quantity = sum(p.get("bulk_quantity", 0) for p in products)

    for product in products:
        print(f"{product['product_name']}: {product.get('bulk_quantity', 0):.1f} cases")

    print(f"Total Bulk Quantity: {total_quantity:.1f} cases")

if __name__ == "__main__":
    main()
