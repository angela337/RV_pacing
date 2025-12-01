import numpy as np
from xml.dom import minidom
from vtk import * 
from vtk.util import numpy_support
import sys
import argparse
import os
import csv

def cylTest(pt1, pt2, testpt, length_sq, radius_sq):
    dx = pt2[0] - pt1[0];
    dy = pt2[1] - pt1[1];
    dz = pt2[2] - pt1[2];
    pdx = testpt[0] - pt1[0];
    pdy = testpt[1] - pt1[1];
    pdz = testpt[2] - pt1[2];
    dot = pdx * dx + pdy * dy + pdz * dz;
    if (dot < 0.0 or dot > length_sq): 
        return 0;
    else: 
        dsq = (pdx*pdx + pdy*pdy + pdz*pdz) - dot*dot/length_sq;
        if (dsq > radius_sq):
            return 0;
        else:
            return 1;

def rotate_vector_axis_angle(vector, axis, angle_deg):
    """
    Rotate a vector around an arbitrary axis by angle_deg degrees.
    Uses Rodrigues' rotation formula.
    """
    angle_rad = np.radians(angle_deg)
    axis = axis / np.linalg.norm(axis)  # Normalize axis
    
    cos_angle = np.cos(angle_rad)
    sin_angle = np.sin(angle_rad)
    
    # Rodrigues' rotation formula
    rotated = (vector * cos_angle + 
               np.cross(axis, vector) * sin_angle + 
               axis * np.dot(axis, vector) * (1 - cos_angle))
    
    return rotated

def generate_cone_directions(normal, cone_angle_deg, num_samples):
    """
    Generate directions within a cone around the normal vector.
    
    Parameters:
    - normal: base direction (surface normal)
    - cone_angle_deg: half-angle of the cone in degrees
    - num_samples: number of directions to sample
    
    Returns:
    - List of normalized direction vectors
    """
    if cone_angle_deg == 0 or num_samples <= 1:
        return [normal]
    
    directions = [normal]  # Always include the original normal
    
    # Create two perpendicular vectors to the normal
    if abs(normal[0]) < 0.9:
        perp1 = np.cross(normal, np.array([1, 0, 0]))
    else:
        perp1 = np.cross(normal, np.array([0, 1, 0]))
    perp1 = perp1 / np.linalg.norm(perp1)
    perp2 = np.cross(normal, perp1)
    perp2 = perp2 / np.linalg.norm(perp2)
    
    # Generate directions in a circular pattern around the cone
    num_ring_samples = num_samples - 1  # Subtract 1 since we already added the center
    for i in range(num_ring_samples):
        angle = 2 * np.pi * i / num_ring_samples
        
        # Create a direction on the cone edge
        # Rotate the normal by cone_angle_deg around an axis in the perpendicular plane
        rotation_axis = perp1 * np.cos(angle) + perp2 * np.sin(angle)
        rotated_dir = rotate_vector_axis_angle(normal, rotation_axis, cone_angle_deg)
        rotated_dir = rotated_dir / np.linalg.norm(rotated_dir)
        
        directions.append(rotated_dir)
    
    return directions

def check_collision_for_direction(strPos, direction, height, radius, RV, PM, TV, refRV,septum_point_ids=None):
    """
    Check if a cylinder in a given direction collides with any structures.
    
    Returns:
    - (rv_collision, pm_collision, tv_collision) as boolean tuple
    """
    endPos = strPos + height * direction
    
    rv_collision = False
    pm_collision = False
    tv_collision = False
    
    # Check RV wall collision
    for ID in range(0, RV.GetNumberOfPoints()):
        tstPoint = np.array(RV.GetPoint(ID))
        distance = np.sqrt(vtkMath.Distance2BetweenPoints(strPos, tstPoint))
        exclusion_distance = 10
        if distance < exclusion_distance: #(radius * 2): # If distance for the test point is too close to the attachment point - don't check these points 
            continue        
        if distance > 1.1*height:
            continue
        if septum_point_ids is not None and ID in septum_point_ids: # Don't test for collision against septum points. 
            continue
        result = cylTest(strPos, endPos, tstPoint, pow(height, 2), pow(radius, 2))
        if result:
            rv_collision = True
            break
    
    # Check PM collision
    for pmID in range(0, PM.GetNumberOfPoints()):
        pmPoint = np.array(PM.GetPoint(pmID))
        result = cylTest(strPos, endPos, pmPoint, pow(height, 2), pow(radius, 2))
        if result:
            pm_collision = True
            break
    
    # Check TV collision if available
    if TV is not None:
        for tvID in range(0, TV.GetNumberOfPoints()):
            tvPoint = np.array(TV.GetPoint(tvID))
            result = cylTest(strPos, endPos, tvPoint, pow(height, 2), pow(radius, 2))
            if result:
                tv_collision = True
                break
    
    return rv_collision, pm_collision, tv_collision

