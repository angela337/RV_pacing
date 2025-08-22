import vtk
import SimpleITK as sitk
import numpy as np
from vtk.util import numpy_support
import argparse
import os


def sitk2vtk_label_preserved(img, target_values=None):
    """Convert a SimpleITK image to a VTK polydata mesh with cell_data['elemTag'] from intensity values."""

    # Convert to numpy
    img_np = sitk.GetArrayFromImage(img)

    # Mask non-target values if specified, but keep original values for matching
    if target_values is not None:
        mask = np.isin(img_np, target_values)
        img_np = np.where(mask, img_np, 0)

    # Convert back to SimpleITK and copy metadata
    img_filtered = sitk.GetImageFromArray(img_np)
    img_filtered.CopyInformation(img)

    # Convert to VTK image
    vtk_image = vtk.vtkImageData()
    shape = img_np.shape
    spacing = img.GetSpacing()
    origin = img.GetOrigin()

    vtk_image.SetDimensions(shape[::-1])
    vtk_image.SetSpacing(spacing)
    vtk_image.SetOrigin(origin)
    vtk_image.SetExtent(0, shape[2]-1, 0, shape[1]-1, 0, shape[0]-1)

    flat = img_np.flatten(order='C')
    vtk_data_array = numpy_support.numpy_to_vtk(flat, deep=True, array_type=vtk.VTK_FLOAT)
    vtk_image.GetPointData().SetScalars(vtk_data_array)

    # Marching cubes
    contour = vtk.vtkMarchingCubes()
    contour.SetInputData(vtk_image)
    contour.ComputeScalarsOn()  # Enable scalar computation to keep label information
    contour.SetValue(0, 1.0)
    contour.Update()

    # Get the output of marching cubes
    polydata = contour.GetOutput()
    point_scalars = polydata.GetPointData().GetScalars()

    # Convert point scalars to cell data (average per cell)
    cell_data = vtk.vtkFloatArray()
    cell_data.SetName("elemTag")
    cell_data.SetNumberOfComponents(1)
    cell_data.SetNumberOfTuples(polydata.GetNumberOfCells())

    for i in range(polydata.GetNumberOfCells()):
        cell = polydata.GetCell(i)
        pt_ids = cell.GetPointIds()
        vals = [point_scalars.GetTuple1(pt_ids.GetId(j)) for j in range(pt_ids.GetNumberOfIds())]
        avg_val = int(round(np.mean(vals)))
        cell_data.SetTuple1(i, avg_val)

    polydata.GetCellData().AddArray(cell_data)
    polydata.GetCellData().SetActiveScalars("elemTag")

    return polydata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert NIfTI image to VTK mesh with labels")
    parser.add_argument("niifile", help="Input NIfTI image")
    parser.add_argument("outvtk", help="Output VTK mesh filename")
    parser.add_argument("--values", nargs="*", type=int, default=None, help="Intensity values to keep")
    parser.add_argument("--binary", action="store_true", help="Write binary VTK file")
    args = parser.parse_args()

    if not os.path.isfile(args.niifile):
        raise FileNotFoundError(f"Input file {args.niifile} not found")

    # Read and optionally filter image
    img = sitk.ReadImage(args.niifile)
    polydata = sitk2vtk_label_preserved(img, target_values=args.values)

    # Save VTK file
    writer = vtk.vtkPolyDataWriter()
    writer.SetFileName(args.outvtk)
    writer.SetInputData(polydata)
    if args.binary:
        writer.SetFileTypeToBinary()
    else:
        writer.SetFileTypeToASCII()
    writer.Write()

    print(f"Saved mesh to {args.outvtk} with cell_data['elemTag']")
