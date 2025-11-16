"""
JSON Serialization Utilities
============================

Utility functions for safe JSON serialization and deserialization with support for numpy types and custom objects.

Features:
- Custom JSON encoder for numpy types
- Complex number support
- Custom object serialization
- Data cleaning functions
- JSON serializability validation
- Comprehensive type handling

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

import json
import numpy as np
from typing import Any, Dict, List, Union
import logging

logger = logging.getLogger(__name__)


class NumpyJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles numpy types and other non-serializable objects.

    This encoder provides comprehensive support for:
    - All numpy numeric types (int8, int16, int32, int64, float16, float32, float64, etc.)
    - Numpy arrays and matrices
    - Complex numbers
    - Sets, tuples, and other Python collections
    - Custom objects with __dict__ attributes
    """

    def default(self, obj: Any) -> Any:
        """
        Convert non-serializable objects to JSON-serializable format.

        Args:
            obj: Object to serialize

        Returns:
            JSON-serializable representation of the object
        """
        try:
            # Handle numpy types
            if hasattr(obj, 'dtype'):
                # Handle numpy arrays
                if hasattr(obj, 'tolist'):
                    return {
                        '_type': 'numpy_array',
                        'data': obj.tolist(),
                        'dtype': str(obj.dtype),
                        'shape': obj.shape
                    }
                # Handle single numpy values
                elif hasattr(obj, 'item'):
                    return obj.item()
                else:
                    return str(obj)

            # Handle numpy scalar types explicitly
            if isinstance(obj, (np.integer, np.signedinteger, np.unsignedinteger)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float16, np.float32, np.float64)):
                return float(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, np.complexfloating):
                return {'real': float(obj.real), 'imag': float(obj.imag), '_type': 'complex'}

            # Handle Python built-in types that aren't JSON serializable
            elif isinstance(obj, set):
                return {'_type': 'set', 'data': list(obj)}
            elif isinstance(obj, tuple):
                return {'_type': 'tuple', 'data': list(obj)}
            elif isinstance(obj, complex):
                return {'real': obj.real, 'imag': obj.imag, '_type': 'complex'}
            elif isinstance(obj, bytes):
                try:
                    return obj.decode('utf-8')
                except UnicodeDecodeError:
                    return {'_type': 'bytes', 'data': obj.hex()}
            elif isinstance(obj, range):
                return {'_type': 'range', 'start': obj.start, 'stop': obj.stop, 'step': obj.step}

            # Handle objects with __dict__ (custom classes)
            elif hasattr(obj, '__dict__'):
                return {
                    '_type': 'object',
                    'class': obj.__class__.__name__,
                    'data': obj.__dict__
                }

            # Handle callable objects
            elif callable(obj):
                return f"<callable: {obj.__name__ if hasattr(obj, '__name__') else str(obj)}>"

            # Final fallback - convert to string
            else:
                return str(obj)

        except Exception as e:
            logger.warning(f"Failed to serialize object of type {type(obj).__name__}: {e}")
            return f"<unserializable: {type(obj).__name__}>"


def safe_json_dumps(data: Any, **kwargs) -> str:
    """
    Safely serialize data to JSON string with comprehensive type support.

    Args:
        data: Data to serialize
        **kwargs: Additional arguments passed to json.dumps

    Returns:
        JSON string representation of the data
    """
    # Set default arguments for better formatting
    default_kwargs = {
        'indent': 2,
        'cls': NumpyJSONEncoder,
        'ensure_ascii': False,
        'sort_keys': True
    }
    default_kwargs.update(kwargs)

    try:
        return json.dumps(data, **default_kwargs)
    except Exception as e:
        logger.error(f"JSON serialization failed: {e}")
        # Fallback: try with minimal options
        try:
            return json.dumps(data, cls=NumpyJSONEncoder)
        except Exception as e2:
            logger.error(f"Fallback JSON serialization also failed: {e2}")
            raise


def safe_json_loads(json_str: str, **kwargs) -> Any:
    """
    Safely deserialize JSON string with support for custom types.

    Args:
        json_str: JSON string to deserialize
        **kwargs: Additional arguments passed to json.loads

    Returns:
        Deserialized data with custom types restored where possible
    """
    try:
        data = json.loads(json_str, **kwargs)
        return _restore_custom_types(data)
    except Exception as e:
        logger.error(f"JSON deserialization failed: {e}")
        raise


