#!/bin/bash
cd /Users/dguenzing/software/xraydb-mcp-server/
exec uv run python src/server.py "$@"