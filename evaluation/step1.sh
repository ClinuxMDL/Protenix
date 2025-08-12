#!/bin/bash

# keep unchanged
export META_CSV_PATH=/voyager-hackathon/dataland/af3-dev/release_data/Reference_Test1/testset1_meta.csv
export BASE_DIR_REF=/voyager-hackathon/dataland/af3-dev/release_data/Reference_Test1/MD

# to be modified
export BASE_DIR_PRED=$1
export PARTIAL_RESULTS_DIR=${BASE_DIR_PRED}_metrics_split

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

pip install posebusters; 
cd "$SCRIPT_DIR";

# Step1
python parallel_run.py
