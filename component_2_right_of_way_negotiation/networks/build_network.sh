#!/usr/bin/env sh
# Stop on failed commands and on attempts to use unset shell variables.
set -eu

# Resolve the script directory in a subshell without allowing CDPATH to add output.
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
# Run the network converter beside its input XML files.
cd "$script_dir"

# Generate intersection.net.xml from the node, edge, and explicit connection XML files below.
# Disable automatic turnarounds; keep the backslash-continued option lines adjacent to this command.
netconvert \
  --node-files intersection.nod.xml \
  --edge-files intersection.edg.xml \
  --connection-files intersection.con.xml \
  --output-file intersection.net.xml \
  --no-turnarounds true

# Report the generated network filename after the converter succeeds.
echo "Generated intersection.net.xml successfully."

