import calculator

# Parameters from the test
bulk_price = 25.0
bottles_per_case = 12
bulk_quantity = 10
daily_cases = 0.5
payment_terms = 20

# Debug the calculation steps
print("Input parameters:")
print(f"  Bulk price: ${bulk_price}")
print(f"  Bottles per case: {bottles_per_case}")
print(f"  Bulk quantity: {bulk_quantity} cases")
print(f"  Daily cases: {daily_cases}")
print(f"  Payment terms: {payment_terms} days")

# Initial investment
total_cost = bulk_price * bottles_per_case * bulk_quantity
print(f"\nInitial investment: ${total_cost}")

# Depletion calculation
if daily_cases > 0:
    daily_depletion_value = daily_cases * bulk_price * bottles_per_case
    print(f"Daily depletion value: ${daily_depletion_value}")

    days_to_deplete = bulk_quantity / daily_cases
    print(f"Days to deplete inventory: {days_to_deplete}")

    depletion_days = min(payment_terms, days_to_deplete)
    print(f"Depletion days (limited by payment terms): {depletion_days}")

    depletion_during_terms = depletion_days * daily_depletion_value
    print(f"Depletion during payment terms: ${depletion_during_terms}")

    # Check if we're deducting more than the total cost
    if depletion_during_terms > total_cost:
        print(f"Warning: Depletion exceeds total cost - limiting to {total_cost}")
        depletion_during_terms = total_cost

    adjusted_cost = total_cost - depletion_during_terms
    print(f"Adjusted cost after depletion: ${adjusted_cost}")

# Run the function
result = calculator.calculate_peak_investment(bulk_price, bottles_per_case, bulk_quantity, daily_cases, payment_terms)
print(f"\nFunction result: ${result}")

# Let's verify with manual calculation for the test case
# With daily_cases = 0.5, over 20 days we should sell 10 cases
# so all inventory is sold during payment terms (20 days = 10 cases)
# Expected value should be 3000.0 - (0.5 * 25.0 * 12 * 20) = 3000 - 3000 = 0

expected = total_cost - min(depletion_days * daily_depletion_value, total_cost)
print(f"Expected result: ${expected}")
