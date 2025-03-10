"""
Packmol tool integration.

This module provides integration with the Packmol tool for generating molecular packing arrangements.
It allows for parsing, updating, and generating Packmol input files as well as executing Packmol.
"""

import os
import json
import logging
import re
from typing import Optional, List, Dict, Any, Union

from .base import BaseExternalTool
from .utils import run_process

logger = logging.getLogger(__name__)

class PackmolTool(BaseExternalTool):
    """
    Integration with the Packmol tool.
    
    This class provides functionality to:
    1. Parse and update Packmol input files
    2. Generate Packmol input files from configuration dictionaries
    3. Execute Packmol for molecular packing
    
    Attributes:
        Inherits all attributes from BaseExternalTool
    """
    
    def _get_tool_name(self) -> str:
        """
        Get the name of the tool.
        
        Returns:
            str: Name of the tool
        """
        return "packmol"
    
    def validate_inputs(self, 
                       input_file: Optional[str] = None,
                       output_file: Optional[str] = None,
                       config_dict: Optional[Dict[str, Any]] = None, 
                       update_dict: Optional[Dict[str, Any]] = None,
                       **kwargs) -> None:
        """
        Validate input parameters for Packmol execution.
        
        Args:
            input_file (str, optional): Path to an existing Packmol input file.
            output_file (str, optional): Path where a generated input file will be written.
            config_dict (dict, optional): Configuration dictionary to use for generating input file.
            update_dict (dict, optional): Updates to apply to the configuration.
            **kwargs: Additional parameters.
            
        Raises:
            ValueError: If inputs are invalid.
        """
        # At least one of input_file or config_dict must be provided
        if input_file is None and config_dict is None:
            raise ValueError("Either input_file or config_dict must be provided")
            
        # If input_file is provided, it must exist
        if input_file is not None and not os.path.isfile(input_file):
            raise ValueError(f"Input file not found: {input_file}")
            
        # If update_dict is provided, it must be a dictionary
        if update_dict is not None and not isinstance(update_dict, dict):
            raise ValueError("update_dict must be a dictionary")
            
        # If config_dict is provided, it must be a dictionary
        if config_dict is not None and not isinstance(config_dict, dict):
            raise ValueError("config_dict must be a dictionary")
    
    def prepare_inputs(self, workspace_path: str,
                      input_file: Optional[str] = None,
                      output_file: Optional[str] = None,
                      config_dict: Optional[Dict[str, Any]] = None,
                      update_dict: Optional[Dict[str, Any]] = None,
                      **kwargs) -> Dict[str, Any]:
        """
        Prepare input files for Packmol in the workspace.
        
        Args:
            workspace_path (str): Path to the workspace directory.
            input_file (str, optional): Path to an existing Packmol input file.
            output_file (str, optional): Path where a generated input file will be written.
            config_dict (dict, optional): Configuration dictionary to use for generating input file.
            update_dict (dict, optional): Updates to apply to the configuration.
            **kwargs: Additional parameters.
            
        Returns:
            dict: Information about prepared inputs, including file paths.
        """
        logger.info(f"Preparing Packmol inputs in workspace: {workspace_path}")
        
        # Initialize the information dictionary
        input_info = {
            'workspace_path': workspace_path
        }
        
        # If input_file is provided, copy it to the workspace
        if input_file is not None:
            # Create a path for the input file in the workspace
            workspace_input_file = os.path.join(workspace_path, os.path.basename(input_file))
            
            # Copy the input file to the workspace
            logger.info(f"Copying input file to workspace: {workspace_input_file}")
            with open(input_file, 'rb') as src, open(workspace_input_file, 'wb') as dst:
                dst.write(src.read())
                
            input_info['input_file'] = workspace_input_file
            
            # Parse the input file to get the configuration dictionary
            config = self.parse_packmol_file(workspace_input_file)
            input_info['config'] = config
        else:
            # Use the provided config_dict
            input_info['config'] = config_dict
        
        # If update_dict is provided, update the configuration
        if update_dict is not None:
            logger.info("Applying updates to configuration")
            input_info['config'] = self.update_dict(input_info['config'], update_dict)
        
        # If output_file is provided, generate a new input file
        if output_file is not None or update_dict is not None:
            # If output_file is not provided, use a default name
            if output_file is None:
                output_file = "packmol.inp"
                
            # Create a path for the output file in the workspace
            workspace_output_file = os.path.join(workspace_path, os.path.basename(output_file))
            
            # Generate the input file
            logger.info(f"Generating input file in workspace: {workspace_output_file}")
            self.generate_packmol_file(input_info['config'], workspace_output_file)
            
            input_info['output_file'] = workspace_output_file
        
        # Find all structure files referenced in the configuration and copy them to the workspace
        structure_files = []
        for struct in input_info['config'].get('structures', []):
            structure_file = struct.get('structure_file')
            if structure_file and os.path.isfile(structure_file):
                # Copy the structure file to the workspace
                workspace_structure_file = os.path.join(workspace_path, os.path.basename(structure_file))
                logger.info(f"Copying structure file to workspace: {workspace_structure_file}")
                with open(structure_file, 'rb') as src, open(workspace_structure_file, 'wb') as dst:
                    dst.write(src.read())
                structure_files.append(workspace_structure_file)
                
                # Update the structure file path in the configuration
                struct['structure_file'] = os.path.basename(structure_file)
        
        input_info['structure_files'] = structure_files
        return input_info
    
    def build_command(self, input_info: Dict[str, Any], **kwargs) -> List[str]:
        """
        Build the Packmol command to be executed.
        
        Args:
            input_info (dict): Information from prepare_inputs.
            **kwargs: Additional parameters.
            
        Returns:
            list: Command list to be executed.
        """
        # Determine which input file to use
        if 'output_file' in input_info:
            # If an output file was generated, use it
            input_file = input_info['output_file']
        elif 'input_file' in input_info:
            # Otherwise, use the original input file
            input_file = input_info['input_file']
        else:
            # If no input file is available, generate one from the configuration
            input_file = os.path.join(input_info['workspace_path'], "packmol.inp")
            self.generate_packmol_file(input_info['config'], input_file)
            input_info['output_file'] = input_file
        
        # Build the command
        cmd = [self.executable_path]
        
        # Add the input file parameter
        # Packmol accepts input file with -i flag
        cmd.extend(["-i", input_file])
        
        # Store the input file for reference
        input_info['final_input_file'] = input_file
        
        # Add timeout parameter if provided
        if 'timeout' in kwargs:
            cmd.extend(["-t", str(kwargs['timeout'])])
        
        logger.info(f"Using Packmol input file: {input_file}")
        
        return cmd
    
    def process_output(self, return_code: int, stdout: str, stderr: str, 
                      input_info: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Process the Packmol output.
        
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
            error_msg = f"Packmol failed with return code {return_code}. "
            
            if stdout.strip():
                logger.error(f"Packmol stdout: {stdout.strip()}")
            if stderr.strip():
                logger.error(f"Packmol stderr: {stderr.strip()}")
                
            raise RuntimeError(error_msg)
        
        # Get the workspace path
        workspace_path = input_info['workspace_path']
        
        # Find the output file (referenced in the config or stdout)
        output_file = None
        for line in stdout.splitlines():
            if "Output file:" in line:
                output_file = line.split(":", 1)[1].strip()
                # If the output file doesn't have an absolute path, assume it's in the workspace
                if not os.path.isabs(output_file):
                    output_file = os.path.join(workspace_path, output_file)
                break
        
        # If no output file was found in stdout, check the configuration
        if not output_file:
            for key, tokens in input_info['config'].get('global', {}).items():
                if key.lower() == 'output':
                    output_file = ' '.join(tokens)
                    # If the output file doesn't have an absolute path, assume it's in the workspace
                    if not os.path.isabs(output_file):
                        output_file = os.path.join(workspace_path, output_file)
                    break
        
        # Track any output files found with the workspace manager
        output_files = []
        if output_file and os.path.isfile(output_file):
            output_files.append(output_file)
            self.workspace_manager.track_files(output_files)
        
        # Create result dictionary
        result = {
            'return_code': return_code,
            'stdout': stdout,
            'stderr': stderr,
            'output_files': output_files,
            'output_file': output_file,
            'config': input_info['config']
        }
        
        # Log success
        logger.info(f"Packmol completed successfully. Generated {len(output_files)} output files.")
        
        return result
    
    def parse_packmol_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse an existing Packmol input file into a structured dictionary.
        
        Args:
            file_path (str): Path to the existing Packmol input file.
        
        Returns:
            dict: The parsed configuration.
        
        Raises:
            Exception: If the file cannot be read or if there is a parsing error.
        """
        config = {"global": {}, "structures": []}
        try:
            with open(file_path, "r") as f:
                lines = f.readlines()
        except Exception as e:
            logger.error(f"Error reading file '{file_path}': {e}")
            raise

        # Remove comments (lines starting with #) and blank lines.
        lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]

        i = 0
        # Read global lines until the first "structure" keyword.
        while i < len(lines):
            line = lines[i]
            if re.match(r"^structure\s+", line, re.IGNORECASE):
                break
            tokens = line.split()
            if tokens:
                key = tokens[0]
                config["global"][key] = tokens[1:]
            i += 1

        # Parse structure blocks.
        while i < len(lines):
            line = lines[i]
            if re.match(r"^structure\s+", line, re.IGNORECASE):
                tokens = line.split()
                if len(tokens) < 2:
                    raise ValueError(f"Malformed structure line at line {i+1}: '{line}'")
                struct_block = {
                    "structure_file": tokens[1],
                    "properties": {},
                    "constraints": [],
                    "others": []
                }
                i += 1
                # Read block until "end structure".
                while i < len(lines):
                    inner_line = lines[i]
                    if inner_line.lower() == "end structure":
                        break
                    # Handle nested "atoms" block.
                    if inner_line.lower().startswith("atoms"):
                        atoms_data = {"atoms": inner_line.split()[1:], "constraints": []}
                        i += 1
                        while i < len(lines):
                            nested_line = lines[i]
                            if nested_line.lower() == "end atoms":
                                break
                            atoms_data["constraints"].append(nested_line)
                            i += 1
                        struct_block["constraints"].append({"keyword": "atoms", "data": atoms_data})
                    else:
                        tokens_inner = inner_line.split()
                        if tokens_inner:
                            key_inner = tokens_inner[0]
                            # Handle compound keywords such as "inside cube" or "outside sphere".
                            if key_inner.lower() in ["inside", "outside"]:
                                if len(tokens_inner) >= 2:
                                    constraint = {
                                        "keyword": key_inner,
                                        "block": tokens_inner[1],
                                        "params": tokens_inner[2:]
                                    }
                                    struct_block["constraints"].append(constraint)
                                else:
                                    struct_block["others"].append(inner_line)
                            else:
                                # Treat as a property line.
                                struct_block["properties"][key_inner] = tokens_inner[1:]
                        else:
                            struct_block["others"].append(inner_line)
                    i += 1
                config["structures"].append(struct_block)
            i += 1

        logger.info(f"Parsed Packmol input file '{file_path}' successfully.")
        return config
    
    def generate_packmol_file(self, config: Dict[str, Any], output_file: str) -> None:
        """
        Generate a Packmol input file from a configuration dictionary.
        
        Args:
            config (dict): The configuration dictionary.
            output_file (str): The path where the generated input file will be written.
        
        Raises:
            Exception: If writing to the file fails.
        """
        try:
            with open(output_file, "w") as f:
                # Write global options.
                for key, tokens in config.get("global", {}).items():
                    f.write(key + " " + " ".join(tokens) + "\n")
                f.write("\n")
                # Write each structure block.
                for struct in config.get("structures", []):
                    f.write("structure " + struct.get("structure_file", "") + "\n")
                    # Write properties.
                    for key, tokens in struct.get("properties", {}).items():
                        f.write("  " + key + " " + " ".join(tokens) + "\n")
                    # Write constraints.
                    for constraint in struct.get("constraints", []):
                        if constraint["keyword"].lower() == "atoms":
                            data = constraint["data"]
                            f.write("  atoms " + " ".join(data.get("atoms", [])) + "\n")
                            for nested in data.get("constraints", []):
                                f.write("    " + nested + "\n")
                            f.write("  end atoms\n")
                        else:
                            if "block" in constraint:
                                f.write("  " + constraint["keyword"] + " " +
                                        constraint["block"] + " " +
                                        " ".join(constraint.get("params", [])) + "\n")
                            else:
                                f.write("  " + constraint["keyword"] + " " +
                                        " ".join(constraint.get("params", [])) + "\n")
                    # Write any other unparsed lines.
                    for other in struct.get("others", []):
                        f.write("  " + other + "\n")
                    f.write("end structure\n\n")
            logger.info(f"Generated Packmol input file '{output_file}' successfully.")
        except Exception as e:
            logger.error(f"Error generating Packmol input file: {e}")
            raise
    
    def update_dict(self, orig: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively update dictionary 'orig' with values from 'updates'.
        
        Args:
            orig (dict): The original dictionary.
            updates (dict): The updates to merge into 'orig'.
        
        Returns:
            dict: The updated dictionary.
        """
        for key, value in updates.items():
            if key in orig and isinstance(orig[key], dict) and isinstance(value, dict):
                self.update_dict(orig[key], value)
            else:
                orig[key] = value
        return orig