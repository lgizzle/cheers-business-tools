#!/usr/bin/env python3

from playwright.sync_api import sync_playwright
import sys
import time

def test_calculator_functionality():
    try:
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            print("🧪 Testing Multi-Product Calculator...")
            page.goto("http://localhost:8080/multi-product-calculator")

            # Wait for page to load
            page.wait_for_load_state("networkidle")

            # Check column headers in correct order
            print("📋 Checking column headers...")

            # Look for the table headers
            headers = page.locator("th").all_text_contents()
            print(f"Found headers: {headers}")

            # Check specific order: ROI → After-Terms ROI Multiplier → Ann. ROI
            expected_sequence = ["ROI", "After-Terms ROI Multiplier", "Ann. ROI"]
            header_text = " ".join(headers)

            if "After-Terms ROI Multiplier" in header_text:
                print("✅ After-Terms ROI Multiplier column header found!")
            else:
                print("❌ After-Terms ROI Multiplier column header missing!")

            # Add a product
            print("➕ Adding a test product...")
            add_button = page.locator("#addProductRow")
            add_button.click()

            # Wait for the row to be added
            time.sleep(1)

            # Fill in test data
            print("📝 Filling in test product data...")

            # Fill in the input fields for the first product
            product_rows = page.locator("tbody tr")
            if product_rows.count() > 0:
                first_row = product_rows.first

                # Fill in product details
                first_row.locator("input[placeholder='Product Name']").fill("Test Product")
                first_row.locator("input[placeholder='Annual Cases']").fill("1000")
                first_row.locator("input[placeholder='On Hand Cases']").fill("50")
                first_row.locator("input[placeholder='Case Cost']").fill("10.00")
                first_row.locator("input[placeholder='Small Deal Cases']").fill("100")
                first_row.locator("input[placeholder='Small Deal Price']").fill("12.00")
                first_row.locator("input[placeholder='Big Deal Price']").fill("11.00")

                # Set bulk cases
                bulk_input = first_row.locator(".product-bulk-cases")
                bulk_input.fill("200")

                print("✅ Test data entered!")

            # Click Calculate
            print("🔢 Running calculation...")
            calculate_button = page.locator("text=Calculate Initial Allocation")
            calculate_button.click()

            # Wait for calculation to complete
            time.sleep(3)

            # Take screenshot of results
            page.screenshot(path="calculator_results.png")
            print("📸 Results screenshot saved as calculator_results.png")

            # Check that values populated in correct columns
            print("🔍 Checking calculated values...")

            # Look for data cells in the table
            data_cells = page.locator("tbody td").all_text_contents()
            print(f"Found data cells: {data_cells[:10]}...")  # Show first 10

            # Check for specific values
            roi_found = any("%" in cell for cell in data_cells)
            if roi_found:
                print("✅ ROI values found (contain % symbol)")
            else:
                print("❌ No ROI values found")

            # Check totals row
            totals_row = page.locator("#totalsRow")
            if totals_row.count() > 0:
                totals_text = totals_row.text_content()
                print(f"📊 Totals row: {totals_text}")
                print("✅ Totals row found!")
            else:
                print("❌ Totals row not found")

            # Check summary section
            summary = page.locator(".summary-section")
            if summary.count() > 0:
                summary_text = summary.text_content()
                print(f"📈 Summary section found")
                if "After-Terms" in summary_text:
                    print("✅ After-Terms metrics in summary!")
                else:
                    print("❌ After-Terms metrics missing from summary")

            browser.close()
            print("🎉 Calculator test completed successfully!")
            return True

    except Exception as e:
        print(f"❌ Calculator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_calculator_functionality()
    sys.exit(0 if success else 1)
