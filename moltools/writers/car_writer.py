"""
Module for writing CAR (Materials Studio Coordinate Archive) files.
"""

import logging

logger = logging.getLogger(__name__)

def write_car_file(output_filename, car_lines):
    """
    Writes CAR lines to a file and ensures the file ends with "end".
    
    Args:
        output_filename (str): Path to the output CAR file.
        car_lines (list): List of strings representing CAR file lines.
        
    Returns:
        bool: True if successful, False otherwise.
        
    Raises:
        IOError: If there's an error writing to the file.
    """
    try:
        with open(output_filename, "w") as f:
            for line in car_lines:
                f.write(line + "\n")
            
            # Make sure the file ends with "end"
            if not car_lines or car_lines[-1].strip().lower() != "end":
                f.write("\nend\n")
        
        logger.info(f"CAR file written successfully: {output_filename}")
        return True
    except IOError as e:
        logger.error(f"Error writing CAR file: {output_filename} - {str(e)}")
        raise