import nibabel as nib
import numpy as np
import argparse
from scipy.ndimage import grey_dilation
from pathlib import Path
import sys

def define_structure(radius=1): 

    radius = radius+1
    diameter = 2 * radius + 1
    center = radius

    x, y, z = np.ogrid[:diameter, :diameter, :diameter]
    dist_squared = (x - center)**2 + (y - center)**2 + (z - center)**2

    # Strict spherical structuring element (Euclidean radius ≤ 1)
    structure = dist_squared <= radius**2
    structure=structure[1:-1,1:-1,1:-1]

    return structure

def dilate_image(image, radius=1):
    """
    Apply 3D grey-level dilation with 1-voxel structuring element.
    
    Args:
        image (np.ndarray): Input 3D image array
        
    Returns:
        np.ndarray: Dilated image
    """
    # Define a 3D structuring element (1 voxel in each direction)
    structure = define_structure(radius)
    # Apply grey-level dilation (1 voxel)
    dilated = grey_dilation(image, footprint=structure)
    return dilated

def extract_labels_dilate(maskfile, outfile=None, dilated_outfile=None, 
                         target_labels=[1, 2, 4, 22], map_target_labels=None, radius=1):
    """
    Extract specific labels from a mask file and optionally create dilated version.
    
    Args:
        maskfile (str): Path to input mask file
        outfile (str, optional): Path for output mask (non-dilated)
        dilated_outfile (str, optional): Path for dilated output mask
        target_labels (list): List of label values to extract
        map_target_labels (list, optional): New values to map target_labels to
        
    Returns:
        int: 0 for success, 1 for error
    """
    try:
        # Load mask image
        mask_img = nib.load(maskfile)
        mask_img.set_sform(mask_img.get_qform(), code=1)
        
        mask_data = mask_img.get_fdata()
        mask_data = mask_data.astype(np.uint8)
        
        # Create binary mask: 1 where label is in target list, else 0
        binary_mask = np.isin(mask_data, target_labels).astype(np.uint8)
        print(f'Created binary mask from labels: {target_labels}')
        
        # Apply mask (binary mask: keep where mask > 0)
        masked_data = np.where(binary_mask > 0, mask_data, 0)
        
        # Map labels if requested
        if map_target_labels is not None:
            if len(map_target_labels) != len(target_labels):
                print(f"❌ Error: Length mismatch - target_labels: {len(target_labels)}, "
                      f"map_target_labels: {len(map_target_labels)}")
                return 1
                
            for i, label in enumerate(target_labels):
                maptolabel = map_target_labels[i]
                masked_data = np.where(masked_data == label, maptolabel, masked_data)
                print(f"Mapped label {label} -> {maptolabel}")
        
        # Save non-dilated version if requested
        if outfile is not None:
            masked_img = nib.Nifti1Image(masked_data, affine=mask_img.affine, 
                                       header=mask_img.header)
            nib.save(masked_img, outfile)
            print(f"✅ Saved non-dilated mask: {outfile}")

        
        # Save dilated version if requested
        if dilated_outfile is not None:
            dilated_data = dilate_image(masked_data, radius)
            dilated_img = nib.Nifti1Image(dilated_data, affine=mask_img.affine, 
                                        header=mask_img.header)
            nib.save(dilated_img, dilated_outfile)
            print(f"✅ Saved dilated mask: {dilated_outfile}")
            return 0
        else: 
            return dilated_data
        
    except Exception as e:
        print(f"❌ Error processing {maskfile}: {str(e)}")
        return 1

def main():
    parser = argparse.ArgumentParser(
        description='Extract blood pool, LV and BiV regions from segmentation mask into new images',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument('-maskfile', 
                       help='Path to input mask file',
                       default='./all_labels_mask_downsample.nii.gz')
    parser.add_argument('-bp_outfile', 
                       help='Output filename for dilated blood pool image (eg BloodPools_Dilated_by_1.nii)',
                       default=None)
    parser.add_argument('-biv', 
                       help='Output filename for BiV masked image (eg ./BiV_masked.nii)',
                       default=None)
    parser.add_argument('-biv_dil', 
                       help='Output filename for dilated BiV masked image (eg ./BiV_masked_Dilated_by_1.nii)',
                       default=None)
    parser.add_argument('-lv_outfile',help='Output filename for dilated LV wall (eg ./LVwall_Dilated_by_1.nii)', 
                        default=None)
    
    args = parser.parse_args()
    
    maskfile = args.maskfile
    bp_outfile = args.bp_outfile
    biv_outfile = args.biv
    biv_dil_outfile = args.biv_dil
    lv_outfile=args.lv_outfile
    
    # Check if mask file exists
    if not Path(maskfile).exists():
        print(f"❌ Error: Mask file does not exist: {maskfile}")
        sys.exit(1)
    else:
        print(f"✅ Mask file exists: {maskfile}")
    
    if lv_outfile is not None: 
        # Process LV image
        print("\n=== Processing LV ===")
        lv_target_labels = [3,11]  # LVBP, LVBP, RVBP, TCV
        lv_map_target_labels = [3,3]  # Map to new values
        
        _ = extract_labels_dilate(
            maskfile=maskfile,
            outfile=None,  # Only create dilated version
            dilated_outfile=lv_outfile,
            target_labels=lv_target_labels,
            map_target_labels=lv_map_target_labels,
            radius=1
        )

        _ = extract_labels_dilate(
            maskfile=lv_outfile,
            outfile=None,  # Only create dilated version
            dilated_outfile=lv_outfile,
            target_labels=lv_target_labels,
            map_target_labels=lv_map_target_labels,
            radius=3
        )

        _ = extract_labels_dilate(
            maskfile=lv_outfile,
            outfile=None,  # Only create dilated version
            dilated_outfile=lv_outfile,
            target_labels=lv_target_labels,
            map_target_labels=lv_map_target_labels,
            radius=3
        )

        _ = extract_labels_dilate(
            maskfile=lv_outfile,
            outfile=None,  # Only create dilated version
            dilated_outfile=lv_outfile,
            target_labels=lv_target_labels,
            map_target_labels=lv_map_target_labels,
            radius=3
        )

        #if result != 0:
        #    print("❌ Failed to process LV wall")
        #    sys.exit(1)

    if bp_outfile is not None: 
        # Process blood pool image
        print("\n=== Processing Blood Pool ===")
        bp_target_labels = [1, 2, 4, 22]  # LVBP, LVBP, RVBP, TCV
        bp_map_target_labels = [10, 10, 40, 30]  # Map to new values
        
        result = extract_labels_dilate(
            maskfile=maskfile,
            outfile=None,  # Only create dilated version
            dilated_outfile=bp_outfile,
            target_labels=bp_target_labels,
            map_target_labels=bp_map_target_labels
        )
        
        if result != 0:
            print("❌ Failed to process blood pool")
            sys.exit(1)
    
    # Process BiV (Biventricular) image
    if biv_dil_outfile is not None: 
        print("\n=== Processing BiV ===")
        biv_target_labels = [3, 5]  # BiV labels
        
        result = extract_labels_dilate(
            maskfile=maskfile,
            outfile=biv_outfile,
            dilated_outfile=biv_dil_outfile,
            target_labels=biv_target_labels,
            map_target_labels=None  # Keep original labels
        )
        
        if result != 0:
            print("❌ Failed to process BiV")
            sys.exit(1)
        
        print("\n✅ All processing completed successfully!")

if __name__ == "__main__":
    main()