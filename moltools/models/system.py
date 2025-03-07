"""
Module for the System class - represents a collection of molecules with periodic boundary conditions.
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union, Any

# Import parsers and models for factory methods
from ..parsers.car_parser import parse_car
from ..parsers.mdf_parser import parse_mdf
from ..models.molecule import Molecule
from ..models.atom import Atom

logger = logging.getLogger(__name__)

class System:
    """
    A class representing a molecular system with multiple molecules and periodic boundary conditions.
    
    Attributes:
        mdf_data (dict): Force-field data from MDF parsing.
        molecules (list): List of Molecule objects.
        pbc (tuple): Periodic boundary conditions (dimensions, angles, cell type).
    """
    
    def __init__(self, mdf_data=None):
        """
        Initialize a System object.
        
        Args:
            mdf_data (dict, optional): Force-field data dictionary from MDF. Default is None.
        """
        self.mdf_data = mdf_data if mdf_data is not None else {}
        self.molecules = []
        self.pbc = None
    
    def generate_grid(self, template_molecule, grid_dims=(8, 8, 8), gap=2.0):
        """
        Replicates a template molecule in a 3D grid.
        
        Args:
            template_molecule (Molecule): The template molecule to replicate.
            grid_dims (tuple): Grid dimensions (nx, ny, nz). Default is (8, 8, 8).
            gap (float): Gap between molecules in Angstroms. Default is 2.0.
        """
        _, center, size = template_molecule.compute_bbox()
        spacing = (size[0] + gap, size[1] + gap, size[2] + gap)
        
        nx, ny, nz = grid_dims
        grid_molecules = []
        
        # Calculate total molecules and report size
        total_molecules = nx * ny * nz
        logger.info(f"Generating {nx}x{ny}x{nz} grid with {gap}Å gap...")
        logger.info(f"Grid will contain {total_molecules} molecules")
        
        # Pre-calculate offsets for efficiency
        x_offsets = [(i + 0.5) * spacing[0] for i in range(nx)]
        y_offsets = [(j + 0.5) * spacing[1] for j in range(ny)]
        z_offsets = [(k + 0.5) * spacing[2] for k in range(nz)]
        
        # Pre-allocate the list for performance
        grid_molecules = []
        count = 0
        progress_step = max(1, total_molecules // 10)  # Report progress about 10 times
        
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    # Calculate the cell center for this grid position
                    offset = (x_offsets[i], y_offsets[j], z_offsets[k])
                    
                    # Create a translated copy of the template molecule
                    new_mol = template_molecule.replicate(offset, center)
                    grid_molecules.append(new_mol)
                    
                    # Update and report progress
                    count += 1
                    if count % progress_step == 0 or count == total_molecules:
                        progress_percent = count / total_molecules * 100
                        logger.info(f"Progress: {count}/{total_molecules} molecules generated ({progress_percent:.1f}%)")
        
        self.molecules = grid_molecules
        
        # Set new periodic boundary conditions for the grid
        overall_box = (nx * spacing[0], ny * spacing[1], nz * spacing[2])
        self.pbc = (overall_box[0], overall_box[1], overall_box[2],
                    90.0, 90.0, 90.0, "P1")
        
        logger.info(f"Grid generation complete: {len(grid_molecules)} molecules.")
        logger.info(f"New box dimensions: {overall_box[0]:.2f} x {overall_box[1]:.2f} x {overall_box[2]:.2f} Å")
    
    def build_mdf_header(self):
        """
        Builds the standard MDF header lines.
        
        Returns:
            list: List of header lines.
        """
        header_lines = [
            "!BIOSYM molecular_data 4",
            "",
            f"!Date: {datetime.now().strftime('%a %b %d %H:%M:%S %Y')}   MolTools Generated MDF file",
            "",
            "#topology",
            "",
            "@column 1 element",
            "@column 2 atom_type",
            "@column 3 charge_group",
            "@column 4 isotope",
            "@column 5 formal_charge",
            "@column 6 charge",
            "@column 7 switching_atom",
            "@column 8 oop_flag",
            "@column 9 chirality_flag",
            "@column 10 occupancy",
            "@column 11 xray_temp_factor",
            "@column 12 connections",
            ""
        ]
        return header_lines
    
    def build_mdf_footer(self):
        """
        Builds the MDF footer using the system's PBC.
        If PBC is not defined, returns a minimal footer with just the end marker.
        
        Returns:
            list: List of footer lines.
        """
        if not self.pbc:
            return ["", "#end"]
            
        cell_type = self.pbc[6] if len(self.pbc) >= 7 else "P1"
        return [
            "!",
            "#symmetry",
            "@periodicity 3 xyz",
            f"@group ({cell_type})",
            "",
            "#end"
        ]
    
    def build_car_header(self):
        """
        Builds the CAR header using the system's PBC.
        
        Returns:
            list: List of header lines.
        """
        if self.pbc and len(self.pbc) >= 7:
            header_lines = [
                "!BIOSYM archive 3",
                "PBC=ON",
                "MolTools Generated CAR File",
                f"!DATE {datetime.now().strftime('%a %b %d %H:%M:%S %Y')}",
                f"PBC   {self.pbc[0]:.4f}   {self.pbc[1]:.4f}   {self.pbc[2]:.4f}   "
                f"{self.pbc[3]:.4f}   {self.pbc[4]:.4f}   {self.pbc[5]:.4f} ({self.pbc[6]})"
            ]
        else:
            header_lines = [
                "!BIOSYM archive 3",
                "PBC=OFF",
                "Materials Studio Generated CAR File",
                f"!DATE {datetime.now().strftime('%a %b %d %H:%M:%S %Y')}"
            ]
        return header_lines
    
    def generate_mdf_lines(self, base_name, residue_mapping=None):
        """
        Generates MDF lines for each molecule in the system.
        
        Args:
            base_name (str): Base name for molecules.
            residue_mapping (dict, optional): Mapping for residue names. Default is None.
        
        Returns:
            list: List of MDF lines.
        """
        mdf_lines = []
        molecule_counter = 1
        
        for mol in self.molecules:
            # Generate molecule header
            mol_name = base_name if molecule_counter == 1 else f"{base_name}{molecule_counter}"
            mdf_lines.append(f"@molecule {mol_name}")
            mdf_lines.append("")
            
            # First, create a lookup table for atoms in this molecule
            atom_lookup = {}
            for i, atom in enumerate(mol.atoms):
                atom_lookup[atom.atom_name] = i
                
            # First pass: Look up the original MDF data for reference
            original_mdf_data = {}
            for key, value in self.mdf_data.items():
                if key[0] == base_name:  # Match the base molecule name
                    # Store this for reference when creating lines
                    original_mdf_data[key[1]] = value  # Key by atom name
            
            # Second pass: Generate lines using appropriate data
            for atom in mol.atoms:
                final_residue_name = f"XXXX_{atom.residue_number}"
                
                # Map the residue name if a mapping is provided
                if residue_mapping:
                    mapped_residue = residue_mapping.get(atom.residue_name, atom.residue_name)
                else:
                    mapped_residue = atom.residue_name
                
                # Try to find this atom in original template MDF data (by atom name)
                original_data = original_mdf_data.get(atom.atom_name.upper())
                
                key = (mapped_residue, atom.atom_name.upper())
                ff_data = self.mdf_data.get(key)
                
                if ff_data is None:
                    # Default force-field data if not found
                    ff_data = {
                        'element': atom.element,
                        'atom_type': atom.atom_type,
                        'charge_group': '?',
                        'isotope': '0',
                        'formal_charge': '0',
                        'charge': atom.charge,
                        'switching_atom': '0',
                        'oop_flag': '0',
                        'chirality_flag': '0',
                        'occupancy': '1.0000',
                        'xray_temp_factor': '0.0000',
                        'connections': atom.connections if hasattr(atom, 'connections') and atom.connections else []
                    }
                
                # Get the connections from the original MDF data
                # Use the previously looked up original data if available 
                original_connections = []
                if original_data and 'connections' in original_data:
                    original_connections = original_data['connections']
                
                # Extract chirality flag value
                chirality = None
                
                # Try to get the real chirality value from the original MDF data
                if original_data and 'chirality_flag' in original_data:
                    chirality = original_data['chirality_flag']
                else:
                    chirality = ff_data['chirality_flag']
                    
                # Format the MDF line
                line = (f"{final_residue_name}:{atom.atom_name:<12} {ff_data['element']:<2} {ff_data['atom_type']:<7} "
                        f"{ff_data['charge_group']:<5} {ff_data['isotope']:<2} {ff_data['formal_charge']:<5} {ff_data['charge']:<6} "
                        f"{ff_data['switching_atom']:<1} {ff_data['oop_flag']:<1} {chirality:<1} "
                        f"{ff_data['occupancy']:<7} {ff_data['xray_temp_factor']:<6}")
                
                # Prioritize connections in order:
                # 1. Original MDF data connections (from template lookup)
                # 2. Connections from the ff_data dictionary
                # 3. Connections from the atom object
                if original_connections:
                    line += " " + " ".join(original_connections)
                elif 'connections' in ff_data and ff_data['connections']:
                    line += " " + " ".join(ff_data['connections'])
                elif hasattr(atom, 'connections') and atom.connections:
                    line += " " + " ".join(atom.connections)
                
                mdf_lines.append(line)
            
            mdf_lines.append("")  # Blank line to separate molecule blocks
            molecule_counter += 1
        
        return mdf_lines
    
    def generate_car_lines(self):
        """
        Generates CAR lines for each molecule in the system.
        Each molecule block is followed by an "end" marker, and the final "end" line
        for the file is handled separately in the to_files method.
        
        Returns:
            list: List of CAR lines.
        """
        car_lines = []
        
        for mol in self.molecules:
            if not mol.atoms:
                continue
                
            output_res_name = mol.atoms[0].residue_name
            
            for atom in mol.atoms:
                key = (atom.residue_name, atom.atom_name.upper())
                ff_data = self.mdf_data.get(key, {
                    'atom_type': atom.atom_type,
                    'element': atom.element,
                    'charge': atom.charge
                })
                
                # Format the CAR line
                line = (f"{atom.atom_name:<6}"
                        f"{atom.x: 14.9f}"
                        f"{atom.y: 15.9f}"
                        f"{atom.z: 15.9f} "
                        f"{output_res_name:<5}"
                        f"{atom.residue_number:<7}"
                        f"{ff_data.get('atom_type', ''): <8}"
                        f"{ff_data.get('element', ''): <4}"
                        f"{ff_data.get('charge', ''): <6}")
                
                car_lines.append(line)
            
            # Add "end" marker after each molecule
            car_lines.append("end")
        
        return car_lines
    
    def __len__(self):
        """
        Get the number of molecules in the system.
        
        Returns:
            int: Number of molecules.
        """
        return len(self.molecules)
    
    def __repr__(self):
        """
        String representation of the system.
        
        Returns:
            str: A string representation of the system.
        """
        if self.pbc:
            return f"System({len(self.molecules)} molecules, PBC={self.pbc[0]:.2f}x{self.pbc[1]:.2f}x{self.pbc[2]:.2f})"
        else:
            return f"System({len(self.molecules)} molecules, PBC=None)"
            
    @classmethod
    def system_from_files(cls, car_file: str, mdf_file: str) -> 'System':
        """
        Factory method to create a System object from CAR and MDF files.
        
        Args:
            car_file (str): Path to the CAR file.
            mdf_file (str): Path to the MDF file.
            
        Returns:
            System: A System object loaded with the data from the files.
            
        Raises:
            FileNotFoundError: If either file does not exist.
            ValueError: If file parsing fails.
        """
        logger.info(f"Loading system from files: {car_file}, {mdf_file}")
        
        # Parse MDF file for force-field data
        mdf_header, mdf_data = parse_mdf(mdf_file)
        
        # Create a new System with the MDF data
        system = cls(mdf_data=mdf_data)
        
        # Parse CAR file for structure data
        car_header, molecule_data, pbc = parse_car(car_file)
        
        # Extract PBC information
        if pbc:
            system.pbc = pbc
        
        # Convert molecule data to Molecule objects
        for mol_block in molecule_data:
            if not mol_block:  # Skip empty molecules
                continue
            
            # Create atoms for this molecule
            atoms = []
            for atom_data in mol_block:
                atom = Atom(
                    atom_name=atom_data['atom_name'],
                    x=atom_data['x'],
                    y=atom_data['y'],
                    z=atom_data['z'],
                    residue_name=atom_data['residue_name'],
                    residue_number=atom_data['residue_number'],
                    atom_type=atom_data.get('atom_type', ''),
                    element=atom_data.get('element', ''),
                    charge=atom_data.get('charge', 0.0)
                )
                atoms.append(atom)
            
            # Create a Molecule from the atoms
            molecule = Molecule(atoms)
            system.molecules.append(molecule)
        
        logger.info(f"System loaded: {len(system.molecules)} molecules, "
                   f"{sum(len(mol.atoms) for mol in system.molecules)} total atoms")
        
        return system
        
    def to_files(self, output_car: str, output_mdf: str, base_name: str = "MOL", residue_mapping: Optional[Dict] = None) -> None:
        """
        Write the system to CAR and MDF files.
        
        Args:
            output_car (str): Path to the output CAR file.
            output_mdf (str): Path to the output MDF file.
            base_name (str, optional): Base name for molecules. Default is "MOL".
            residue_mapping (dict, optional): Mapping for residue names. Default is None.
            
        Raises:
            IOError: If writing to either file fails.
        """
        logger.info(f"Writing system to files: {output_car}, {output_mdf}")
        
        # Generate CAR file content
        car_lines = self.build_car_header()
        car_lines.extend(self.generate_car_lines())
        
        # Generate MDF file content
        mdf_lines = self.build_mdf_header()
        mdf_lines.extend(self.generate_mdf_lines(base_name, residue_mapping))
        mdf_lines.extend(self.build_mdf_footer())
        
        # Write CAR file
        try:
            with open(output_car, 'w') as f:
                for line in car_lines:
                    f.write(line + '\n')
                
                # Write a final "end" line to end the file
                # This is in addition to the "end" after each molecule block
                f.write("end\n")
                    
            logger.info(f"CAR file written: {output_car}")
        except Exception as e:
            logger.error(f"Error writing CAR file: {str(e)}")
            raise IOError(f"Failed to write CAR file: {str(e)}")
        
        # Write MDF file
        try:
            with open(output_mdf, 'w') as f:
                for line in mdf_lines:
                    f.write(line + '\n')
            logger.info(f"MDF file written: {output_mdf}")
        except Exception as e:
            logger.error(f"Error writing MDF file: {str(e)}")
            raise IOError(f"Failed to write MDF file: {str(e)}")
    
    def update_ff_types(self, mapping: Union[Dict, str]) -> int:
        """
        Update force-field types in the system based on a mapping.
        
        Args:
            mapping (dict or str): Dictionary mapping (charge, element) to force-field types,
                                  or path to a JSON file containing this mapping.
                                  
        Returns:
            int: Number of atoms updated.
            
        Raises:
            ValueError: If the mapping is invalid or file not found.
        """
        logger.info("Updating force-field types in system")
        
        # Load mapping from file if a string was provided
        if isinstance(mapping, str):
            try:
                with open(mapping, 'r') as f:
                    mapping_dict = json.load(f)
                
                # Process keys to handle tuple format
                processed_mapping = {}
                for key, value in mapping_dict.items():
                    if key.startswith('(') and key.endswith(')'):
                        try:
                            parts = key.strip('()').split(',')
                            if len(parts) == 2:
                                charge = float(parts[0].strip())
                                element = parts[1].strip().strip('"\'')
                                processed_mapping[(charge, element)] = value
                            else:
                                processed_mapping[key] = value
                        except ValueError:
                            processed_mapping[key] = value
                    else:
                        processed_mapping[key] = value
                
                mapping = processed_mapping
                logger.info(f"Loaded force-field mapping from file: {len(mapping)} entries")
            except Exception as e:
                logger.error(f"Error loading mapping file: {str(e)}")
                raise ValueError(f"Invalid mapping file: {str(e)}")
        
        # Update force-field types for each atom in each molecule
        update_count = 0
        for molecule in self.molecules:
            for atom in molecule.atoms:
                key = (atom.charge, atom.element)
                if key in mapping:
                    old_type = atom.atom_type
                    new_type = mapping[key]
                    atom.atom_type = new_type
                    
                    # Update in MDF data if present
                    mdf_key = (atom.residue_name, atom.atom_name.upper())
                    if mdf_key in self.mdf_data:
                        self.mdf_data[mdf_key]['atom_type'] = new_type
                    
                    logger.debug(f"Updated {atom.atom_name} ({atom.element}): {old_type} -> {new_type}")
                    update_count += 1
        
        logger.info(f"Updated {update_count} force-field types in system")
        return update_count
    
    def update_charges(self, mapping: Union[Dict, str]) -> int:
        """
        Update atomic charges in the system based on a mapping from force-field types.
        
        Args:
            mapping (dict or str): Dictionary mapping force-field types to charges,
                                  or path to a JSON file containing this mapping.
                                  
        Returns:
            int: Number of atoms updated.
            
        Raises:
            ValueError: If the mapping is invalid or file not found.
        """
        logger.info("Updating charges in system")
        
        # Load mapping from file if a string was provided
        if isinstance(mapping, str):
            try:
                with open(mapping, 'r') as f:
                    mapping = json.load(f)
                logger.info(f"Loaded charge mapping from file: {len(mapping)} entries")
            except Exception as e:
                logger.error(f"Error loading mapping file: {str(e)}")
                raise ValueError(f"Invalid mapping file: {str(e)}")
        
        # Update charges for each atom in each molecule
        update_count = 0
        for molecule in self.molecules:
            for atom in molecule.atoms:
                if atom.atom_type in mapping:
                    old_charge = atom.charge
                    new_charge = mapping[atom.atom_type]
                    atom.charge = new_charge
                    
                    # Update in MDF data if present
                    mdf_key = (atom.residue_name, atom.atom_name.upper())
                    if mdf_key in self.mdf_data:
                        self.mdf_data[mdf_key]['charge'] = new_charge
                    
                    logger.debug(f"Updated {atom.atom_name} ({atom.atom_type}): charge {old_charge} -> {new_charge}")
                    update_count += 1
        
        logger.info(f"Updated {update_count} charges in system")
        return update_count
