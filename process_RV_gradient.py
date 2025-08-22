import nibabel as nib
from nilearn.image import resample_to_img
import numpy as np
import SimpleITK as sitk
from pathlib import Path
import argparse
import sys

def mask_gradient(dcmfile, maskfile, outfile, target_labels=[4,5,22,24]): 

        # Convert NRRD to NIfTI if needed       
        # convert_nrrd_to_nifti(maskfile.replace('.nii', '.nrrd'), maskfile)

    # Load the dcm image and the mask
    dcm_img = nib.load(dcmfile)
    dcm_img.set_sform(dcm_img.get_qform(), code=1)

    #print(dcm_img.header)
    mask_img = nib.load(maskfile)
    mask_img.set_sform(mask_img.get_qform(), code=1)
    #print(mask_img.header)
    # Resample mask to match dcm image space (voxel size, orientation, etc.)
    resampled_mask_img = resample_to_img(mask_img, dcm_img, interpolation='nearest', force_resample=True, copy_header=True)
    print('resample image')
    # Get data arrays
    dcm_data = dcm_img.get_fdata()
    mask_data = resampled_mask_img.get_fdata()

    # Define target labels # RV BP
    #target_labels = [4, 5, 22, 24]

    # Create binary mask: 1 where label is in target list, else 0
    binary_mask = np.isin(mask_data, target_labels).astype(np.uint8)
    print('create binary mask from labels')

    # Apply mask (binary mask: keep where mask > 0)
    masked_data = np.where(binary_mask > 0, dcm_data, 0)

    # Create new image with original affine and header
    # masked_img = nib.Nifti1Image(masked_data, affine=dcm_img.affine, header=dcm_img.header)

    # Save result
    # nib.save(masked_img, path+'dcm_masked.nii')
    
    # Gradient magnitude with Gaussian smoothing (sigma in image spacing units)
    img_sitk = sitk.GetImageFromArray(masked_data)

    sigma = 3.0
    gradient = sitk.GradientMagnitudeRecursiveGaussian(img_sitk, sigma)
    print('gradient edge detection')
    # Convert to NumPy array for display
    gradient_array = sitk.GetArrayViewFromImage(gradient)

    grad_mask_img = nib.Nifti1Image(gradient_array, affine=dcm_img.affine, header=dcm_img.header)
    
    nib.save(grad_mask_img, outfile)

    print('Saving: ' + outfile)


def main(): 
    parser = argparse.ArgumentParser(description='Process the dcm-0 image to pull out the RV BP and apply a gradient edge filter so that we can identify RV structures')
    parser.add_argument('dcmfile', help='dcm-0 filename', default='./dcm-0.nii')
    parser.add_argument('maskfile', help='Mask file', default='./all_labels_mask.nii')
    parser.add_argument('outfile', help='output file name for the dcm image that is masked on the RV with a gradient edge filter applied to RV BP', 
                        default='./dcm-masked_gradient.nii')    
    parser.add_argument(
        "--target_labels",
        type=int,
        nargs="+",
        default=[4, 5, 22, 24],
        help="List of target labels (default: [4, 5, 22, 24])"
    )

    args=parser.parse_args()

    dcmfile=args.dcmfile
    maskfile=args.maskfile
    outfile=args.outfile
    target_labels=args.target_labels
    
    # Check if mask file exists
    if not Path(maskfile).exists():
        print(f"❌ Error: Mask file does not exist: {maskfile}")
        sys.exit(1)
    else:
        print("Mask file exists")

    # Check if DICOM (dcm) file exists
    if not Path(dcmfile).exists():
        print(f"❌ Error: DICOM file does not exist: {dcmfile}")
        sys.exit(1)
    else:
        print("DICOM file exists")

    mask_gradient(dcmfile, maskfile, outfile, target_labels)

if __name__ == "__main__":
    main()