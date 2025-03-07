"""
Module for writing MDF (Materials Studio Molecular Data Format) files.
"""

import logging

logger = logging.getLogger(__name__)

def write_mdf_file(output_filename, mdf_lines):
    """
    Writes MDF lines to a file.
    
    Args:
        output_filename (str): Path to the output MDF file.
        mdf_lines (list): List of strings representing MDF file lines.
        
    Returns:
        bool: True if successful, False otherwise.
        
    Raises:
        IOError: If there's an error writing to the file.
    """
    try:
        with open(output_filename, "w") as f:
            for line in mdf_lines:
                f.write(line + "\n")
        
        logger.info(f"MDF file written successfully: {output_filename}")
        return True
    except IOError as e:
        logger.error(f"Error writing MDF file: {output_filename} - {str(e)}")
        raise