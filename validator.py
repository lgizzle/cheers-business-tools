"""
Input validation functions for the multi-product calculator.
Validates all inputs to ensure they meet requirements and constraints.
"""

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

def format_currency(val):
    try:
        return f"${float(val):.2f}"
    except Exception:
        return str(val)

def validate_numeric(value, name, min_value=None, allow_zero=True, integer_only=False):
    """
    Validate that a value is numeric and within constraints.

    Parameters:
    - value: The value to validate
    - name: Name of the parameter (for error messages)
    - min_value: Minimum allowed value (optional)
    - allow_zero: Whether zero is allowed (default True)
    - integer_only: Whether only integers are allowed (default False)

    Raises ValidationError if validation fails.
    """
    # Check if value is numeric
    try:
        numeric_value = float(value)
        if integer_only and int(numeric_value) != numeric_value:
            raise ValidationError(f"{name} must be an integer, got {value}")
    except (ValueError, TypeError):
        raise ValidationError(f"{name} must be a number, got {value}")

    # Check if value is negative
    if numeric_value < 0:
        if name.lower().endswith('price'):
            raise ValidationError(f"{name} cannot be negative, got {format_currency(value)}")
        else:
            raise ValidationError(f"{name} cannot be negative, got {value}")

    # Check if zero is allowed
    if not allow_zero and numeric_value == 0:
        raise ValidationError(f"{name} cannot be zero")

    # Check minimum value
    if min_value is not None and numeric_value < min_value:
        if name.lower().endswith('price'):
            raise ValidationError(f"{name} must be at least {format_currency(min_value)}, got {format_currency(value)}")
        else:
            raise ValidationError(f"{name} must be at least {min_value}, got {value}")

    return numeric_value

def validate_product(product):
    """
    Validate a product's required fields and constraints.

    Parameters:
    - product: Dictionary containing product data

    Returns: Validated product with numeric fields converted to appropriate types.
    Raises ValidationError if validation fails.
    """
    # Check required fields
    required_fields = [
        "product_name", "current_price", "bulk_price",
        "on_hand", "annual_cases", "bottles_per_case"
    ]

    for field in required_fields:
        if field not in product:
            raise ValidationError(f"Missing required field: {field}")

    # Validate product name
    if not product["product_name"] or not isinstance(product["product_name"], str):
        raise ValidationError("Product name must be a non-empty string")

    # Validate numeric fields
    validated = {
        "product_name": product["product_name"],
        "current_price": validate_numeric(product["current_price"], "Current price", min_value=0),
        "bulk_price": validate_numeric(product["bulk_price"], "Bulk price", min_value=0),
        "on_hand": validate_numeric(product["on_hand"], "Cases on hand", min_value=0, integer_only=False),
        "annual_cases": validate_numeric(product["annual_cases"], "Cases per year", min_value=0),
        "bottles_per_case": validate_numeric(product["bottles_per_case"], "Bottles per case", min_value=1, allow_zero=False, integer_only=True)
    }

    # Validate optional bulk_quantity if present
    if "bulk_quantity" in product:
        validated["bulk_quantity"] = validate_numeric(
            product["bulk_quantity"], "Bulk quantity", min_value=0, integer_only=False
        )

    # Additional validation rules
    if validated["bulk_price"] > validated["current_price"]:
        raise ValidationError(f"Bulk price ({format_currency(validated['bulk_price'])}) cannot be higher than current price ({format_currency(validated['current_price'])})")

    return validated

def validate_calculator_params(params):
    """
    Validate parameters for the multi-product calculator.

    Parameters:
    - params: Dictionary containing calculator parameters

    Returns: Validated params with numeric fields converted to appropriate types.
    Raises ValidationError if validation fails.
    """
    # Handle both old and new parameter names for backward compatibility
    # Check for either smallDealCases or small_deal_minimum
    if 'smallDealCases' not in params and 'small_deal_minimum' not in params:
        raise ValidationError("Missing required field: smallDealCases or small_deal_minimum")

    # Check for either dealSizeCases or bulk_deal_minimum
    if 'dealSizeCases' not in params and 'bulk_deal_minimum' not in params:
        raise ValidationError("Missing required field: dealSizeCases or bulk_deal_minimum")

    # Check for either paymentTermsDays or payment_terms
    if 'paymentTermsDays' not in params and 'payment_terms' not in params:
        raise ValidationError("Missing required field: paymentTermsDays or payment_terms")

    # Validate numeric fields with backward compatibility
    small_deal_value = params.get('smallDealCases', params.get('small_deal_minimum'))
    bulk_deal_value = params.get('dealSizeCases', params.get('bulk_deal_minimum'))
    payment_terms_value = params.get('paymentTermsDays', params.get('payment_terms'))

    validated = {
        "small_deal_minimum": validate_numeric(small_deal_value, "Small deal minimum", min_value=0, integer_only=False),
        "bulk_deal_minimum": validate_numeric(bulk_deal_value, "Bulk deal minimum", min_value=0, integer_only=False),
        "payment_terms": validate_numeric(payment_terms_value, "Payment terms", min_value=0, integer_only=True),
        # Also include the new parameter names for consistency
        "smallDealCases": validate_numeric(small_deal_value, "Small deal cases", min_value=0, integer_only=False),
        "dealSizeCases": validate_numeric(bulk_deal_value, "Deal size cases", min_value=0, integer_only=False),
        "paymentTermsDays": validate_numeric(payment_terms_value, "Payment terms days", min_value=0, integer_only=True)
    }

    # Additional validation rules
    if validated["small_deal_minimum"] > validated["bulk_deal_minimum"]:
        raise ValidationError(f"Small deal minimum ({validated['small_deal_minimum']}) cannot be larger than bulk deal minimum ({validated['bulk_deal_minimum']})")

    # Optional fields
    if "min_days_stock" in params and params["min_days_stock"] is not None:
        validated["min_days_stock"] = validate_numeric(params["min_days_stock"], "Minimum days stock", min_value=0)

    return validated

def validate_bulk_quantities(products, bulk_deal_minimum):
    """
    Validate that the sum of bulk quantities meets the minimum requirement.

    Parameters:
    - products: List of product dictionaries
    - bulk_deal_minimum: Minimum required bulk quantity

    Raises ValidationError if validation fails.
    """
    if not products:
        raise ValidationError("No products provided")

    total_quantity = sum(p.get("bulk_quantity", 0) for p in products)

    if total_quantity < bulk_deal_minimum:
        raise ValidationError(
            f"Total bulk quantity ({total_quantity}) is less than the required minimum ({bulk_deal_minimum})"
        )

    return True
