# MS_HF_cohort - RV Device Collision Analysis

Cardiac biomedical research codebase for analyzing right ventricular (RV) leadless pacemaker placement simulations. This project performs collision detection between implantable cardiac devices and anatomical structures throughout the cardiac cycle.

## Overview

This pipeline:
1. Processes cardiac MRI/CT DICOM images and segmentation masks
2. Generates 3D meshes of cardiac structures (RV wall, papillary muscles, tricuspid valve)
3. Simulates cylindrical device placement at multiple positions on the RV septal wall
4. Detects collisions between devices and cardiac structures across all cardiac phases
5. Maps results to AHA (American Heart Association) regions for statistical analysis
6. Generates publication-ready plots and tables

## Main Pipeline

### run_RV_sim.sh
Main orchestration script that controls the entire workflow. Uses flags to enable/disable processing stages:

```bash
# Key flags in the script:
# - Image processing and mesh generation
# - Motion tracking across cardiac frames
# - Collision simulation execution
# - Post-processing and analysis
```

## Core Scripts

### Collision Detection

**RV_collision.py**
- Main collision detection algorithm
- Tests cylindrical device placement against RV wall, papillary muscles (PM), and tricuspid valve (TV)
- Supports cone angle rotation analysis for sensitivity testing
- Outputs collision statistics as CSV files
- Usage: Called by run_RV_sim.sh with device parameters (length, diameter, position)

**collision_map.py**
- Simplified collision detection using PyVista mesh operations
- Used for quick visualization and prototyping

### Image Processing

**process_RV_gradient.py**
- Processes DICOM images to extract RV blood pool regions
- Applies gradient edge detection for structure identification
- Inputs: DICOM file + segmentation mask
- Outputs: Gradient-filtered NIfTI image

**make_dilated_images.py**
- Extracts specific labels from segmentation masks
- Creates morphologically dilated versions of structures
- Used for LV wall, blood pool, and BiV region extraction

**nii2vtk2.py**
- Converts NIfTI medical images to VTK polydata meshes
- Preserves label information as element tags (elemTag)

## Analysis Notebooks

### Primary Analysis

**Process_AHA_csv_to_plots_tables.ipynb**
- Main analysis notebook
- Reads collision CSV output files
- Generates statistical plots by AHA region
- Creates publication-ready figures and tables
- Compares standard vs cone rotation simulations

**AHA_mapping.ipynb**
- Maps collision detection results to AHA cardiac regions
- Organizes and processes regional data

**Statistics_compare_csv_output_from_AHA_mapping.ipynb**
- Statistical comparison across devices and configurations
- Compares collision rates between device types

### Visualization

**Device_specs.ipynb**
- Device specifications and volume calculations
- 3D mesh visualization with front/back views

**Map_3D_mesh.ipynb**
- Projects AHA analysis results onto 3D cardiac mesh
- Creates spatial visualization of collision hotspots

**Make_cylinders_for_vis.ipynb**
- Generates cylinder representations for device visualization
- Creates animated visualizations of device motion

**MRI_with_mesh.ipynb**
- Overlays 3D meshes on original MRI slices
- Quality control and visualization

### Validation

**check_convergence.ipynb**
- Validates simulation convergence
- Data quality checks

**Statistics_collField_length.ipynb**
- Analyzes collision field values as function of device length
- Length sensitivity analysis

**RV_mapping.ipynb**
- RV segmentation and mapping workflows

## Utility Scripts

### File Management
- **move_files.sh** - Moves/copies data files between directories
- **copy_files_from_392.sh** - Copies DICOM files from remote server
- **unzip.sh** - Unzips archived data files
- **check_nii_file.sh** - Validates NIfTI file integrity

### Visualization
- **make_images_len.sh** - Creates screenshot images of mesh visualizations

## Data Directories

```
Motion_data/
├── input_vtk/          # Input VTK meshes (RV, LV surfaces) at each time frame (0-10)
├── Structures/         # Transform scripts for motion tracking
├── output_cylinders/   # Generated device cylinder meshes
├── GMSH/               # GMSH mesh data
├── videos/             # Animation outputs
└── figures/            # Generated figures

plots/                  # Output PNG images of collision analysis results
```

## Devices Analyzed

| Device | Initial Length (mm) | Diameter (mm) |
|--------|---------------------|---------------|
| AveirVR | 38.0 | 6.5 |
| AveirAR | 32.2 | 6.5 |
| MicraTPS | 25.9 | 6.7 |

## Dependencies

- Python: numpy, vtk, pyvista, nibabel, SimpleITK, scipy, pandas, matplotlib
- GMSH for mesh generation
- Bash for pipeline orchestration

## Typical Workflow

1. **Prepare data**: Place DICOM and segmentation masks in appropriate directories
2. **Run pipeline**: Execute `run_RV_sim.sh` with appropriate flags enabled
3. **Analyze results**: Open `Process_AHA_csv_to_plots_tables.ipynb` to generate figures
4. **Visualize**: Use `Map_3D_mesh.ipynb` to create 3D collision maps
