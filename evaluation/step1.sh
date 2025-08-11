#!/bin/bash

# keep unchanged
export META_CSV_PATH=folder/of/metadata_evaluation_set.csv
export BASE_DIR_REF=folder/of/reference_dir

# to be modified
export BASE_DIR_PRED=folder/of/inference/results
export PARTIAL_RESULTS_DIR=${BASE_DIR_PRED}_split

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

pip install posebusters; 
cd "$SCRIPT_DIR";

# Step1
python parallel_run.py
