#!/usr/bin/env python3

from playwright.sync_api import sync_playwright
import sys

def test_playwright():
    try:
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            # Navigate to our Flask app
            print("Navigating to http://localhost:8080...")
            page.goto("http://localhost:8080")

            # Take a screenshot
            page.screenshot(path="test_screenshot.png")
            print("Screenshot saved as test_screenshot.png")

            # Get the page title
            title = page.title()
            print(f"Page title: {title}")

            # Navigate to multi-product calculator
            print("Navigating to multi-product calculator...")
            page.goto("http://localhost:8080/multi-product-calculator")

            # Take another screenshot
            page.screenshot(path="calculator_screenshot.png")
            print("Calculator screenshot saved as calculator_screenshot.png")

            # Check for the "Add Product" button
            add_button = page.locator("text=Add Product")
            if add_button.count() > 0:
                print("✅ Add Product button found!")
            else:
                print("❌ Add Product button not found")

            # Check column headers
            roi_header = page.locator("text=After-Terms ROI Multiplier")
            if roi_header.count() > 0:
                print("✅ After-Terms ROI Multiplier column found!")
            else:
                print("❌ After-Terms ROI Multiplier column not found")

            browser.close()
            print("✅ Playwright test completed successfully!")
            return True

    except Exception as e:
        print(f"❌ Playwright test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_playwright()
    sys.exit(0 if success else 1)
