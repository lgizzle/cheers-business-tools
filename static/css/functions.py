def calculate_total_savings(p1, q1, p2, q2, b):
    """
    Calculate savings from purchasing bottles at bulk deal prices.

    Args:
        p1 (float): Price per bottle in the base deal
        q1 (int): Minimum quantity of cases needed for base deal
        p2 (float): Price per bottle in the bulk deal
        q2 (int): Minimum quantity of cases needed for bulk deal
        b (int): Number of bottles per case

    Returns:
        float: The calculated savings using (P1 - P2) * B * Q2
    """
    # Input validation
    if any(not isinstance(val, (int, float)) for val in [p1, q1, p2, q2, b]):
        raise TypeError("All inputs must be numeric")

    if any(val < 0 for val in [p1, q1, p2, q2, b]):
        raise ValueError("All inputs must be non-negative")

    # Calculate savings
    savings = (p1 - p2) * b * q2

    return savings

def calculate_peak_investment(p1, q1, p2, q2, b):
    """
    Calculate the peak investment required to purchase
    each deal.

    Args:
        p1 (float): Price per bottle in the base deal
        q1 (int): Minimum quantity of cases needed for base deal
        p2 (float): Price per bottle in the bulk deal
        q2 (int): Minimum quantity of cases needed for bulk deal
        b (int): Number of bottles per case

    Returns:
        # returns a list of floats that represent the peak investment for each deal

    """
    peak_investment = [p1 * b * q1, p2 * b * q2]
    return peak_investment




def calculate_cases_sold_per_day(v, b):
    """
    Calculate the number of cases sold per day.

    Args:
        v (float): The volume of cases sold per year
        b (int): The number of bottles per case

    Returns:
        float: The number of cases sold per day
    """
    cases_sold_per_day = v / (365 * b)
    return cases_sold_per_day

def boolean_deal_exceeds_dealer_terms_period(cases_sold_within_dealer_terms_period, q1, q2):
    """
    Determine whether the number of cases sold per dealer
    term exceeds the quantity of cases needed for the deal.

    Args:
        cases_sold_per_dealer_term (int): The number of cases sold per dealer term
        q (int): The quantity of cases needed for the deal

    Returns:
        list of booleans: True if the number of cases sold per dealer
        term exceeds the quantity of cases needed for the
        deal, False otherwise
    """
    deal_exceeds_dealer_terms_period = [cases_sold_within_dealer_terms_period >= q1, cases_sold_within_dealer_terms_period >= q2]
    return deal_exceeds_dealer_terms_period

def is_infinite_return(deal_exceeds_dealer_terms_period):
    """
    Determine whether the number of cases sold per dealer
    term exceeds the quantity of cases needed for the deal.
    """
    if deal_exceeds_dealer_terms_period[0] and deal_exceeds_dealer_terms_period[1]:
        return True
    if deal_exceeds_dealer_terms_period[0] or deal_exceeds_dealer_terms_period[1]:
        return False
    else:
        return False

def calculate_cases_sold_within_dealer_terms_period(v, b, t):
    """
    Calculate the number of cases sold per dealer term.
    """
    cases_sold_within_dealer_terms_period = v / (t * b)
    return cases_sold_within_dealer_terms_period

def calculate_holding_period_for_deal(q, cases_sold_per_day):
    """
    Calculate the holding period for a deal.

    Args:
        q (int): The quantity of cases needed for the deal
        cases_sold_per_day (float): The number of cases sold per day

    Returns:
        float: The holding period for a deal
    """
    holding_period_for_deal = q / cases_sold_per_day
    return holding_period_for_deal


# fx to calculate cases left over after dealer terms period
# must first check if the dealer terms period has been exceeded for each deal
# if so, return the number of cases left over
# if not, return 0
# needs to be done for each deal

