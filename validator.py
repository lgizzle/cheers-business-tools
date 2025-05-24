"""
Input validation functions for the multi-product calculator.
Validates all inputs to ensure they meet requirements and constraints.
"""

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

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
        raise ValidationError(f"{name} cannot be negative, got {value}")

    # Check if zero is allowed
    if not allow_zero and numeric_value == 0:
        raise ValidationError(f"{name} cannot be zero")

    # Check minimum value
    if min_value is not None and numeric_value < min_value:
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
        "cases_on_hand", "cases_per_year", "bottles_per_case"
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
        "cases_on_hand": validate_numeric(product["cases_on_hand"], "Cases on hand", min_value=0, integer_only=False),
        "cases_per_year": validate_numeric(product["cases_per_year"], "Cases per year", min_value=0),
        "bottles_per_case": validate_numeric(product["bottles_per_case"], "Bottles per case", min_value=1, allow_zero=False, integer_only=True)
    }

    # Validate optional bulk_quantity if present
    if "bulk_quantity" in product:
        validated["bulk_quantity"] = validate_numeric(
            product["bulk_quantity"], "Bulk quantity", min_value=0, integer_only=False
        )

    # Additional validation rules
    if validated["bulk_price"] > validated["current_price"]:
        raise ValidationError(f"Bulk price (${validated['bulk_price']}) cannot be higher than current price (${validated['current_price']})")

    return validated

def validate_calculator_params(params):
    """
    Validate parameters for the multi-product calculator.

    Parameters:
    - params: Dictionary containing calculator parameters

    Returns: Validated params with numeric fields converted to appropriate types.
    Raises ValidationError if validation fails.
    """
    # Check required fields
    required_fields = ["small_deal_minimum", "bulk_deal_minimum", "payment_terms"]

    for field in required_fields:
        if field not in params:
            raise ValidationError(f"Missing required field: {field}")

    # Validate numeric fields
    validated = {
        "small_deal_minimum": validate_numeric(params["small_deal_minimum"], "Small deal minimum", min_value=0, integer_only=False),
        "bulk_deal_minimum": validate_numeric(params["bulk_deal_minimum"], "Bulk deal minimum", min_value=0, integer_only=False),
        "payment_terms": validate_numeric(params["payment_terms"], "Payment terms", min_value=0, integer_only=True)
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
