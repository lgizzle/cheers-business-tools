"""
Pure calculation functions for the multi-product deal calculator.
These functions handle core business logic calculations with no side effects.
"""

# Import math at the top level to ensure it's available for all functions
import math

def calculate_savings_per_case(current_price, bulk_price, bottles_per_case):
    """Calculate savings per case based on price difference."""
    return (current_price - bulk_price) * bottles_per_case

def calculate_total_savings(current_price, bulk_price, bulk_quantity, bottles_per_case):
    """Calculate total savings from a bulk purchase."""
    return calculate_savings_per_case(current_price, bulk_price, bottles_per_case) * bulk_quantity

def calculate_days_of_stock(cases_on_hand, cases_per_year):
    """Calculate days of stock based on inventory and annual sales."""
    if cases_per_year <= 0:
        return 0
    return (cases_on_hand / cases_per_year) * 365

def calculate_days_of_stock_after_purchase(cases_on_hand, bulk_quantity, cases_per_year):
    """Calculate days of stock after purchase."""
    return calculate_days_of_stock(cases_on_hand + bulk_quantity, cases_per_year)

def calculate_daily_cases(cases_per_year):
    """Calculate daily case sales."""
    return cases_per_year / 365

def calculate_holding_time(bulk_quantity, cases_per_year, max_days=365):
    """Calculate how long it will take to deplete inventory in days."""
    if cases_per_year <= 0:
        return 0
    return min(bulk_quantity / calculate_daily_cases(cases_per_year), max_days)

def calculate_peak_investment(bulk_price, bottles_per_case, bulk_quantity, daily_cases, payment_terms):
    """Calculate peak additional investment."""
    # Initial investment
    total_cost = bulk_price * bottles_per_case * bulk_quantity

    # If there are daily sales, we need to account for depletion during payment terms
    if daily_cases > 0:
        # Calculate how much inventory is sold each day (in dollars)
        daily_depletion_value = daily_cases * bulk_price * bottles_per_case

        # Calculate days it takes to fully deplete the inventory
        days_to_deplete = bulk_quantity / daily_cases

        # Only subtract the depletion that occurs during the payment terms
        # Limited by either the payment terms or how long it takes to deplete
        depletion_days = min(payment_terms, days_to_deplete)
        depletion_during_terms = depletion_days * daily_depletion_value

        # Ensure we don't deduct more than the total cost
        depletion_during_terms = min(depletion_during_terms, total_cost)

        # Adjust the total cost
        total_cost -= depletion_during_terms

    # Don't allow negative investment (though this shouldn't happen in practice)
    return max(0, total_cost)

def calculate_daily_carrying_cost(investment, annual_interest_rate):
    """Calculate daily carrying cost based on investment and interest rate."""
    daily_rate = annual_interest_rate / 365
    return investment * daily_rate

def calculate_roi(savings, investment):
    """
    Calculate ROI as a decimal (not percentage).

    Parameters:
    - savings: Total savings amount
    - investment: Total investment amount

    Returns: ROI as a decimal
    """
    if investment <= 0:
        return 0
    return savings / investment

def calculate_annualized_roi(roi, holding_time_years):
    """
    Calculate annualized ROI based on holding time in years.

    Parameters:
    - roi: ROI as a decimal
    - holding_time_years: Holding time in years

    Returns: Annualized ROI as a decimal
    """
    if holding_time_years <= 0.05:  # If holding time is less than ~18 days
        # Avoid division by very small numbers
        return roi * 2  # Conservative estimate: double the ROI for very short holding periods
    elif holding_time_years >= 1:
        # For holding times longer than a year, simply divide by the years
        return roi / holding_time_years
    else:
        # For holding times between 18 days and 1 year, scale up to annual equivalent
        # but cap at 5x the original ROI to avoid unreasonable numbers
        return min(roi / holding_time_years, roi * 5)

def calculate_holding_cost(bulk_price, bottles_per_case, bulk_quantity, daily_interest_rate, holding_time_days):
    """Calculate the cost of holding inventory based on interest rate."""
    investment = bulk_price * bottles_per_case * bulk_quantity
    return investment * daily_interest_rate * holding_time_days

def calculate_average_investment(peak_investment, bulk_price, bottles_per_case, bulk_quantity, daily_cases):
    """Calculate average investment throughout the holding period."""
    # If no sales, the average investment is the same as peak
    if daily_cases <= 0:
        return peak_investment

    # Calculate total initial investment
    initial_investment = bulk_price * bottles_per_case * bulk_quantity

    # Calculate days to deplete inventory
    days_to_deplete = bulk_quantity / daily_cases if daily_cases > 0 else 0

    # Average investment is the area under the depletion curve divided by time
    # For linear depletion, this is (peak + 0) / 2
    average_investment = peak_investment / 2

    return average_investment

def calculate_minimum_stock_needed(cases_on_hand, daily_cases, min_days_stock):
    """
    Calculate minimum additional cases needed to meet minimum days of stock.

    Parameters:
    - cases_on_hand: Current inventory in cases
    - daily_cases: Average daily sales in cases
    - min_days_stock: Minimum days of stock required

    Returns: Minimum additional cases needed (can be 0 if already met)
    """
    if daily_cases <= 0 or min_days_stock <= 0:
        return 0

    # Calculate required inventory for minimum days
    required_cases = daily_cases * min_days_stock

    # Calculate how many more cases are needed
    additional_needed = max(0, required_cases - cases_on_hand)

    return additional_needed

