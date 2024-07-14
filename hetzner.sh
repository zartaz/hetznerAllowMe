#!/bin/bash


PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source the virtual environment
source "$PROJECT_DIR/env/bin/activate"

# Run the Python script
python "$PROJECT_DIR/fire.py"

# Deactivate the virtual environment (optional, but good practice)
deactivate

# add to .ssh/config
ssh hetzner