def generateLocationMap(RV_files, PM_files, TV_files, out_files, radius=6.5/2, height=42, 
                       ntimes=10, cone_angle=0, num_cone_samples=10, save_csv=False, verbose=False,
                       RV_files_smooth=None):
    """
    Modified to support cone rotation analysis with collision percentages.
    
    New parameters:
    - cone_angle: half-angle of the cone in degrees (0 = no rotation)
    - num_cone_samples: number of directions to test within the cone
    """
    print(f'Cone angle: {cone_angle}')
    print(f'Num cone samples: {num_cone_samples}')
    # Load reference meshes
    reader = vtkPolyDataReader()
    RV0_file = RV_files + "0.vtk"
    reader.SetFileName(RV0_file)
    reader.Update()
    refRV = vtkPolyData()
    refRV.ShallowCopy(reader.GetOutput())
    
    PM_reader = vtkPolyDataReader()
    PM0_file = PM_files + "0.vtk"
    PM_reader.SetFileName(PM0_file)
    PM_reader.Update()
    refPM = vtkPolyData()
    refPM.ShallowCopy(PM_reader.GetOutput())
    
    if TV_files is not None:
        TV_reader = vtkPolyDataReader()
        TV0_file = TV_files + "0.vtk"
        TV_reader.SetFileName(TV0_file)
        TV_reader.Update()
        refTV = vtkPolyData()
        refTV.ShallowCopy(TV_reader.GetOutput())

    # Initialize arrays
    num_points = refRV.GetNumberOfPoints()
    sumCollisions = np.zeros(num_points)
    sumPMCollisions = np.zeros(num_points)
    sumTVCollisions = np.zeros(num_points)
    sumCombinedCollisions = np.zeros(num_points)
    
    # New arrays for cone collision tracking
    sumRVConeCollisions = np.zeros(num_points)
    sumPMConeCollisions = np.zeros(num_points)
    sumTVConeCollisions = np.zeros(num_points)
    sumCombinedConeCollisions = np.zeros(num_points)
    
    # CSV data collection
    csv_data = []

    # Loop through time frames
    for j in range(0, ntimes):
        collisionArray = np.zeros(num_points)
        pmCollisionArray = np.zeros(num_points)
        tvCollisionArray = np.zeros(num_points)
        
        # Cone collision assume collision and if there is no collision in any direction set to zero
        rvConeCollision = np.ones(num_points)
        pmConeCollision = np.ones(num_points)
        tvConeCollision = np.ones(num_points)
        combinedConeCollision = np.ones(num_points)
        
        # Load meshes at this time point
        RVN_file = RV_files + str(j) + '.vtk'        
        if not os.path.isfile(RVN_file):
            print(f"Error: RV file {RVN_file} does not exist. Skipping frame {j}.")
            continue
        
        if verbose: 
            print(f"[{j+1}/{ntimes}] Loading RV: {RVN_file}")

        reader = vtkPolyDataReader()
        reader.SetFileName(RVN_file)
        reader.Update()
        RV = vtkPolyData().NewInstance()
        RV.ShallowCopy(reader.GetOutput())
        
        PMN_file = PM_files + str(j) + '.vtk'
        if not os.path.isfile(PMN_file):
            print(f"Error: PM file {PMN_file} does not exist. Skipping frame {j}.")
            continue
        if verbose: 
            print(f"[{j+1}/{ntimes}] Loading PM: {PMN_file}")
        PM_reader = vtkPolyDataReader()
        PM_reader.SetFileName(PMN_file)
        PM_reader.Update()
        PM = vtkPolyData().NewInstance()
        PM.ShallowCopy(PM_reader.GetOutput())
        
        TV = None
        if TV_files is not None:
            TVN_file = TV_files + str(j) + '.vtk'
            if not os.path.isfile(TVN_file):
                print(f"Error: TV file {TVN_file} name given, but does not exist. Skipping frame {j}.")
                continue
            if verbose: 
                print(f"[{j+1}/{ntimes}] Loading TV: {TVN_file}")
            TV_reader = vtkPolyDataReader()
            TV_reader.SetFileName(TVN_file)
            TV_reader.Update()
            TV = vtkPolyData().NewInstance()
            TV.ShallowCopy(TV_reader.GetOutput())

        # Generate normals for RV
        normalGenerator = vtkPolyDataNormals()
        normalGenerator.SetInputData(RV)
        normalGenerator.ComputePointNormalsOn()
        normalGenerator.ComputeCellNormalsOff()
        normalGenerator.AutoOrientNormalsOn()
        normalGenerator.FlipNormalsOn()
        normalGenerator.Update()
        RV = normalGenerator.GetOutput()
        
        # 
        # Get cell data and filter for elemTag == 3
        cell_data = RV.GetCellData()
        elem_tag_array = cell_data.GetArray('elemTag')
        # Get point IDs from cells with elemTag == 3
        septum_point_ids = set()
        for cellID in range(RV.GetNumberOfCells()):
            if elem_tag_array.GetValue(cellID) == 3:
                cell = RV.GetCell(cellID)
                for i in range(cell.GetNumberOfPoints()):
                    septum_point_ids.add(cell.GetPointId(i))

        verbose_point_flag=True
        # Iterate over all points, but only process those NOT in elemTag=3
        for ptID in range(refRV.GetNumberOfPoints()):
            if ptID not in septum_point_ids:
                tvConeCollision[ptID] = 0
                rvConeCollision[ptID] = 0
                pmConeCollision[ptID] = 0
                combinedConeCollision[ptID] = 0
                continue
                
 
            strPos = np.array(RV.GetPoint(ptID))
            normal = np.array(RV.GetPointData().GetArray("Normals").GetTuple(ptID))
            
            # Generate cone directions
            directions = generate_cone_directions(normal, cone_angle, num_cone_samples)
            if verbose and verbose_point_flag: 
                print(f'pt{ptID} directions: {directions}')
            
            # Test each direction in the cone
            for dir_idx, direction in enumerate(directions):
                if verbose and verbose_point_flag:                     
                    print(f'Testing direction {dir_idx}: {direction}')

                rv_col, pm_col, tv_col = check_collision_for_direction(
                    strPos, direction, height, radius, RV, PM, TV, refRV,septum_point_ids
                )
                if verbose and verbose_point_flag: 
                    print(f'rv_col: {rv_col}, pm_col: {pm_col}, tv_col: {tv_col}')
                # For the first direction (original normal), record standard collisions
                if dir_idx == 0:
                    if rv_col:
                        collisionArray[ptID] = 1
                        sumCollisions[ptID] = 1
                    if pm_col:
                        pmCollisionArray[ptID] = 1
                        sumPMCollisions[ptID] = 1
                    if tv_col and TV is not None:
                        tvCollisionArray[ptID] = 1
                        sumTVCollisions[ptID] = 1
                
                # If any direction does not collide - set collision to 0 for the cone code
                if not rv_col:
                    rvConeCollision[ptID] = 0
                if not pm_col:
                    pmConeCollision[ptID] = 0
                if not tv_col and TV is not None:
                    tvConeCollision[ptID] = 0
                
                # Combined collision for any direction in the cone
                #no_combined_collision = not rv_col and not pm_col and (not tv_col if TV is not None else True)
                no_combined_collision = not rvConeCollision[ptID] and not pmConeCollision[ptID] and (not tvConeCollision[ptID] if TV is not None else True)
                
                if no_combined_collision:
                    combinedConeCollision[ptID] = 0
                    # If any directions gives no collision then skip
                    continue 
                
            if verbose_point_flag: 
                verbose_point_flag=False # Only print verbose output for first septal point 
            if verbose and ptID % 1000 == 0: 
                print(f"Time[{j+1}/{ntimes}]: Processed {ptID} points out of {refRV.GetNumberOfPoints()}", flush=True)

        # Calculate cone collision percentages for this frame
        num_directions = len(directions) if directions is not None and len(directions) > 0 else num_cone_samples
        rvConeCollisionPercent = rvConeCollision
        pmConeCollisionPercent = pmConeCollision
        tvConeCollisionPercent = tvConeCollision if TV is not None else np.zeros(num_points)
        combinedConeCollisionPercent = combinedConeCollision 
        
        # Update cumulative cone collision sums
        sumRVConeCollisions += rvConeCollision
        sumPMConeCollisions += pmConeCollision
        sumTVConeCollisions += tvConeCollision
        sumCombinedConeCollisions += combinedConeCollision
        
        # Save results for this frame
        reader = vtkPolyDataReader()
        reader.SetFileName(RVN_file)
        reader.Update()
        RV = vtkPolyData().NewInstance()
        RV.ShallowCopy(reader.GetOutput())
        
        # Add standard collision data
        colParam_vtk = numpy_support.numpy_to_vtk(collisionArray)
        colParam_vtk.SetName('RV_Collision')
        RV.GetPointData().AddArray(colParam_vtk)
        
        pmColParam_vtk = numpy_support.numpy_to_vtk(pmCollisionArray)
        pmColParam_vtk.SetName('PM_Collision')
        RV.GetPointData().AddArray(pmColParam_vtk)
        
        if TV_files is not None:
            tvColParam_vtk = numpy_support.numpy_to_vtk(tvCollisionArray)
            tvColParam_vtk.SetName('TV_Collision')
            RV.GetPointData().AddArray(tvColParam_vtk)
        
        # Combine collision data
        if TV_files is not None:
            combinedCollisionArray = np.logical_or(np.logical_or(collisionArray, pmCollisionArray), tvCollisionArray).astype(int)
        else:
            combinedCollisionArray = np.logical_or(collisionArray, pmCollisionArray).astype(int)
        
        sumCombinedCollisions += combinedCollisionArray
        
        combinedColParam_vtk = numpy_support.numpy_to_vtk(combinedCollisionArray)
        combinedColParam_vtk.SetName('Combined_Collision')
        RV.GetPointData().AddArray(combinedColParam_vtk)
        
        # Add cone collision percentage data
        rvConePercent_vtk = numpy_support.numpy_to_vtk(rvConeCollisionPercent)
        rvConePercent_vtk.SetName('RV_Collision_Cone_Percent')
        RV.GetPointData().AddArray(rvConePercent_vtk)
        
        pmConePercent_vtk = numpy_support.numpy_to_vtk(pmConeCollisionPercent)
        pmConePercent_vtk.SetName('PM_Collision_Cone_Percent')
        RV.GetPointData().AddArray(pmConePercent_vtk)
        
        if TV_files is not None:
            tvConePercent_vtk = numpy_support.numpy_to_vtk(tvConeCollisionPercent)
            tvConePercent_vtk.SetName('TV_Collision_Cone_Percent')
            RV.GetPointData().AddArray(tvConePercent_vtk)
        
        combinedConePercent_vtk = numpy_support.numpy_to_vtk(combinedConeCollisionPercent)
        combinedConePercent_vtk.SetName('Combined_Collision_Cone_Percent')
        RV.GetPointData().AddArray(combinedConePercent_vtk)
        
        # Write VTK file
        outname = out_files + str(j) + '.vtk'
        writer = vtkPolyDataWriter()
        writer.SetFileName(outname)
        writer.SetInputData(RV)
        writer.Write()
        
        if verbose:
            print(f"[{j+1}/{ntimes}] Processed frame {j}")
    
    # Calculate overall percentages across all frames
    RV_Collision_Percent = (sumCollisions / ntimes) * 100
    PM_Collision_Percent = (sumPMCollisions / ntimes) * 100
    TV_Collision_Percent = (sumTVCollisions / ntimes) * 100 if TV_files is not None else np.zeros(num_points)
    Combined_Collision_Percent = (sumCombinedCollisions / ntimes) * 100
    
    # Calculate overall cone collision percentages
    total_cone_samples = ntimes #* num_cone_samples
    RV_Collision_Cone_Percent = (sumRVConeCollisions / total_cone_samples) * 100
    PM_Collision_Cone_Percent = (sumPMConeCollisions / total_cone_samples) * 100
    TV_Collision_Cone_Percent = (sumTVConeCollisions / total_cone_samples) * 100 if TV_files is not None else np.zeros(num_points)
    Combined_Collision_Cone_Percent = (sumCombinedConeCollisions / total_cone_samples) * 100
    
    if verbose: 
        print('Add summary arrays to reference mesh')
    # Add summary arrays to reference mesh
    reader = vtkPolyDataReader()
    reader.SetFileName(RV0_file)
    reader.Update()
    RV_summary = vtkPolyData()
    RV_summary.ShallowCopy(reader.GetOutput())
    
    # Add standard collision percentages
    rv_pct_vtk = numpy_support.numpy_to_vtk(RV_Collision_Percent)
    rv_pct_vtk.SetName('RV_Collision_Percent')
    RV_summary.GetPointData().AddArray(rv_pct_vtk)
    
    pm_pct_vtk = numpy_support.numpy_to_vtk(PM_Collision_Percent)
    pm_pct_vtk.SetName('PM_Collision_Percent')
    RV_summary.GetPointData().AddArray(pm_pct_vtk)
    
    if TV_files is not None:
        tv_pct_vtk = numpy_support.numpy_to_vtk(TV_Collision_Percent)
        tv_pct_vtk.SetName('TV_Collision_Percent')
        RV_summary.GetPointData().AddArray(tv_pct_vtk)
    
    combined_pct_vtk = numpy_support.numpy_to_vtk(Combined_Collision_Percent)
    combined_pct_vtk.SetName('Combined_Collision_Percent')
    RV_summary.GetPointData().AddArray(combined_pct_vtk)
    
    # Add cone collision percentages
    rv_cone_pct_vtk = numpy_support.numpy_to_vtk(RV_Collision_Cone_Percent)
    rv_cone_pct_vtk.SetName('RV_Collision_Cone_Percent')
    RV_summary.GetPointData().AddArray(rv_cone_pct_vtk)
    
    pm_cone_pct_vtk = numpy_support.numpy_to_vtk(PM_Collision_Cone_Percent)
    pm_cone_pct_vtk.SetName('PM_Collision_Cone_Percent')
    RV_summary.GetPointData().AddArray(pm_cone_pct_vtk)
    
    if TV_files is not None:
        tv_cone_pct_vtk = numpy_support.numpy_to_vtk(TV_Collision_Cone_Percent)
        tv_cone_pct_vtk.SetName('TV_Collision_Cone_Percent')
        RV_summary.GetPointData().AddArray(tv_cone_pct_vtk)
    
    combined_cone_pct_vtk = numpy_support.numpy_to_vtk(Combined_Collision_Cone_Percent)
    combined_cone_pct_vtk.SetName('Combined_Collision_Cone_Percent')
    RV_summary.GetPointData().AddArray(combined_cone_pct_vtk)
    
    # Write to RV_collision-all_times.vtk file
    all_times_outname = out_files + 'all_times.vtk'
    writer = vtkPolyDataWriter()
    writer.SetFileName(all_times_outname)
    writer.SetInputData(RV_summary)
    writer.Write()
    
    print(f"All times summary file saved: {all_times_outname}")
    
    # Save CSV if requested
    if save_csv:
        csv_outname = out_files + 'all_times.csv'
        with open(csv_outname, 'w', newline='') as csvfile:
            fieldnames = ['Point_ID', 'RV_Collision_Percent', 'PM_Collision_Percent', 
                         'Combined_Collision_Percent', 'RV_Collision_Cone_Percent',
                         'PM_Collision_Cone_Percent', 'Combined_Collision_Cone_Percent']
            if TV_files is not None:
                fieldnames.insert(3, 'TV_Collision_Percent')
                fieldnames.insert(7, 'TV_Collision_Cone_Percent')
            
            writer_csv = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer_csv.writeheader()
            
            for ptID in range(num_points):
                row = {
                    'Point_ID': ptID,
                    'RV_Collision_Percent': RV_Collision_Percent[ptID],
                    'PM_Collision_Percent': PM_Collision_Percent[ptID],
                    'Combined_Collision_Percent': Combined_Collision_Percent[ptID],
                    'RV_Collision_Cone_Percent': RV_Collision_Cone_Percent[ptID],
                    'PM_Collision_Cone_Percent': PM_Collision_Cone_Percent[ptID],
                    'Combined_Collision_Cone_Percent': Combined_Collision_Cone_Percent[ptID]
                }
                if TV_files is not None:
                    row['TV_Collision_Percent'] = TV_Collision_Percent[ptID]
                    row['TV_Collision_Cone_Percent'] = TV_Collision_Cone_Percent[ptID]
                
                writer_csv.writerow(row)
        
        print(f"CSV file saved: {csv_outname}")
    
    return RV_summary

