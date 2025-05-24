"""
API utilities for data validation and conversion.
Provides reusable functions for handling API data across different calculators.
"""

import numpy as np
import json

def validate_required_fields(data, required_fields):
    """Raise ValueError if any required field is missing or empty in data."""
    missing = [f for f in required_fields if f not in data or data[f] in (None, '', [])]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")


def validate_numeric(value, name, min_value=None, max_value=None):
    """
    Validate that a value is numeric and within a specified range.

    Args:
        value: The value to validate
        name: Name of the parameter (for error messages)
        min_value: Minimum allowed value (optional)
        max_value: Maximum allowed value (optional)

    Returns:
        float: The validated numeric value

    Raises:
        ValueError: If validation fails
    """
    # Convert to float
    try:
        numeric_value = float(value)
    except (ValueError, TypeError):
        raise ValueError(f"{name} must be a number")

    # Check minimum
    if min_value is not None and numeric_value < min_value:
        raise ValueError(f"{name} must be at least {min_value}")

    # Check maximum
    if max_value is not None and numeric_value > max_value:
        raise ValueError(f"{name} must be at most {max_value}")

    return numeric_value

def convert_numpy_types(obj):
    """
    Convert numpy types to standard Python types for JSON serialization.

    Args:
        obj: Object that may contain numpy types

    Returns:
        Object with numpy types converted to standard Python types
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(i) for i in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(i) for i in obj)
    else:
        return obj

class NumpyJSONEncoder(json.JSONEncoder):
    """
    JSON encoder that handles numpy types.
    Usage: json.dumps(data, cls=NumpyJSONEncoder)
    """
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyJSONEncoder, self).default(obj)

def validate_request_data(data, required_fields=None):
    """
    Validate that required fields are present in the request data.

    Args:
        data: Request data to validate
        required_fields: List of required field names

    Returns:
        bool: True if validation passes

    Raises:
        ValueError: If required fields are missing
    """
    if required_fields is None:
        return True

    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)

    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

    return True
