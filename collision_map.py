import pyvista as pv
import numpy as np

path="/home/alee9/Work/MS_HF_cohort/data/07/"

# Parameters
Fr_diameter=19
R = Fr_diameter/6
L = 32

target_tags = [4]  # The elemTags you're interested in

# Load meshes
#mesh1 = pv.read("mesh1_with_normals.vtp")
mesh2 = pv.read(path+"2_motion/transformed-0.vtk") # Is the transformed data
# Step 1: Filter mesh2 based on elemTags
if "elemTag" not in mesh2.cell_data:
    raise ValueError("mesh2 does not contain 'elemTag' in cell_data")

mask = mesh2.cell_data['elemTag'] == 40
mesh1=mesh2.extract_cells(mask) # Corresponds to the mesh with the sparse points to anchor the cylinder + normals on this mesh

tags = mesh2.cell_data["elemTag"]
mask = np.isin(tags, target_tags)
filtered_mesh2 = mesh2.extract_cells(mask)

# Step 2: Get normals from mesh1
normals = mesh1.point_data.get("Normals")
if normals is None:
    raise ValueError("mesh1 does not contain 'Normals'")

N = 500
new_points   = mesh1.points[::N]
new_normals  = normals[::N]

# Step 3: Perform cylinder overlap check
overlap_flags = []

for point, normal in zip(new_points, new_normals):
    normal = normal / np.linalg.norm(normal)
    print(f'Point: {point}')
    print(f'Normal: {normal}')
    # Center the cylinder
    center = point + (normal * (L / 2.0))

    # Build the cylinder
    cylinder = pv.Cylinder(center=center, direction=normal, radius=R, height=L)

    # Check intersection with filtered mesh2
    intersection = filtered_mesh2.clip_surface(cylinder, invert=False, compute_distance=False)
    print(f'Intersection: {intersection}')
    has_overlap = intersection.n_points > 0

    overlap_flags.append(has_overlap)

# Step 4: Save result
mesh1.point_data["cylinder_hits"] = np.array(overlap_flags, dtype=int)
mesh1.save(path+"2_motion/mesh1_with_filtered_hits.vtp")
#mesh1.plot(scalars="cylinder_hits", cmap="coolwarm")