def get_specs(device_name, new_L): 
    devices = {
        "Micra": {"D": 6.7, "L": 25.9},
        "AveirAR": {"D": 6.5, "L": 32.2},
        "AveirVR": {"D": 6.5, "L": 38}
    }
    
    if device_name not in devices:
        print(f"Error: device '{device_name}' not found in known devices.")
        print("Available devices:", ", ".join(devices.keys()))
        sys.exit(1)

    D = devices[device_name]['D']
    L = devices[device_name]['L']
    vol = np.pi * ((D / 2) ** 2) * L
    new_R = np.sqrt(vol / (np.pi * new_L))
    
    return new_R


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Track the motion collision of a cylinder on the RV wall against RV wall and RV structures',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-RV_files', help='Basename to decimated RV wall vtk file', default='RV_dec-')
    parser.add_argument('-RV_files_smooth', help='Basename to smooth high resolution RV wall vtk file', default=None) #'RV_smth-'
    parser.add_argument('-PM_files', help='Basename to PM files (papillary muscles and cone to Tricuspid valve ring) vtk files', default='PM-')    
    parser.add_argument('-TV_files', help='Basename to Tricuspid valve ring vtk files', default=None)
    parser.add_argument('-out_files', help='Basename to output vtk files', default='RV_collision-')
    parser.add_argument('-ntimes', help='Number of cine time points for files', default=10, type=int)
    parser.add_argument('-device', default='Aveir10', help='Device name')
    parser.add_argument('-L', default=42, help='new length of device to test', type=float)
    parser.add_argument('-cone_angle', default=0, type=float, 
                       help='Half-angle of cone rotation in degrees (0 = no rotation, e.g., 10 for ±10 degree cone)')
    parser.add_argument('-num_cone_samples', default=10, type=int,
                       help='Number of directions to sample within the cone')
    parser.add_argument('--save_csv', action='store_true', help='Save a CSV summary of percent collisions')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')                        
    
    args = parser.parse_args()
    
    RV_files = args.RV_files
    RV_files_smooth=args.RV_files_smooth
    PM_files = args.PM_files
    TV_files = args.TV_files
    out_files = args.out_files
    ntimes = args.ntimes
    device = args.device
    
    height = args.L
    radius = get_specs(device, height)
    
    if args.verbose: 
        print(f'Running sims for device: {device}')
        print(f'Device dimensions: radius={radius:.2f}mm, length={height}mm')
        if args.cone_angle > 0:
            print(f'Cone rotation: ±{args.cone_angle}° with {args.num_cone_samples} samples')
    
    generateLocationMap(RV_files, PM_files, TV_files, out_files, radius, height, ntimes, 
                        cone_angle=args.cone_angle, num_cone_samples=args.num_cone_samples,
                       save_csv=args.save_csv, verbose=args.verbose,RV_files_smooth=RV_files_smooth)