def calculate_cases_left_over(cases_sold_within_dealer_terms_period, q1, q2):
    """
    Calculate the number of cases left over after the dealer terms period.

    args:
        cases_sold_within_dealer_terms_period (int): The
        number of cases sold within the dealer terms period
        q1 (int): The quantity of cases needed for the first deal
        q2 (int): The quantity of cases needed for the second deal

    returns:
        list of ints: A list of the number of cases left over
        after the dealer terms period for each deal
    """
    cases_left_over = [
        cases_sold_within_dealer_terms_period - q1,
        cases_sold_within_dealer_terms_period - q2
    ]
    return cases_left_over

# calculate dollar value of cases left over
# since the number of cases left is a number, we need to multiply it by the price per bottle
# no special case for it if it is 0

def calculate_dollar_value_of_cases_left_over(cases_left_over, p1, p2, b):
    """
    Calculate the dollar value of cases left over.

    args:
        cases_left_over (list of ints): A list of the number of cases left over
        p1 (float): The price per bottle in the first deal
        p2 (float): The price per bottle in the second deal
        b (int): The number of bottles per case

    returns:
        list of floats: A list of the dollar value of cases left over for each deal
    """
    dollar_value_of_cases_left_over = [cases_left_over[0] * p1 * b, cases_left_over[1] * p2 * b]
    return dollar_value_of_cases_left_over

def calculate_additional_holding_period(dollar_value_of_cases_left_over, cases_sold_per_day):
    """
    Calculate the additional holding period.

    args:
        cases_left_over (int): The number of cases left over
        cases_sold_per_day (float): The number of cases sold per day

    returns:
        float: The additional holding period in days
    """
    additional_holding_period = dollar_value_of_cases_left_over / cases_sold_per_day
    return additional_holding_period

# calculate average dollar value of cases left over
# assume linear depreciation of cases left over at the rate of cases_sold_per_day
# no special case for it if it is 0

def calculate_average_dollar_value_of_cases_left_over(dollar_value_of_cases_left_over):
    """
    Calculate the average dollar value of cases left over.

    args:
        dollar_value_of_cases_left_over (list of floats): A list of the dollar value of cases left over

    returns:
        list of floats: A list of the average dollar value of cases left over
    """
    average_dollar_value_of_cases_left_over = [dollar_value_of_cases_left_over[0] / 2, dollar_value_of_cases_left_over[1] / 2]
    return average_dollar_value_of_cases_left_over

# calculate the deleta of average dollar value of cases left over
# no special case for it if it is 0

def calculate_delta_of_average_dollar_value_of_cases_left_over(average_dollar_value_of_cases_left_over):
    """
    Calculate the delta of average dollar value of cases left over.

    args:
        average_dollar_value_of_cases_left_over (list of floats): A list of the average dollar value of cases left over

    returns:
        integer: The delta of average dollar value of cases
        left over as it relates to the second deal
    """
    delta_of_average_dollar_value_of_cases_left_over = average_dollar_value_of_cases_left_over[1] - average_dollar_value_of_cases_left_over[0]
    return delta_of_average_dollar_value_of_cases_left_over

def calculate_roi(savings, delta_of_average_dollar_value_of_cases_left_over):
    """
    Calculate the return on investment.

    args:
        savings (float): The savings from the deal
        delta_of_average_dollar_value_of_cases_left_over (int): The delta of average dollar value of cases left over

    returns:
        float: The return on investment
    """
    roi = savings / delta_of_average_dollar_value_of_cases_left_over
    return roi

def calculate_deal_turnover_rate(additional_holding_period):
    """
    Calculate the deal turnover rate.

    args:
        additional_holding_period (float): The additional holding period

    returns:
        float: The deal turnover rate in turns per year
    """
    deal_turnover_rate = 365 / additional_holding_period
    return deal_turnover_rate

def calculate_annualized_roi(roi, deal_turnover_rate):
    """
    Calculate the annualized return on investment.

    args:
        roi (float): The return on investment
        deal_turnover_rate (float): The deal turnover rate

    returns:
        float: The annualized return on investment
    """
    annualized_roi = roi * deal_turnover_rate
    return annualized_roi
    # why one plus?  seems like we'd just use the roi and then annual


