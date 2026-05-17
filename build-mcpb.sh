#!/usr/bin/env bash
# Build the xraydb-mcp-server.mcpb bundle for Claude Desktop one-click install.
# An .mcpb file is just a zip containing manifest.json plus the server source.
set -euo pipefail

cd "$(dirname "$0")"

OUT="xraydb-mcp-server.mcpb"
rm -f "$OUT"

zip -r "$OUT" \
  manifest.json \
  src/server.py \
  -x "src/__pycache__/*" "src/*.egg-info/*"

echo "Built $OUT"
unzip -l "$OUT"
