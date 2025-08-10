#!/bin/bash
set -e

SRC_BASE="/voyager-hackathon/dataland/af3-dev/release_data"
DEST_BASE="$(pwd)/release_data"

mkdir -p "$DEST_BASE"

cp -r "$SRC_BASE/ccd_cache" "$DEST_BASE/ccd_cache"
cp -r "$SRC_BASE/checkpoint" "$DEST_BASE/checkpoint"

echo "Finish clone data to $DEST_BASE"