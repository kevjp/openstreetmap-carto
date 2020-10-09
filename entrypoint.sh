#!/bin/bash --login

set -e

source $CONDA_DIR/etc/profile.d/conda.sh


conda activate geopy_copy
python setup.py build_ext --inplace
# echo $CONDA_PREFIX

# /env/bin/pip install --requirement /tmp/requirements.txt

# python setup.py build_ext --inplace

exec "$@"