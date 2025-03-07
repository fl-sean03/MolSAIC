# Molecular File Formats Reference

This document provides detailed specifications for the molecular file formats supported by MONET, describing headers, data entries, footers, column sizes, and whitespace requirements. These formats represent molecular structures and systems precisely and are compatible with software such as Materials Studio.

### 1. PDB File Format

**Header**:

- Begins with lines starting with `REMARK`, indicating metadata.
- Includes explicit statement: `generated coordinate PDB file from .car/.mdf files`.
- Multi-molecule systems include a `CRYST1` line specifying periodic boundary conditions (PBC):
  - Columns: Cell dimensions (a, b, c), Angles (alpha, beta, gamma), Space group (P 1), Z-value.
  - Precision: Dimensions (Å) and angles (degrees) to two decimals.

**Main Section**:

- Lines begin with `ATOM`.
- Strict format and specific column widths:

```
(1-6)   Record name "ATOM"
(7-11)  Atom serial number (right-aligned)
(13-16) Atom name (left-justified)
(18-20) Residue name
(23-26) Residue sequence number (right-aligned)
(31-38) X-coordinate (right-aligned, 3 decimals)
(39-46) Y-coordinate (right-aligned, 3 decimals)
(47-54) Z-coordinate (right-aligned, 3 decimals)
(55-60) Occupancy
(61-66) Temperature factor
(77-78) Element symbol (right-aligned)
```

- Columns separated by precise whitespace alignment (1-2 spaces).

**Example**:

```
ATOM      1 C1   nec     1       3.111   0.134  -0.289  1.00  0.00      nec  C
```

**Footer**:

- Ends without special terminator lines.

---

## CAR File Format

**Header**:

- Begins with `!BIOSYM archive 3` indicating file version.
- Specifies `PBC=ON/OFF` explicitly.
- Includes line: `Materials Studio Generated CAR File`.
- Contains generation date explicitly (`!DATE`).

**Example**:

```
!BIOSYM archive 3
PBC=ON
Materials Studio Generated CAR File
!DATE Wed Mar 05 18:07:25 2025
PBC    9.8627    9.8627    9.8627   90.0000   90.0000   90.0000 (P1)
```

**Main Section**:

- Atom entries structured as follows:

```
(1-8)   Atom name
(9-22)  X-coordinate (9 decimals)
(23-36) Y-coordinate (9 decimals)
(37-50) Z-coordinate (9 decimals)
(51-55) Identifier (constant "XXXX")
(56-58) Molecule index
(59-64) Atom type
(65-67) Element symbol
(68-74) Partial charge (3 decimals)
```

- Consistent whitespace alignment between columns (7-8 spaces typically).
- Multi-molecule files include repeated molecule sections separated by `end`.

Example:

```
C1       3.111059790    0.133921270   -0.289480390 XXXX 1      CT3     C  -0.270
```

**Footer**:

- Ends explicitly with the line: `end`

---

## MDF File Format

**Header**:

- Begins with `!BIOSYM molecular_data 4`.
- Explicit date and metadata about Materials Studio.
- Clearly defines each column with `@column`:

```
@column 1 element
@column 2 atom_type
@column 3 charge_group
@column 4 isotope
@column 5 formal_charge
@column 6 charge
@column 7 switching_atom
@column 8 oop_flag
@column 9 chirality_flag
@column 10 occupancy
@column 11 xray_temp_factor
@column 12 connections
```

**Main Section**:

- Precise structure for each atom entry:

```
(1-15)   Atom Label (XXXX_#:Atom)
(16-18)  Element
(19-24)  Atom Type
(25-31)  Charge Group
(32-34)  Isotope
(35-37)  Formal Charge
(38-44)  Charge Value
(45-47)  Switching Atom
(48-50)  OOP Flag
(51-53)  Chirality Flag
(54-60)  Occupancy
(61-67)  X-Ray Temp Factor
(68-)    Connectivity List
```

- Connectivity shown with fractional bond orders (e.g., `/1.5`).
- New molecules explicitly defined using `@molecule`.

Example:

```
XXXX_1:C1           C  CT3     ?     0  0    -0.2700 0 0 8 1.0000  0.0000 C2 H1 H2 H3
@molecule NEC_0H
```

**Whitespace**:

- Essential spacing between columns; atom identifiers occupy 15-20 characters.

**Footer**:

- Each molecule's definition ends implicitly after connectivity.

---

### Formatting Standards Across Files

- Adhere strictly to defined column widths and whitespace rules.
- Numerical values must be right-aligned, text fields left-aligned.
- Character limits must be exact to maintain alignment.
- Include explicit metadata for compatibility with modeling software.

This detailed reference ensures accurate and consistent file generation for molecular simulations.


