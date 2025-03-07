# Utility functions for molecular tools

def is_float(value):
    """Check if a value can be converted to float.
    
    Args:
        value: The value to check
        
    Returns:
        bool: True if the value can be converted to float, False otherwise
    """
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False
        
def validate_coordinates(x, y, z):
    """Validate that coordinates are numeric.
    
    Args:
        x: X coordinate
        y: Y coordinate
        z: Z coordinate
        
    Returns:
        bool: True if all coordinates are numeric, False otherwise
    """
    return all(is_float(coord) for coord in (x, y, z))