def _restore_custom_types(obj: Any) -> Any:
    """
    Recursively restore custom types from deserialized JSON data.

    Args:
        obj: Deserialized JSON object

    Returns:
        Object with custom types restored where possible
    """
    if isinstance(obj, dict):
        # Check if this is a custom type marker
        if '_type' in obj:
            obj_type = obj['_type']

            if obj_type == 'numpy_array':
                try:
                    import numpy as np
                    return np.array(obj['data'], dtype=obj['dtype']).reshape(obj['shape'])
                except Exception as e:
                    logger.warning(f"Failed to restore numpy array: {e}")
                    return obj['data']

            elif obj_type == 'set':
                return set(_restore_custom_types(obj['data']))

            elif obj_type == 'tuple':
                return tuple(_restore_custom_types(obj['data']))

            elif obj_type == 'complex':
                return complex(obj['real'], obj['imag'])

            elif obj_type == 'bytes':
                try:
                    return bytes.fromhex(obj['data'])
                except Exception:
                    return obj['data']

            elif obj_type == 'range':
                return range(obj['start'], obj['stop'], obj['step'])

            elif obj_type == 'object':
                # For custom objects, just return the data dict
                # Full object restoration would require importing the class
                return _restore_custom_types(obj['data'])

        # Recursively process dictionary values
        return {key: _restore_custom_types(value) for key, value in obj.items()}

    elif isinstance(obj, list):
        # Recursively process list items
        return [_restore_custom_types(item) for item in obj]

    else:
        # Return primitive types as-is
        return obj


def clean_data_for_json(data: Any) -> Any:
    """
    Pre-process data to remove or convert problematic types before JSON serialization.

    This function is useful when you want to clean data before serialization
    rather than handling it in the encoder.

    Args:
        data: Data to clean

    Returns:
        Cleaned data ready for JSON serialization
    """
    if isinstance(data, dict):
        return {key: clean_data_for_json(value) for key, value in data.items()}
    elif isinstance(data, (list, tuple)):
        return [clean_data_for_json(item) for item in data]
    elif hasattr(data, 'dtype'):
        # Handle numpy types
        if hasattr(data, 'tolist'):
            return data.tolist()
        elif hasattr(data, 'item'):
            return data.item()
        else:
            return str(data)
    elif isinstance(data, (np.integer, np.signedinteger, np.unsignedinteger)):
        return int(data)
    elif isinstance(data, (np.floating, np.float16, np.float32, np.float64)):
        return float(data)
    elif isinstance(data, np.bool_):
        return bool(data)
    elif isinstance(data, set):
        return list(data)
    elif isinstance(data, complex):
        return {'real': data.real, 'imag': data.imag}
    elif callable(data):
        return f"<callable: {data.__name__ if hasattr(data, '__name__') else str(data)}>"
    elif hasattr(data, '__dataclass_fields__'):
        # Handle dataclass objects by converting to dict
        return {field: clean_data_for_json(getattr(data, field)) for field in data.__dataclass_fields__}
    elif hasattr(data, '__dict__'):
        # Handle custom objects with __dict__ attribute
        return {key: clean_data_for_json(value) for key, value in data.__dict__.items() if not key.startswith('_')}
    else:
        return data


def validate_json_serializable(data: Any, path: str = "root") -> List[str]:
    """
    Validate that data is JSON serializable and return list of problematic paths.

    Args:
        data: Data to validate
        path: Current path in the data structure (for error reporting)

    Returns:
        List of paths where serialization issues were found
    """
    issues = []

    try:
        json.dumps(data)
        return issues  # No issues found
    except TypeError as e:
        # Try to identify the specific problematic object
        if isinstance(data, dict):
            for key, value in data.items():
                issues.extend(validate_json_serializable(value, f"{path}.{key}"))
        elif isinstance(data, (list, tuple)):
            for i, item in enumerate(data):
                issues.extend(validate_json_serializable(item, f"{path}[{i}]"))
        else:
            issues.append(f"{path}: {type(data).__name__} - {str(e)}")

    return issues


# Convenience functions for backward compatibility
def numpy_json_dumps(data: Any, **kwargs) -> str:
    """Alias for safe_json_dumps for backward compatibility."""
    return safe_json_dumps(data, **kwargs)


def numpy_json_loads(json_str: str, **kwargs) -> Any:
    """Alias for safe_json_loads for backward compatibility."""
    return safe_json_loads(json_str, **kwargs)