def calculate_maximum_stock(daily_cases, max_days, cases_on_hand):
    """
    Calculate maximum reasonable additional inventory to purchase.

    Parameters:
    - daily_cases: Average daily sales in cases
    - max_days: Maximum days of stock allowed
    - cases_on_hand: Current inventory in cases

    Returns: Maximum additional cases that should be purchased
    """
    if daily_cases <= 0 or max_days <= 0:
        return 0

    # Calculate maximum total inventory
    max_inventory = daily_cases * max_days

    # Calculate how many more cases can be added
    additional_allowed = max(0, max_inventory - cases_on_hand)

    return additional_allowed

def calculate_total_inventory(cases_on_hand, bulk_quantity):
    """Calculate total inventory after purchase."""
    return cases_on_hand + bulk_quantity

def compute_product_metrics(product, params):
    """
    Compute all metrics for a single product.

    Parameters:
    - product: Product dictionary with all required fields
    - params: Parameters dictionary with all required fields

    Returns: Dictionary with all calculated metrics
    """
    # Extract values from parameters
    daily_interest_rate = params.get("daily_interest_rate", 0.08 / 365)
    payment_terms = params.get("payment_terms", 30)

    # Calculate basic metrics
    daily_cases = calculate_daily_cases(product["cases_per_year"])
    savings_per_case = calculate_savings_per_case(
        product["current_price"], product["bulk_price"], product["bottles_per_case"]
    )
    bulk_quantity = product.get("bulk_quantity", 0)
    total_savings = calculate_total_savings(
        product["current_price"], product["bulk_price"], bulk_quantity, product["bottles_per_case"]
    )

    # Calculate days of stock
    days_of_stock = calculate_days_of_stock(product["cases_on_hand"], product["cases_per_year"])
    days_of_stock_after = calculate_days_of_stock_after_purchase(
        product["cases_on_hand"], bulk_quantity, product["cases_per_year"]
    )

    # Calculate holding time in days (time to sell through bulk quantity)
    # This is NOT the days of stock; it's how long it takes to sell just the bulk quantity
    holding_time_days = bulk_quantity / daily_cases if daily_cases > 0 else 0
    holding_time_years = holding_time_days / 365

    # Calculate investment (cost of buying bulk quantity)
    investment_per_case = product["bulk_price"] * product["bottles_per_case"]
    peak_investment = investment_per_case * bulk_quantity

    # Use payment terms to adjust peak investment if applicable
    if daily_cases > 0:
        # Calculate sales during payment terms (in dollars)
        days_to_deplete = bulk_quantity / daily_cases
        depletion_days = min(payment_terms, days_to_deplete)
        depletion_value = depletion_days * daily_cases * investment_per_case

        # Adjust peak investment
        peak_investment = max(0, peak_investment - depletion_value)

    # Calculate average investment over time (assuming linear depletion)
    average_investment = peak_investment / 2 if daily_cases > 0 else peak_investment

    # Calculate holding cost based on interest rate and holding time
    holding_cost = calculate_holding_cost(
        product["bulk_price"], product["bottles_per_case"], bulk_quantity, daily_interest_rate, holding_time_days
    )

    # Calculate ROI using net savings
    net_savings = max(0, total_savings - holding_cost)  # Ensure net savings is not negative
    roi = calculate_roi(net_savings, peak_investment)
    annual_roi = calculate_annualized_roi(roi, holding_time_years)

    return {
        "product_name": product["product_name"],
        "daily_cases": daily_cases,
        "savings_per_case": savings_per_case,
        "total_savings": total_savings,
        "days_of_stock": days_of_stock,
        "days_of_stock_after": days_of_stock_after,
        "holding_time_days": holding_time_days,
        "holding_time_years": holding_time_years,
        "peak_investment": peak_investment,
        "average_investment": average_investment,
        "holding_cost": holding_cost,
        "net_savings": net_savings,
        "roi": roi,
        "annual_roi": annual_roi
    }

def compute_scenario_metrics(products, params):
    """
    Compute overall scenario metrics for multiple products.

    Parameters:
    - products: List of product dictionaries
    - params: Parameters dictionary

    Returns: Dictionary with overall metrics
    """
    # Calculate metrics for each product
    product_metrics = [compute_product_metrics(product, params) for product in products]

    # Calculate overall metrics
    total_savings = sum(pm["total_savings"] for pm in product_metrics)
    total_holding_cost = sum(pm["holding_cost"] for pm in product_metrics)
    total_peak_investment = sum(pm["peak_investment"] for pm in product_metrics)
    total_average_investment = sum(pm["average_investment"] for pm in product_metrics)

    # Ensure net savings is not negative
    net_savings = max(0, total_savings - total_holding_cost)

    # Calculate overall ROI
    overall_roi = calculate_roi(net_savings, total_peak_investment)

    # Ensure overall ROI is not negative
    overall_roi = max(0, overall_roi)

    # Estimate overall holding time (weighted average)
    total_bulk_quantity = sum(p.get("bulk_quantity", 0) for p in products)
    if total_bulk_quantity > 0:
        weighted_holding_time = sum(
            pm["holding_time_years"] * p.get("bulk_quantity", 0) / total_bulk_quantity
            for pm, p in zip(product_metrics, products)
        )
    else:
        weighted_holding_time = 0

    # Calculate annualized ROI
    overall_annual_roi = calculate_annualized_roi(overall_roi, weighted_holding_time)

    return {
        "product_metrics": product_metrics,
        "total_savings": total_savings,
        "total_holding_cost": total_holding_cost,
        "net_savings": net_savings,
        "total_peak_investment": total_peak_investment,
        "total_average_investment": total_average_investment,
        "overall_roi": overall_roi,
        "weighted_holding_time": weighted_holding_time,
        "overall_annual_roi": overall_annual_roi
    }
