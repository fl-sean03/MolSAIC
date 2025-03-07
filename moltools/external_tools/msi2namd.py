"""
MSI2NAMD tool integration.

This module provides integration with the MSI2NAMD tool for converting
Material Studio files (CAR/MDF) to NAMD format (PSF/PDB).
"""

import os
import logging
import tempfile
import glob
from typing import Optional, List, Dict, Any, Union, Tuple

from moltools.models.system import System
from .base import BaseExternalTool
from .utils import create_temp_file

logger = logging.getLogger(__name__)

class MSI2NAMDTool(BaseExternalTool):
    """
    Integration with the MSI2NAMD tool.
    
    This class provides functionality to convert Material Studio files
    (CAR/MDF) to NAMD format (PSF/PDB) using the MSI2NAMD external tool.
    """
    
    def _get_tool_name(self) -> str:
        """
        Get the name of the tool.
        
        Returns:
            str: Name of the tool
        """
        return "msi2namd"
    
    def validate_inputs(self, 
                       system: Optional[System] = None,
                       car_file: Optional[str] = None,
                       mdf_file: Optional[str] = None,
                       residue_name: Optional[str] = None,
                       parameter_file: Optional[str] = None,
                       **kwargs) -> None:
        """
        Validate input parameters for MSI2NAMD.
        
        Args:
            system (System, optional): The molecular system to convert.
            car_file (str, optional): Path to CAR file (if system not provided).
            mdf_file (str, optional): Path to MDF file (if system not provided).
            residue_name (str, optional): Residue name for the PDB file.
            parameter_file (str, optional): Path to parameter file.
            **kwargs: Additional parameters.
            
        Raises:
            ValueError: If inputs are invalid.
        """
        # Validate input mode (system object or input files)
        if system is None and (car_file is None or mdf_file is None):
            raise ValueError("Either system object or both car_file and mdf_file must be provided")
            
        # If files are provided, validate they exist
        if system is None:
            if not os.path.isfile(car_file):
                raise ValueError(f"CAR file not found: {car_file}")
            if not os.path.isfile(mdf_file):
                raise ValueError(f"MDF file not found: {mdf_file}")
        
        # Parameter file is REQUIRED for MSI2NAMD
        if parameter_file is None:
            raise ValueError("Parameter file is required for MSI2NAMD conversion")
        
        # Validate parameter file exists
        if not os.path.isfile(parameter_file):
            raise ValueError(f"Parameter file not found: {parameter_file}")
    
    def prepare_inputs(self, workspace_path: str,
                      system: Optional[System] = None,
                      car_file: Optional[str] = None,
                      mdf_file: Optional[str] = None,
                      residue_name: Optional[str] = None,
                      parameter_file: Optional[str] = None,
                      base_name: str = "system",
                      **kwargs) -> Dict[str, Any]:
        """
        Prepare input files for MSI2NAMD in the workspace.
        
        Args:
            workspace_path (str): Path to the workspace directory.
            system (System, optional): The molecular system to convert.
            car_file (str, optional): Path to CAR file (if system not provided).
            mdf_file (str, optional): Path to MDF file (if system not provided).
            residue_name (str, optional): Residue name for PDB file.
            parameter_file (str, optional): Path to parameter file.
            base_name (str, optional): Base name for output files. Default is "system".
            **kwargs: Additional parameters.
            
        Returns:
            dict: Information about prepared inputs, including file paths.
        """
        logger.info(f"Preparing MSI2NAMD inputs in workspace: {workspace_path}")
        
        # Create temp CAR/MDF files if system object is provided
        if system:
            # Generate temp file paths in the workspace
            temp_car = os.path.join(workspace_path, f"{base_name}.car")
            temp_mdf = os.path.join(workspace_path, f"{base_name}.mdf")
            
            # Save system to temporary files
            system.to_files(temp_car, temp_mdf, base_name=residue_name or "MOL")
            
            car_file = temp_car
            mdf_file = temp_mdf
            
            logger.debug(f"Created temporary CAR/MDF files from system object: {temp_car}, {temp_mdf}")
        else:
            # MSI2NAMD requires CAR and MDF files to have the same base name
            # Get base name (without extension) from the CAR file
            base_filename = os.path.splitext(os.path.basename(car_file))[0]
            
            # Ensure the files have matching names in the workspace
            temp_car = os.path.join(workspace_path, f"{base_filename}.car")
            temp_mdf = os.path.join(workspace_path, f"{base_filename}.mdf")
            
            # Copy CAR file to workspace
            logger.info(f"Copying CAR file to workspace: {temp_car}")
            with open(car_file, 'rb') as src, open(temp_car, 'wb') as dst:
                dst.write(src.read())
                
            # Copy MDF file to workspace
            logger.info(f"Copying MDF file to workspace: {temp_mdf}")
            with open(mdf_file, 'rb') as src, open(temp_mdf, 'wb') as dst:
                dst.write(src.read())
            
            logger.info(f"Input files prepared in workspace with base name: {base_filename}")
        
        # Copy parameter file (required)
        if not parameter_file:
            raise ValueError("Parameter file is required")
            
        # Copy parameter file to workspace
        temp_param = os.path.join(workspace_path, os.path.basename(parameter_file))
        
        # Copy the parameter file
        logger.info(f"Copying parameter file to workspace: {temp_param}")
        with open(parameter_file, 'rb') as src, open(temp_param, 'wb') as dst:
            dst.write(src.read())
        
        logger.info(f"Parameter file prepared in workspace: {os.path.basename(parameter_file)}")
        
        # Create input information dictionary
        input_info = {
            'car_file': temp_car,
            'mdf_file': temp_mdf,
            'parameter_file': temp_param,
            'residue_name': residue_name,
            'base_name': base_name,
            'workspace_path': workspace_path
        }
        
        return input_info
    
    def build_command(self, input_info: Dict[str, Any], **kwargs) -> List[str]:
        """
        Build the MSI2NAMD command to be executed.
        
        Args:
            input_info (dict): Information from prepare_inputs.
            **kwargs: Additional parameters.
            
        Returns:
            list: Command list to be executed.
        """
        # Extract file paths from input_info
        car_file = input_info['car_file']
        mdf_file = input_info['mdf_file']
        parameter_file = input_info.get('parameter_file')
        residue_name = input_info.get('residue_name') or "MOL"
        
        # Get the base name for input files (without extension)
        # Both car_file and mdf_file should have the same base name
        input_base = os.path.splitext(os.path.basename(car_file))[0]
        
        # Get output name
        output_name = kwargs.get('output_name', input_base)
        
        # Validate residue name (must be <= 4 characters)
        if len(residue_name) > 4:
            logger.warning(f"Residue name '{residue_name}' is too long (> 4 chars), truncating to '{residue_name[:4]}'")
            residue_name = residue_name[:4]
        
        # Build command according to proper format:
        # msi2namd.exe -file <INPUT_FILE> -res <RESIDUE_NAME> -classII <PARAMETER_FILE> -output <OUTPUT_NAME>
        cmd = [self.executable_path]
        
        # Add input file base name (no extension)
        cmd.extend(["-file", input_base])
        
        # Add residue name
        cmd.extend(["-res", residue_name])
        
        # Parameter file is required
        if not parameter_file:
            raise ValueError("Parameter file is required for MSI2NAMD conversion")
        
        # Add parameter file
        parameter_filename = os.path.basename(parameter_file)
        cmd.extend(["-classII", parameter_filename])
        logger.info(f"Using parameter file: {parameter_filename}")
        
        # Add output name
        cmd.extend(["-output", output_name])
        
        # Add charge groups flag if specified
        if kwargs.get('charge_groups'):
            cmd.extend(["-cg"])
        
        return cmd
    
    def process_output(self, return_code: int, stdout: str, stderr: str, 
                      input_info: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Process the MSI2NAMD output.
        
        Args:
            return_code (int): Process return code.
            stdout (str): Process standard output.
            stderr (str): Process standard error.
            input_info (dict): Information from prepare_inputs.
            **kwargs: Additional parameters.
            
        Returns:
            dict: Processed output information, including paths to output files.
            
        Raises:
            RuntimeError: If the tool execution failed.
        """
        # Check if the execution was successful
        if return_code != 0:
            workspace_path = input_info['workspace_path']
            
            # Keep error message concise - the details are in the log files
            error_msg = f"MSI2NAMD failed with return code {return_code}. "
            error_msg += f"Check detailed logs in the workspace for troubleshooting: {workspace_path}"
            
            # Log the error with more details for debugging 
            logger.error(f"MSI2NAMD execution failed (code {return_code})")
            
            if stdout.strip():
                logger.debug(f"MSI2NAMD stdout: {stdout.strip()}")
            if stderr.strip():
                logger.debug(f"MSI2NAMD stderr: {stderr.strip()}")
                
            raise RuntimeError(error_msg)
        
        # Get paths to output files
        workspace_path = input_info['workspace_path']
        output_name = kwargs.get('output_name', os.path.splitext(os.path.basename(input_info['car_file']))[0])
        
        # Expected output files with the specified output name
        pdb_file = os.path.join(workspace_path, f"{output_name}.pdb")
        psf_file = os.path.join(workspace_path, f"{output_name}.psf")
        
        # Define expected output file patterns (also look for any PDB/PSF files as fallback)
        output_patterns = [
            os.path.join(workspace_path, f"{output_name}.pdb"),
            os.path.join(workspace_path, f"{output_name}.psf"),
            os.path.join(workspace_path, "*.pdb"),
            os.path.join(workspace_path, "*.psf"),
            os.path.join(workspace_path, "*.params")
        ]
        
        # Find all output files
        output_files = []
        for pattern in output_patterns:
            output_files.extend(glob.glob(pattern))
        
        # Track these files with the workspace manager
        self.workspace_manager.track_files(output_files)
        
        # Create result dictionary
        result = {
            'return_code': return_code,
            'stdout': stdout,
            'stderr': stderr,
            'output_files': output_files,
            'pdb_file': next((f for f in output_files if f.endswith('.pdb')), None),
            'psf_file': next((f for f in output_files if f.endswith('.psf')), None),
            'namd_file': next((f for f in output_files if f.endswith('.namd')), None),
            'param_file': next((f for f in output_files if f.endswith('.params')), None)
        }
        
        # Log success
        logger.info(f"MSI2NAMD completed successfully. Generated {len(output_files)} output files.")
        for key in ['pdb_file', 'psf_file', 'namd_file', 'param_file']:
            if result[key]:
                logger.debug(f"{key}: {result[key]}")
        
        return result