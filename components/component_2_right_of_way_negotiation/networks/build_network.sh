#!/usr/bin/env sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$script_dir"

netconvert \
  --node-files intersection.nod.xml \
  --edge-files intersection.edg.xml \
  --connection-files intersection.con.xml \
  --output-file intersection.net.xml \
  --no-turnarounds true

echo "Generated intersection.net.xml successfully."

