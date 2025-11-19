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

def check_collision_for_direction(strPos, direction, height, radius, RV, PM, TV, refRV):
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
    for ID in range(0, refRV.GetNumberOfPoints()):
        tstPoint = np.array(RV.GetPoint(ID))
        distance = np.sqrt(vtkMath.Distance2BetweenPoints(strPos, tstPoint))
        if distance < (radius * 2 * 1.3):
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
                       ntimes=10, cone_angle=0, num_cone_samples=10, save_csv=False, verbose=False):
    """
    Modified to support cone rotation analysis.
    
    New parameters:
    - cone_angle: half-angle of the cone in degrees (0 = no rotation)
    - num_cone_samples: number of directions to test within the cone
    """
    
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
    
    # New arrays for cone analysis
    collision_free_count = np.zeros(num_points)  # Number of collision-free orientations
    best_cone_angle = np.zeros(num_points)  # Best angle found (if any)
    has_collision_free = np.zeros(num_points)  # Binary: 1 if any collision-free orientation exists

    # Loop through time frames
    for j in range(0, ntimes):
        collisionArray = np.zeros(num_points)
        pmCollisionArray = np.zeros(num_points)
        tvCollisionArray = np.zeros(num_points)
        
        # New arrays for this frame
        frame_collision_free_count = np.zeros(num_points)
        frame_has_collision_free = np.zeros(num_points)
        
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
        
        # Loop through locations on RV wall
        for ptID in range(0, refRV.GetNumberOfPoints()):
            strPos = np.array(RV.GetPoint(ptID))
            normal = np.array(RV.GetPointData().GetArray("Normals").GetTuple(ptID))
            
            # Generate cone directions
            directions = generate_cone_directions(normal, cone_angle, num_cone_samples)
            
            collision_free_found = False
            best_angle_for_point = -1
            
            # Test each direction in the cone
            for dir_idx, direction in enumerate(directions):
                rv_col, pm_col, tv_col = check_collision_for_direction(
                    strPos, direction, height, radius, RV, PM, TV, refRV
                )
                
                # Check if this direction is collision-free
                any_collision = rv_col or pm_col or (tv_col if TV is not None else False)
                
                if not any_collision:
                    collision_free_found = True
                    frame_collision_free_count[ptID] += 1
                    if best_angle_for_point < 0:
                        # Calculate approximate angle from normal
                        if dir_idx == 0:
                            best_angle_for_point = 0
                        else:
                            best_angle_for_point = cone_angle
                
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
            
            # Update collision-free tracking
            if collision_free_found:
                frame_has_collision_free[ptID] = 1
                has_collision_free[ptID] = 1
                collision_free_count[ptID] += frame_collision_free_count[ptID]
                if best_angle_for_point >= 0:
                    best_cone_angle[ptID] = best_angle_for_point
        
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
        
        # Add cone analysis data
        frame_cf_vtk = numpy_support.numpy_to_vtk(frame_collision_free_count)
        frame_cf_vtk.SetName('Collision_Free_Count')
        RV.GetPointData().AddArray(frame_cf_vtk)
        
        frame_has_cf_vtk = numpy_support.numpy_to_vtk(frame_has_collision_free)
        frame_has_cf_vtk.SetName('Has_Collision_Free')
        RV.GetPointData().AddArray(frame_has_cf_vtk)
        
        outname = out_files + str(j) + '.vtk'
        writer = vtkPolyDataWriter()
        writer.SetFileName(outname)
        writer.SetInputData(RV)
        writer.Write()
        
        if verbose:
            num_cf = np.sum(frame_has_collision_free)
            print(f"[{j+1}/{ntimes}] Processed frame {j}: {num_cf}/{num_points} points have collision-free orientations")
    
    # Store aggregate results
    num_frames = ntimes
    
    # Standard collision data
    colParam_vtk = numpy_support.numpy_to_vtk(sumCollisions)
    colParam_vtk.SetName('RV_Collision')
    refRV.GetPointData().AddArray(colParam_vtk)

    pmColParam_vtk = numpy_support.numpy_to_vtk(sumPMCollisions)
    pmColParam_vtk.SetName('PM_Collision')
    refRV.GetPointData().AddArray(pmColParam_vtk)
    
    if TV_files is not None:
        tvColParam_vtk = numpy_support.numpy_to_vtk(sumTVCollisions)
        tvColParam_vtk.SetName('TV_Collision')
        refRV.GetPointData().AddArray(tvColParam_vtk)
    
    if TV_files is not None:
        sumCombinedCollisions = np.logical_or(np.logical_or(sumCollisions, sumPMCollisions), sumTVCollisions).astype(int)
    else:
        sumCombinedCollisions = np.logical_or(sumCollisions, sumPMCollisions).astype(int)
    
    combinedColParam_vtk = numpy_support.numpy_to_vtk(sumCombinedCollisions)
    combinedColParam_vtk.SetName('Combined_Collision')
    refRV.GetPointData().AddArray(combinedColParam_vtk)

    # Percentage collisions
    sumCollisions_percent = (sumCollisions / num_frames) * 100
    sumPMCollisions_percent = (sumPMCollisions / num_frames) * 100
    sumTVCollisions_percent = (sumTVCollisions / num_frames) * 100 if TV_files is not None else None
    sumCombinedCollisions_percent = (sumCombinedCollisions / num_frames) * 100

    colParam_percent_vtk = numpy_support.numpy_to_vtk(sumCollisions_percent)
    colParam_percent_vtk.SetName('RV_Collision_Percent')
    refRV.GetPointData().AddArray(colParam_percent_vtk)

    pmColParam_percent_vtk = numpy_support.numpy_to_vtk(sumPMCollisions_percent)
    pmColParam_percent_vtk.SetName('PM_Collision_Percent')
    refRV.GetPointData().AddArray(pmColParam_percent_vtk)

    if TV_files is not None:
        tvColParam_percent_vtk = numpy_support.numpy_to_vtk(sumTVCollisions_percent)
        tvColParam_percent_vtk.SetName('TV_Collision_Percent')
        refRV.GetPointData().AddArray(tvColParam_percent_vtk)

    combinedColParam_percent_vtk = numpy_support.numpy_to_vtk(sumCombinedCollisions_percent)
    combinedColParam_percent_vtk.SetName('Combined_Collision_Percent')
    refRV.GetPointData().AddArray(combinedColParam_percent_vtk)
    
    # Add cone analysis results
    has_cf_vtk = numpy_support.numpy_to_vtk(has_collision_free)
    has_cf_vtk.SetName('Has_Collision_Free_Orientation')
    refRV.GetPointData().AddArray(has_cf_vtk)
    
    cf_count_vtk = numpy_support.numpy_to_vtk(collision_free_count)
    cf_count_vtk.SetName('Total_Collision_Free_Count')
    refRV.GetPointData().AddArray(cf_count_vtk)
    
    best_angle_vtk = numpy_support.numpy_to_vtk(best_cone_angle)
    best_angle_vtk.SetName('Best_Cone_Angle')
    refRV.GetPointData().AddArray(best_angle_vtk)
    
    # Calculate percentage of collision-free orientations
    collision_free_percent = (collision_free_count / (num_frames * num_cone_samples)) * 100
    cf_percent_vtk = numpy_support.numpy_to_vtk(collision_free_percent)
    cf_percent_vtk.SetName('Collision_Free_Percent')
    refRV.GetPointData().AddArray(cf_percent_vtk)
    
    outname = out_files + 'all_times.vtk'
    writer = vtkPolyDataWriter()
    writer.SetFileName(outname)
    writer.SetInputData(refRV)
    writer.Write()
    
    # Save CSV summary
    if save_csv:
        csv_outname = out_files + 'collision_summary.csv'
        with open(csv_outname, mode='w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            header = ['PointID', 'RV_Collision_Percent', 'PM_Collision_Percent']
            if TV_files is not None:
                header.append('TV_Collision_Percent')
            header.extend(['Combined_Collision_Percent', 'Has_Collision_Free', 
                          'Collision_Free_Percent', 'Best_Cone_Angle'])
            writer.writerow(header)
            
            for i in range(refRV.GetNumberOfPoints()):
                row = [i, sumCollisions_percent[i], sumPMCollisions_percent[i]]
                if TV_files is not None:
                    row.append(sumTVCollisions_percent[i])
                row.extend([sumCombinedCollisions_percent[i], has_collision_free[i],
                           collision_free_percent[i], best_cone_angle[i]])
                writer.writerow(row)
        
        if verbose:
            print(f"CSV summary saved to {csv_outname}")
            total_cf = np.sum(has_collision_free)
            print(f"\nSummary: {total_cf}/{num_points} points ({100*total_cf/num_points:.1f}%) have at least one collision-free orientation")


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
                       save_csv=args.save_csv, verbose=args.verbose)