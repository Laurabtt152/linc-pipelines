"""
Script to run TIRL registration on a series of (photo, histo) pairs.

Environment Parameters
----------------------
LINCSET   : Path to root of LINCBRAIN dataset to process
LINCSUB   : Name of subject to process
TIRLPARAM : Path to a TIRL parameter file, to use as template

Inputs and Outputs
------------------
All inputs are assumed to exist under {LINCSET}/rawdata/sub-{LINCSUB}/micr.

All outputs are written under {LINCSET}/derivatives/tirl-histo/sub-{LINCSUB}.
Each BIDS sample/slice gets its own subdirectory sub-{LINCSUB}_sample-{SAMPLE},
containing all outputs from the TIRL pipeline.

Dependencies
------------
- [private] https://github.com/inhuszar/tirl
- [private] https://github.com/inhuszar/tirlscripts-oxford-scriptutils
- [private] https://github.com/inhuszar/tirlscripts-mgh-linc
"""
import os
import sys
import yaml
import subprocess
from glob import glob

HOME = os.environ['HOME']

# Path to TIRL template parameter file
TIRLPARAM = os.path.join(os.path.dirname(__file__), 'tirl_histo2block.yml')
TIRLPARAM = os.environ.get('TIRLPARAM', TIRLPARAM)
print('TIRL PARAMETER FILE:    ', TIRLPARAM)

# Path to LincBrain dataset
LINCSET = os.path.join(HOME, 'localdata/linc/lincbrain/000003')
LINCSET = os.environ.get('LINCSET', LINCSET)
print('LINC DATASET:           ', LINCSET)

# Subject to process
LINCSUB = 'MR256'
LINCSUB = os.environ.get('LINCSUB', LINCSUB)
print('SUBJECT:                ', LINCSUB)

# Folder with preprocessed histo an photo files
INP_FOLDER = os.path.join(LINCSET, f'rawdata/sub-{LINCSUB}/micr')
print('INPUT FOLDER:           ', INP_FOLDER)

# Folder with registration outputs
OUT_FOLDER = os.path.join(LINCSET, f'derivatives/tirl-histo/sub-{LINCSUB}')
print('OUTPUT FOLDER:          ', OUT_FOLDER)

print('-' * 48)

# Find all histo files
FNAMES_HISTO = list(sorted(glob(os.path.join(INP_FOLDER, f'sub-{LINCSUB}_sample-*_stain-LY_DF.tif'))))

for fname_histo in FNAMES_HISTO:
    basename_histo = os.path.splitext(os.path.basename(fname_histo))[0]
    basename_sample = basename_histo[:-12]
    basename_photo = basename_sample + '_photo'
    fname_photo = os.path.join(INP_FOLDER, basename_photo + '.tif')
    print('- Histo:', fname_histo)
    print('- Photo:', fname_photo)
    if not os.path.exists(fname_photo):
        print('! PHOTO NOT FOUND')
        continue

    out_folder_sample = os.path.join(OUT_FOLDER, basename_sample)

    os.makedirs(out_folder_sample, exist_ok=True)
    with open(TIRLPARAM, 'r') as f:
        param = yaml.full_load(f)

    param['histology']['file'] = fname_histo
    param['block']['file'] = fname_photo
    param['general']['outputdir'] = out_folder_sample
    param['general']['logfile'] = os.path.join(out_folder_sample, 'logfile.log')
    param['general']['paramlogfile'] = os.path.join(out_folder_sample, 'paramlogfile.log')
    if sys.platform == 'darwin':
        param['general']['system'] = 'macosx'
    elif sys.platform == 'linux':
        param['general']['system'] = 'linux'
    else:
        raise RuntimeError('System not supported. Must be Linux or MacOS.')

    fname_param = os.path.join(out_folder_sample, 'tirlparam.yml')
    with open(fname_param, 'w') as f:
        yaml.dump(param, f)

    subprocess.run([
        'tirl', 'linc.h2b', '--config', fname_param, '--verbose',
    ])
