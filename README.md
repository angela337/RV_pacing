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

**RV_SNR.ipynb**
- Computes image quality metrics (SNR and CNR) for cardiac NIfTI images
- SNR = mean(RV blood pool) / std(RV blood pool)
- CNR = |mean(RV) - mean(Myocardium)| / std(background)
- Iterates over all cases and reports per-case metrics

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
- **copy_files_from_392.sh** - Copies DICOM files from remote server
- **check_nii_file.sh** - Validates NIfTI file integrity

### Visualization
- **make_images_len.sh** - Creates screenshot images of mesh visualizations

## Data Directories

```
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

## Collision Percentage Calculation

Collision percentages are computed at three levels: per-point across the cardiac cycle, per-patient, and across the patient cohort.

### 1. Per-Point, Per-Frame (RV_collision.py)

At each cardiac time frame, a cylinder is placed at every septal wall point oriented along the surface normal. The `cylTest` function performs a geometric point-in-cylinder test: it projects each structure point onto the cylinder axis and checks that (a) the projection falls within the cylinder height and (b) the perpendicular distance is within the radius.

Three structures are tested independently:
- **RV wall** — excludes points within 10mm of the attachment site, beyond 1.1x the device height, or on the septum itself
- **Papillary muscles (PM)** — all PM mesh points
- **Tricuspid valve (TV)** — all TV mesh points

The result per point per frame is binary (1 = any structure point falls inside the cylinder).

### 2. Per-Patient Summary (RV_collision.py)

Binary collisions are summed across all `ntimes` frames (typically 10, representing the cardiac cycle). The per-patient percentage at each mesh point is:

```
Collision_Percent = (sum of collisions across frames / ntimes) * 100
```

A `Combined_Collision` field is also computed as the logical OR of RV, PM, and TV collisions at each frame. These results are saved to `RV_collision-all_times.vtk`.

### 3. Cone Rotation Sensitivity (RV_collision.py)

The cone analysis tests multiple device orientations within a cone of half-angle `cone_angle` around the surface normal. Cone collision arrays start at 1 (assume collision) and are set to 0 if **any** sampled direction does not collide. This answers: "Is collision unavoidable regardless of device angle?"

### 4. Cross-Patient Aggregation (AHA_mapping.ipynb)

For each patient (cases 1-13), the `all_times` VTK file is loaded. The collision field is **binarized** per patient: any nonzero collision percentage becomes 1 (collided at least once across the cardiac cycle), zero stays 0.

Each patient's septum mesh has different geometry. To combine across patients, the binary field is interpolated onto a common polar coordinate grid (200 x 180, z x theta) via `interpolate_field()`.

All patient grids are stacked into `interp_stack` with shape `(N_cases, 200, 180)`. The sum across axis 0 produces `sum_field`: a count of how many patients had a collision at each spatial location.

### 5. AHA Region Statistics (AHA_mapping.ipynb)

For each AHA region, the corresponding theta/z range is extracted from `sum_field`, and:

```
region_mean = np.mean(region) * 10    # count / ~10 cases * 100 = percentage
region_std  = np.std(region) * 10
```

The final reported "Mean % of collisions" per AHA region is the **spatial average across that region of the percentage of patients who had a collision at that location**.

| Level | Representation |
|-------|---------------|
| Per point, per frame | Binary: did the cylinder collide here this frame? |
| Per point, per patient | Binary: did this point ever collide across any time frame? |
| Per grid cell, across patients | Count: how many patients had a collision at this location |
| Per AHA region | Mean/std of that count (as %) across all grid cells in the region |

## Typical Workflow

1. **Prepare data**: Place DICOM and segmentation masks in appropriate directories
2. **Run pipeline**: Execute `run_RV_sim.sh` with appropriate flags enabled
3. **Analyze results**: Open `Process_AHA_csv_to_plots_tables.ipynb` to generate figures
4. **Visualize**: Use `Map_3D_mesh.ipynb` to create 3D collision maps
