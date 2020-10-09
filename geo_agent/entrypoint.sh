#!/bin/bash --login


set -e



# conda activate $ENV_PREFIX
conda activate geopy_copy

exec "$@"