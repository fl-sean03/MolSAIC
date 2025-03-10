"""
Command-line interface module for MolTools.
Provides entry point for command-line operations.
"""

import argparse
import sys
import logging
import json
import os
from datetime import datetime

from moltools import config
from moltools.transformers import grid, update_ff, update_charges
from moltools.pipeline import MolecularPipeline

logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for the CLI.
    """
    # Set up logging right away to capture all logs
    config.setup_logging()
    
    parser = argparse.ArgumentParser(
        description="MolTools - Molecular Data Processing Tools",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    
    # Global options
    parser.add_argument("--log-level", 
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        default=config.DEFAULT_LOG_LEVEL,
                        help="Set logging level")
    
    # Add global options for all subcommands
    parser.add_argument("--file-mode", action="store_true", 
                      help="[DEPRECATED] Use legacy file-based approach instead of object-based pipeline")
    parser.add_argument("--debug-output", action="store_true",
                      help="Generate intermediate files for debugging (only available in object-based mode)")
    parser.add_argument("--debug-prefix", default="debug_",
                      help="Prefix for debug output files (only with --debug-output)")
    
    # Split into two separate flags for clarity
    keep_group = parser.add_mutually_exclusive_group()
    keep_group.add_argument("--keep", action="store_true",
                      help="Keep all artifacts after completion (logs and workspaces)")
    keep_group.add_argument("--keep-logs", action="store_true",
                      help="Keep only logs after completion (cleanup workspaces)")
    
    # Subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")
    
    # Packmol subcommand
    packmol_parser = subparsers.add_parser("packmol", help="Work with Packmol input files")
    packmol_parser.add_argument("--input-file", required=True, help="Path to an existing Packmol input file")
    packmol_parser.add_argument("--output-file", help="Path to write the generated Packmol input file")
    packmol_parser.add_argument("--update-file", help="Path to a JSON file with updates to apply")
    packmol_parser.add_argument("--execute", action="store_true", help="Execute Packmol after processing")
    packmol_parser.add_argument("--print-json", action="store_true", help="Print configuration as JSON and exit")
    
    # Grid subcommand
    grid_parser = subparsers.add_parser("grid", help="Generate a grid of replicated molecules")
    grid_parser.add_argument("--mdf", required=True, help="Input MDF file")
    grid_parser.add_argument("--car", required=True, help="Input CAR file")
    grid_parser.add_argument("--output-mdf", default="grid_box.mdf", help="Output MDF file")
    grid_parser.add_argument("--output-car", default="grid_box.car", help="Output CAR file")
    grid_parser.add_argument("--grid", type=int, default=config.DEFAULT_GRID_SIZE, 
                           help=f"Grid dimension along each axis (default: {config.DEFAULT_GRID_SIZE})")
    grid_parser.add_argument("--gap", type=float, default=config.DEFAULT_GAP, 
                           help=f"Gap (in Angstroms) between molecules (default: {config.DEFAULT_GAP})")
    grid_parser.add_argument("--base-name", default="MOL", 
                           help="Base molecule name for output molecules")
    
    # Update force-field subcommand
    update_ff_parser = subparsers.add_parser("update-ff", 
                                           help="Update force-field types based on a mapping")
    update_ff_parser.add_argument("--mdf", help="Input MDF file")
    update_ff_parser.add_argument("--car", help="Input CAR file")
    update_ff_parser.add_argument("--output-mdf", help="Output MDF file")
    update_ff_parser.add_argument("--output-car", help="Output CAR file")
    update_ff_parser.add_argument("--mapping", required=True, help="JSON mapping file")
    
    # Update charges subcommand
    update_charges_parser = subparsers.add_parser("update-charges", 
                                               help="Update atomic charges based on a mapping")
    update_charges_parser.add_argument("--mdf", help="Input MDF file")
    update_charges_parser.add_argument("--car", help="Input CAR file")
    update_charges_parser.add_argument("--output-mdf", help="Output MDF file")
    update_charges_parser.add_argument("--output-car", help="Output CAR file")
    update_charges_parser.add_argument("--mapping", required=True, help="JSON mapping file")
    
    # Convert to NAMD subcommand (object-mode only)
    namd_parser = subparsers.add_parser("convert-to-namd", 
                                      help="Convert files to NAMD format (PDB/PSF) using MSI2NAMD")
    namd_parser.add_argument("--mdf", required=True, help="Input MDF file")
    namd_parser.add_argument("--car", required=True, help="Input CAR file")
    namd_parser.add_argument("--output-dir", default="namd_output", 
                         help="Output directory for NAMD files (default: namd_output)")
    namd_parser.add_argument("--residue-name", help="Residue name for NAMD files (max 4 characters)")
    namd_parser.add_argument("--parameter-file", required=True, 
                         help="Parameter file for MSI2NAMD conversion (REQUIRED)")
    namd_parser.add_argument("--charge-groups", action="store_true", 
                         help="Include charge groups in conversion (-cg flag)")
    
    args = parser.parse_args()
    
    # Update logging with the user-specified level
    config.setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Create a new workspace for this session in the current directory
    try:
        # First try to get the current directory and print it for debugging
        current_dir = os.getcwd()
        logger.info(f"Current working directory: {current_dir}")
        
        # Check if the directory exists and is writable
        if not os.access(current_dir, os.W_OK):
            logger.error(f"Current directory is not writable: {current_dir}")
            logger.error("Please run the command from a writable directory")
            return 1
            
        # Create workspace directory if it doesn't exist yet
        workspace_dir = os.path.join(current_dir, ".moltools_workspace")
        logger.info(f"Creating workspace directory: {workspace_dir}")
        
        # Try to create the directory
        os.makedirs(workspace_dir, exist_ok=True)
        
        # Verify the directory was created
        if not os.path.exists(workspace_dir):
            logger.error(f"Failed to create workspace directory: {workspace_dir}")
            return 1
            
        # Explicitly set the workspace path
        os.environ['MOLTOOLS_WORKSPACE_PATH'] = workspace_dir
        
        # Create the workspace
        from moltools.workspace import create_global_workspace
        workspace_path = create_global_workspace("session_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
        logger.debug(f"Created session workspace: {workspace_path}")
        logger.info(f"All logs will be saved to: {os.path.join(workspace_path, 'moltools.log')}")
    except Exception as e:
        logger.error(f"Failed to set up workspace: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        
        # Add more detailed troubleshooting info
        if isinstance(e, FileNotFoundError):
            logger.error("Directory doesn't exist. Check if you're running from a valid directory.")
        elif isinstance(e, PermissionError):
            logger.error("Permission denied. Check if you have write permissions to the current directory.")
        else:
            logger.error("Please run the command from a writable directory")
        return 1
    
    # Set flags based on the keep options
    if args.keep:
        # Keep everything
        config.keep_session_workspace = True
        config.keep_all_workspaces = True
    elif args.keep_logs:
        # Keep only logs
        config.keep_session_workspace = True
        config.keep_all_workspaces = False
    else:
        # Keep nothing
        config.keep_session_workspace = False
        config.keep_all_workspaces = False
    
    # Check for file mode deprecation
    if args.file_mode and config.FILE_MODE_DEPRECATED:
        config.show_file_mode_deprecation_warning(logger)
    
    # Execute requested command
    if args.command == "grid":
        logger.info("Executing grid replication command...")
        grid_dims = (args.grid, args.grid, args.grid)
        
        # Determine processing mode (object-based by default)
        use_object_mode = not args.file_mode
        
        # Validate debug_output option
        if args.debug_output and not use_object_mode:
            logger.warning("Debug output is only available in object-based mode. Ignoring --debug-output.")
            args.debug_output = False
        
        try:
            if use_object_mode:
                logger.info("Using object-based approach for grid replication")
                
                # Create pipeline
                pipeline = MolecularPipeline(
                    debug=args.debug_output,
                    debug_prefix=args.debug_prefix,
                    keep_workspace=config.keep_all_workspaces
                )
                
                # Load, transform, save
                pipeline.load(args.car, args.mdf) \
                        .generate_grid(grid_dims, args.gap) \
                        .save(args.output_car, args.output_mdf, args.base_name)
                
                total_molecules = grid_dims[0] * grid_dims[1] * grid_dims[2]
                logger.info(f"Grid generation successful: {grid_dims[0]}x{grid_dims[1]}x{grid_dims[2]} = {total_molecules} molecules")
            else:
                logger.info("Using legacy file-based approach for grid replication")
                grid.generate_grid_files(
                    args.car, args.mdf, 
                    args.output_car, args.output_mdf, 
                    grid_dims, args.gap, args.base_name
                )
                logger.info(f"Grid generation successful: {args.grid}x{args.grid}x{args.grid} = {args.grid**3} molecules")
        except Exception as e:
            logger.error(f"Grid generation failed: {str(e)}")
            # Keep workspace on error
            config.keep_session_workspace = True
            logger.info(f"Logs available in workspace: {config.session_workspace.current_workspace}")
            return 1
    
    elif args.command == "update-ff":
        logger.info("Executing force-field update command...")
        
        # Determine processing mode (object-based by default)
        use_object_mode = not args.file_mode
        
        # Validate debug_output option
        if args.debug_output and not use_object_mode:
            logger.warning("Debug output is only available in object-based mode. Ignoring --debug-output.")
            args.debug_output = False
        
        # Object-based approach validation
        if use_object_mode:
            if not (args.mdf and args.car):
                logger.error("Both --mdf and --car are required when using object-based mode")
                return 1
            if not (args.output_mdf or args.output_car):
                logger.error("At least one of --output-mdf or --output-car must be provided")
                return 1
        else:
            # File-based approach validation
            if not (args.mdf or args.car):
                logger.error("At least one of --mdf or --car must be provided")
                return 1
            if args.mdf and not args.output_mdf:
                logger.error("--output-mdf is required when --mdf is provided")
                return 1
            if args.car and not args.output_car:
                logger.error("--output-car is required when --car is provided")
                return 1
        
        try:
            if use_object_mode:
                logger.info("Using object-based approach for force-field update")
                
                # Create pipeline with the global keep_workspace setting
                pipeline = MolecularPipeline(
                    debug=args.debug_output,
                    debug_prefix=args.debug_prefix,
                    keep_workspace=config.keep_all_workspaces
                )
                
                # Load, transform, save
                pipeline.load(args.car, args.mdf) \
                        .update_ff_types(args.mapping) \
                        .save(args.output_car, args.output_mdf)
                
                logger.info("Force-field types updated successfully")
            else:
                logger.info("Using legacy file-based approach for force-field update")
                results = update_ff.update_ff_types(
                    car_file=args.car,
                    mdf_file=args.mdf,
                    output_car=args.output_car,
                    output_mdf=args.output_mdf,
                    mapping_file=args.mapping
                )
                
                if 'car_updates' in results:
                    logger.info(f"Updated {results['car_updates']} atoms in CAR file: {args.output_car}")
                if 'mdf_updates' in results:
                    logger.info(f"Updated {results['mdf_updates']} atoms in MDF file: {args.output_mdf}")
        except Exception as e:
            logger.error(f"Force-field update failed: {str(e)}")
            # Keep workspace on error
            config.keep_session_workspace = True
            logger.info(f"Logs available in workspace: {config.session_workspace.current_workspace}")
            return 1
    
    elif args.command == "update-charges":
        logger.info("Executing charge update command...")
        
        # Determine processing mode (object-based by default)
        use_object_mode = not args.file_mode
        
        # Validate debug_output option
        if args.debug_output and not use_object_mode:
            logger.warning("Debug output is only available in object-based mode. Ignoring --debug-output.")
            args.debug_output = False
        
        # Object-based approach validation
        if use_object_mode:
            if not (args.mdf and args.car):
                logger.error("Both --mdf and --car are required when using object-based mode")
                return 1
            if not (args.output_mdf or args.output_car):
                logger.error("At least one of --output-mdf or --output-car must be provided")
                return 1
        else:
            # File-based approach validation
            if not (args.mdf or args.car):
                logger.error("At least one of --mdf or --car must be provided")
                return 1
            if args.mdf and not args.output_mdf:
                logger.error("--output-mdf is required when --mdf is provided")
                return 1
            if args.car and not args.output_car:
                logger.error("--output-car is required when --car is provided")
                return 1
        
        try:
            if use_object_mode:
                logger.info("Using object-based approach for charge update")
                
                # Create pipeline with the global keep_workspace setting
                pipeline = MolecularPipeline(
                    debug=args.debug_output,
                    debug_prefix=args.debug_prefix,
                    keep_workspace=config.keep_all_workspaces
                )
                
                # Load, transform, save
                pipeline.load(args.car, args.mdf) \
                        .update_charges(args.mapping) \
                        .save(args.output_car, args.output_mdf)
                
                logger.info("Charges updated successfully")
            else:
                logger.info("Using legacy file-based approach for charge update")
                results = update_charges.update_charges(
                    car_file=args.car,
                    mdf_file=args.mdf,
                    output_car=args.output_car,
                    output_mdf=args.output_mdf,
                    mapping_file=args.mapping
                )
                
                if 'car_updates' in results:
                    logger.info(f"Updated {results['car_updates']} charges in CAR file: {args.output_car}")
                if 'mdf_updates' in results:
                    logger.info(f"Updated {results['mdf_updates']} charges in MDF file: {args.output_mdf}")
        except Exception as e:
            logger.error(f"Charge update failed: {str(e)}")
            # Keep workspace on error
            config.keep_session_workspace = True
            logger.info(f"Logs available in workspace: {config.session_workspace.current_workspace}")
            return 1
    
    elif args.command == "packmol":
        logger.info("Executing Packmol command...")
        
        try:
            # Import the Packmol tool
            from moltools.external_tools import PackmolTool
            
            # Create a Packmol tool instance
            packmol = PackmolTool()
            
            # Parse input file
            logger.info(f"Parsing Packmol input file: {args.input_file}")
            config_dict = packmol.parse_packmol_file(args.input_file)
            
            # Print JSON and exit if requested
            if args.print_json:
                print(json.dumps(config_dict, indent=2))
                return 0
            
            # Load updates from file if provided
            update_dict = None
            if args.update_file:
                if os.path.isfile(args.update_file):
                    try:
                        with open(args.update_file, 'r') as f:
                            update_dict = json.load(f)
                        logger.info(f"Loaded updates from file: {args.update_file}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse update file as JSON: {e}")
                        return 1
                else:
                    logger.error(f"Update file not found: {args.update_file}")
                    return 1
            
            # Execute Packmol if requested
            if args.execute:
                logger.info("Executing Packmol...")
                result = packmol.execute(
                    input_file=args.input_file,
                    output_file=args.output_file,
                    update_dict=update_dict
                )
                
                # Check if execution was successful
                if result['return_code'] == 0:
                    logger.info("Packmol execution successful!")
                    if result.get('output_file'):
                        logger.info(f"Output file created: {result['output_file']}")
                else:
                    logger.error("Packmol execution failed.")
                    return 1
            # Otherwise, just update and generate a new input file
            elif args.output_file:
                logger.info(f"Generating Packmol input file: {args.output_file}")
                
                # Apply updates if provided
                if update_dict:
                    config_dict = packmol.update_dict(config_dict, update_dict)
                    logger.info("Applied updates to configuration.")
                
                # Generate the new input file
                packmol.generate_packmol_file(config_dict, args.output_file)
                logger.info(f"Generated input file: {args.output_file}")
            else:
                logger.error("Either --output-file or --execute must be specified.")
                return 1
                
        except Exception as e:
            logger.error(f"Packmol operation failed: {str(e)}")
            # Keep workspace on error
            config.keep_session_workspace = True
            logger.info(f"Logs available in workspace: {config.session_workspace.current_workspace}")
            return 1
            
    elif args.command == "convert-to-namd":
        logger.info("Executing NAMD conversion command...")
        
        # NAMD conversion is only available in object mode
        if args.file_mode:
            logger.error("NAMD conversion is only available in object-based mode")
            return 1
        
        # Handle output directory
        output_dir = args.output_dir
        
        # Convert to absolute path if relative
        if not os.path.isabs(output_dir):
            output_dir = os.path.abspath(output_dir)
        
        try:
            # Create the directory and any needed parent directories
            os.makedirs(output_dir, exist_ok=True)
            logger.debug(f"Created output directory: {output_dir}")
        except Exception as e:
            logger.error(f"Failed to create output directory '{output_dir}': {str(e)}")
            logger.error("Please check directory permissions or provide a different output directory")
            return 1
        
        # Update the argument with the absolute path
        args.output_dir = output_dir
        logger.debug(f"Using output directory: {output_dir}")
        
        try:
            # Session workspace is already set up by the global flag processing
            
            # Create pipeline with the global keep_workspace setting
            pipeline = MolecularPipeline(
                debug=args.debug_output,
                debug_prefix=args.debug_prefix,
                keep_workspace=config.keep_all_workspaces
            )
            
            # Load system
            pipeline.load(args.car, args.mdf)
            
            # Convert to NAMD - respect global keep flags
            cleanup_workspace = not config.keep_all_workspaces
            
            pipeline.convert_to_namd(
                output_dir=args.output_dir,
                residue_name=args.residue_name,
                parameter_file=args.parameter_file,
                charge_groups=args.charge_groups,
                cleanup_workspace=cleanup_workspace
            )
            
            # Report result files
            for key, file_path in pipeline.namd_files.items():
                if file_path and os.path.exists(file_path):
                    file_size = os.path.getsize(file_path) / 1024  # Size in KB
                    logger.info(f"Generated {key}: {os.path.basename(file_path)} ({file_size:.1f} KB)")
            
            logger.info(f"NAMD conversion successful. Output files in: {args.output_dir}")
            
        except Exception as e:
            logger.error(f"NAMD conversion failed: {str(e)}")
            # Keep workspace on error
            config.keep_session_workspace = True
            logger.info(f"Logs available in workspace: {config.session_workspace.current_workspace}")
            return 1
    
    else:
        parser.print_help()
        return 1
    
    return 0

def cleanup_session():
    """Clean up the session workspace if needed."""
    if config.session_workspace:
        # Keep the workspace if requested with --keep or if there was an error
        should_keep = (
            getattr(config, 'keep_session_workspace', False) or 
            sys.exc_info()[0] is not None
        )
        
        if should_keep:
            if sys.exc_info()[0] is not None:
                logger.info(f"Keeping session workspace due to error. Logs available at: {config.session_workspace.current_workspace}")
            else:
                if config.keep_all_workspaces:
                    logger.info(f"Keeping all workspaces and logs (--keep). Session workspace: {config.session_workspace.current_workspace}")
                else:
                    logger.info(f"Keeping logs only (--keep-logs). Session workspace: {config.session_workspace.current_workspace}")
        else:
            # Clean up the session workspace
            logger.debug(f"Cleaning up session workspace: {config.session_workspace.current_workspace}")
            config.session_workspace.close(cleanup=True)

if __name__ == "__main__":
    try:
        exit_code = main()
    finally:
        cleanup_session()
    
    sys.exit(exit_code)