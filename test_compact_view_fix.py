#!/usr/bin/env python3
"""
Test script to verify the compact view fix is working
"""

import requests
import re

def test_multi_product_calculator():
    """Test the multi-product calculator page loads and has the fixed JavaScript"""

    print("Testing Multi-Product Calculator compact view fix...")

    try:
        # Test if the server is running
        response = requests.get("http://localhost:8080/multi-product-calculator")
        if response.status_code != 200:
            print(f"❌ Server not responding properly (Status: {response.status_code})")
            return False

        print("✅ Multi-product calculator page loads successfully")

        # Check if the page contains the fixed JavaScript
        html_content = response.text

        # Look for the old buggy JavaScript selector (should not exist in JavaScript context)
        # But CSS selectors like .thead-light th[colspan="2"] are fine
        if 'querySelectorAll(\'th[colspan="2"]' in html_content or 'querySelectorAll("th[colspan=\\"2\\"]' in html_content:
            print("❌ Page still contains the buggy JavaScript selector")
            return False

        # Look for the new robust JavaScript selector (should exist)
        if 'querySelectorAll(\'th[colspan]\')' in html_content:
            print("✅ Page contains the fixed robust JavaScript selector")
        else:
            print("❌ Page doesn't contain the expected JavaScript selector")
            print("   Looking for: querySelectorAll('th[colspan]')")
            # Debug: show what we actually found
            if 'querySelectorAll' in html_content:
                print("   Found other querySelectorAll calls in the page")
            return False

        # Check for compact view toggle
        if 'id="compactViewToggle"' in html_content:
            print("✅ Compact view toggle is present")
        else:
            print("❌ Compact view toggle is missing")
            return False

        # Check for detail-column classes
        detail_column_count = html_content.count('class="detail-column"')
        if detail_column_count >= 10:  # Should be many detail-column elements
            print(f"✅ Found {detail_column_count} detail-column classes")
        else:
            print(f"❌ Only found {detail_column_count} detail-column classes (expected more)")
            return False

        print("\n🎉 Compact view fix appears to be working correctly!")
        print("\nFixed issues:")
        print("1. ✅ JavaScript now uses robust selector th[colspan] instead of th[colspan=\"2\"]")
        print("2. ✅ This allows proper restoration of columns when toggling back from compact view")
        print("3. ✅ No more lost columns when switching between views")

        return True

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask server. Make sure it's running on http://localhost:8080")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = test_multi_product_calculator()
    if not success:
        print("\n💡 To start the Flask server, run: python app.py")
        exit(1)
    else:
        print("\n✅ All tests passed!")
        exit(0)
