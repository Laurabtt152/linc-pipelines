"""
Script to stack series of (photo, histo) pairs that have been registerd
with TIRL. It takes care of potential 180 flips of the photos.

Environment Parameters
----------------------
LINCSET   : Path to root of LINCBRAIN dataset to process
LINCSUB   : Name of subject to process
XSPACE    : X resolution (mm/voxel)
YSPACE    : Y resolution (mm/voxel)
ZSPACE    : Spacing between photos (mm)

Inputs and Outputs
------------------
Raw inputs are assumed to exist under {LINCSET}/rawdata/sub-{LINCSUB}/micr.

All registration outputs are assumed to exist under
{LINCSET}/derivatives/tirl-histo/sub-{LINCSUB}/sub-{LINCSUB}_sample-{SAMPLE}/.

Stacked outputs are written under {LINCSET}/derivatives/tirl-histo.
- A photo stack sub-{LINCSUB}_photo.nii.gz
- A histo stack sub-{LINCSUB}_histo.nii.gz

Dependencies
------------
- imageio
- tifffile
- nibabel
- numpy
"""
import os
import sys
import imageio
import tifffile
import nibabel
import numpy as np
from glob import glob

HOME = os.environ['HOME']

# Path to LincBrain dataset
LINCSET = os.path.join(HOME, 'localdata/linc/lincbrain/000003')
LINCSET = os.environ.get('LINCSET', LINCSET)
print('LINC DATASET:           ', LINCSET)

# Subject to process
LINCSUB = 'MR256'
LINCSUB = os.environ.get('LINCSUB', LINCSUB)
print('SUBJECT:                ', LINCSUB)

# spacing
XSPACE, YSPACE, ZSPACE = 0.05, 0.05, 0.2
XSPACE = os.environ.get('XSPACE', XSPACE)
YSPACE = os.environ.get('YSPACE', YSPACE)
ZSPACE = os.environ.get('ZSPACE', ZSPACE)

# Folder with preprocessed histo an photo files
RAW_FOLDER = os.path.join(LINCSET, f'rawdata/sub-{LINCSUB}/micr')
print('RAW FOLDER:             ', RAW_FOLDER)

# Folder with registration outputs
TIRL_FOLDER = os.path.join(LINCSET, f'derivatives/tirl-histo/sub-{LINCSUB}')
print('TIRL FOLDER:            ', TIRL_FOLDER)

print('-' * 48)

# Find all photo files
FNAMES_PHOTO = list(sorted(glob(os.path.join(RAW_FOLDER, f'sub-{LINCSUB}_sample-*_photo.tif'))))

photo_stack = []
histo_stack = []
for fname_photo in FNAMES_PHOTO:
    basename_histo = os.path.splitext(os.path.basename(fname_photo))[0]
    basename_sample = basename_histo[:-6]
    print('- Photo:', fname_photo)

    dat_photo = tifffile.TiffFile(fname_photo).asarray()
    dat_photo = np.frombuffer(dat_photo.tobytes(), dtype='u1').reshape(dat_photo.shape)

    flip = False
    if photo_stack:
        overlap = ((photo_stack[-1] != 0) & (dat_photo != 0)).mean()
        flip = ((photo_stack[-1] != 0) & (dat_photo[::-1, ::-1] != 0)).mean() > overlap
    if flip:
        dat_photo = dat_photo[::-1, ::-1]
    photo_stack.append(dat_photo)

    fname_histo = os.path.join(TIRL_FOLDER, basename_sample, 'moving4_nonlinear.png')
    print('- Histo:', fname_histo)

    if not os.path.exists(fname_histo):
        print('! HISTO NOT FOUND')
        histo_stack.append(np.zeros_like(photo_stack[-1]))
        continue

    dat_histo = imageio.imread(fname_histo).astype('u1')
    dat_histo[dat_histo == 255] = 0
    if flip:
        dat_histo = dat_histo[::-1, ::-1]
    histo_stack.append(dat_histo)

orient = np.asarray([
    [ 0, -1,  0,  0],
    [ 0,  0, -1,  0],
    [+1,  0,  0,  0],
    [ 0,  0,  0, +1],
], dtype='double')

photo_stack = np.stack(photo_stack, -1)
photo_nii = nibabel.Nifti1Image(photo_stack, orient)
photo_nii.header.set_zooms([XSPACE, YSPACE, ZSPACE])
nibabel.save(photo_nii, os.path.join(TIRL_FOLDER, f'sub-{LINCSUB}_photo.nii.gz'))

histo_stack = np.stack(histo_stack, -1)
histo_nii = nibabel.Nifti1Image(histo_stack, orient)
histo_nii.header.set_zooms([XSPACE, YSPACE, ZSPACE])
nibabel.save(histo_nii, os.path.join(TIRL_FOLDER, f'sub-{LINCSUB}_histo.nii.gz'))
