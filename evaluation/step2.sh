#!/bin/bash

export PARTIAL_RESULTS_DIR=$1

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR";

# Step2
python merge_results.py