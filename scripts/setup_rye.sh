#!/bin/bash
set -eux

# Download and install rye
curl -sSf https://rye.astral.sh/get | RYE_INSTALL_OPTION="--yes" bash

# Source rye for bash
echo 'source "$HOME/.rye/env"' >> ~/.bashrc

# Setup completions for bash
mkdir -p ~/.local/share/bash-completion/completions
~/.rye/shims/rye self completion > ~/.local/share/bash-completion/completions/rye.bash

# Install dependencies
~/.rye/shims/rye sync --no-lock

echo "Rye has been successfully installed and configured."
