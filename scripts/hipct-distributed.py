import os
import zarr
import nibabel as nib
import numpy as np
import cv2
import dask.array as da
from dask.distributed import Client, LocalCluster
from skimage import exposure
from skimage.draw import disk

def setup_dask_cluster():
    """Initialize a local Dask cluster for distributed computation."""
    cluster = LocalCluster()
    client = Client(cluster)
    print("Dask cluster initialized")
    return client

def nifti_to_zarr(nifti_path, zarr_path):
    """Convert a NIfTI file to Zarr format."""
    img = nib.load(nifti_path)
    data = img.get_fdata()
    z = zarr.open(zarr_path, mode='w', shape=data.shape, dtype=data.dtype)
    z[:] = data
    print(f"Converted {nifti_path} to {zarr_path}")
    return z

def load_zarr_data(zarr_path):
    """Load data directly from an existing Zarr file."""
    zarr_data = zarr.open(zarr_path, mode='r')
    dask_data = da.from_zarr(zarr_data)
    print(f"Loaded Zarr dataset from {zarr_path}")
    return dask_data

def proportional_thresholding(data, lower_limit=0.01, upper_limit=0.99):
    """Apply proportional thresholding to remove low-intensity artifacts."""
    min_val, max_val = np.percentile(data, [lower_limit * 100, upper_limit * 100])
    data = np.clip(data, min_val, max_val)
    return (data - min_val) / (max_val - min_val)  # Normalize

def apply_clahe(slice_data):
    """Apply CLAHE to a 2D image slice."""
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply((slice_data * 255).astype(np.uint8))

def quantize_to_8bit(data, lower_percentile=2, upper_percentile=98):
    """Quantize data to 8-bit format based on percentiles."""
    min_val, max_val = np.percentile(data, [lower_percentile, upper_percentile])
    data = np.clip(data, min_val, max_val)
    return ((data - min_val) / (max_val - min_val) * 255).astype(np.uint8)

def generate_circular_mask(shape, diameter):
    """Generate a circular mask for a given shape."""
    mask = np.zeros(shape, dtype=np.uint8)
    center = (shape[0] // 2, shape[1] // 2)
    rr, cc = disk(center, diameter // 2)
    mask[rr, cc] = 1
    return mask

def process_3d_data(dask_data, output_path, mask_diameter=None):
    """Process 3D data with proportional thresholding, CLAHE, and quantization."""
    if mask_diameter:
        mask = generate_circular_mask(dask_data.shape[1:], mask_diameter)
        dask_data = dask_data * mask

    processed_slices = []
    for i in range(dask_data.shape[0]):
        slice_data = dask_data[i].compute()
        slice_data = proportional_thresholding(slice_data)
        slice_data = apply_clahe(slice_data)
        processed_slices.append(quantize_to_8bit(slice_data))

    processed_data = np.stack(processed_slices, axis=0)
    zarr.save(output_path, processed_data)
    print(f"Processed data saved to {output_path}")

if __name__ == "__main__":
    # Initialize Dask cluster
    client = setup_dask_cluster()

    # Paths
    nifti_path = "path/to/input.nii.gz"  # Path to the NIfTI file (if applicable)
    zarr_path = "path/to/data.zarr"      # Path to the Zarr file (output or input)
    processed_output_path = "path/to/processed_output.zarr"

    # Determine data source
    if os.path.exists(zarr_path):
        print("Zarr file detected. Loading directly...")
        dask_data = load_zarr_data(zarr_path)
    else:
        print("No Zarr file detected. Converting NIfTI to Zarr...")
        nifti_to_zarr(nifti_path, zarr_path)
        dask_data = load_zarr_data(zarr_path)

    # Processing
    process_3d_data(dask_data, processed_output_path, mask_diameter=256)

    client.close()
