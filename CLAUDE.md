# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cardiac research pipeline simulating cylindrical leadless pacemaker placement in the right ventricle (RV) and detecting collisions with anatomical structures (RV wall, papillary muscles, tricuspid valve) across the cardiac cycle. Results are mapped to AHA regions for statistical analysis and publication figures.

**Published in**: Heart Rhythm O2, 2026. DOI: 10.1016/j.hroo.2026.02.030

## Running the Pipeline

The main orchestration script is `run_RV_sim.sh`. It controls all stages via boolean flags at the top of the script. To run only specific stages, set others to `false`:

```bash
bash run_RV_sim.sh
```

Patient cases processed: 01, 02, 04, 06–11, 13. Cases 03, 05, 12 are excluded (bad/missing data).

Collision detection is parallelized with `MAX_JOBS=16` (xargs-based).

## Running Individual Scripts

```bash
# Image preprocessing: extract RV gradient edges
python process_RV_gradient.py <dicom.nii> <mask.nii> <output.nii>

# Label extraction and dilation
python make_dilated_images.py <input.nii> <output.nii> --labels 4 5 22 24 --radius 1

# NIfTI → VTK mesh conversion
python nii2vtk2.py <input.nii> <output.vtk> --values 1 2 3

# Collision detection (typically called by run_RV_sim.sh)
python RV_collision.py <RV_wall.vtk> <PM.vtk> <TV.vtk> <output_prefix> \
    --length 25.9 --diameter 6.7 --cone_angle 5 --cone_samples 10
```

## Architecture and Data Flow

```
DICOM + segmentation masks (data/XX/1_seg/)
  → process_RV_gradient.py     # gradient edge detection for manual segmentation
  → make_dilated_images.py     # extract/dilate structure labels
  → nii2vtk2.py                # NIfTI → VTK meshes
  → CemrgApp (external)        # motion tracking across cardiac frames
  → RV_collision.py            # cylinder collision detection, outputs VTK + CSV
  → AHA_mapping.ipynb          # binarize per patient, interpolate to polar grid
  → Process_AHA_csv_to_plots_tables.ipynb  # publication figures
```

**Data directory layout**:
```
/data/XX/
  1_seg/      # segmentation masks, preprocessed NIfTI
  2_motion/   # CemrgApp motion output, collision results
  PM/         # papillary muscle meshes
```

## Core Algorithm: Collision Detection (RV_collision.py)

The `cylTest()` function performs geometric point-in-cylinder testing:
- Projects each structure point onto the cylinder axis
- Accepts if projection height ∈ [0, length] AND perpendicular distance ≤ radius

RV wall exclusion rules (points are skipped):
- Within 10 mm of attachment site
- Beyond 1.1× device height
- On the septum itself

**Cone rotation analysis**: tests `cone_samples` device orientations within a cone of half-angle `cone_angle` around the surface normal using Rodrigues' rotation. Cone collision starts at 1 (assume collision) and is cleared to 0 if *any* sampled direction avoids collision — i.e., it answers "is collision unavoidable?"

**Output files per simulation**:
- `RV_collision-frame_XX.vtk` — per-frame binary collision field
- `RV_collision-all_times.vtk` — summary mesh with per-point collision percentages
- `*_collision_data.csv` — tabular collision statistics

## Collision Percentage Calculation (Multi-Level)

| Level | Method |
|-------|--------|
| Per point, per frame | Binary: cylTest hit or miss |
| Per point, per patient | `sum(collisions across frames) / ntimes * 100` |
| Per patient, per grid cell | Binarized (any nonzero → 1), interpolated onto 200×180 polar grid |
| Per AHA region | `np.mean(region) * 10` across all grid cells in that region |

Cross-patient aggregation uses a common polar coordinate grid (200 z-bins × 180 theta-bins). All patient grids stack to shape `(N_cases, 200, 180)`.

## Devices

| Device | Length (mm) | Diameter (mm) |
|--------|-------------|---------------|
| AveirVR | 38.0 | 6.5 |
| AveirAR | 32.2 | 6.5 |
| MicraTPS | 25.9 | 6.7 |

The pipeline tests 7 device lengths (15–45 mm) per device per case.

## Dependencies

**Python**: `numpy`, `vtk`, `pyvista`, `nibabel`, `SimpleITK`, `scipy`, `pandas`, `matplotlib`

**External tools** (must be installed separately):
- GMSH — cylinder mesh generation
- CemrgApp 2.3 — DICOM processing and motion tracking
- Meshtool — mesh operations
- ImageMagick — figure compositing (`make_images_len.sh`)

No `requirements.txt` or `setup.py` exists. Install dependencies manually.

## Analysis Notebook Order

For reproducing results from scratch after pipeline completes:
1. `AHA_mapping.ipynb` — aggregate per-patient VTK outputs onto polar grid
2. `Statistics_compare_csv_output_from_AHA_mapping.ipynb` — cross-device stats
3. `Process_AHA_csv_to_plots_tables.ipynb` — publication figures and tables
4. `Map_3D_mesh.ipynb` — 3D spatial collision hotspot visualization
