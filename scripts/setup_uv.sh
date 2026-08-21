#!/bin/bash
set -euxo pipefail

# Download and install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install environment
uv sync --locked
# "$HOME/.local/bin/uv" sync --locked  # Uses explicit path.

echo "uv has been successfully set up."