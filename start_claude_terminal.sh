#!/bin/bash
# Quick start script for the Claude terminal interface

# Make terminal_interface.py executable
chmod +x terminal_interface.py

# Check if API key is provided as environment variable
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "Warning: ANTHROPIC_API_KEY environment variable not set."
    echo "You can either set it before running this script or provide it as an argument."
    echo "Usage: ./start_claude_terminal.sh [API_KEY]"
    
    # If provided as argument, use it
    if [ $# -ge 1 ]; then
        ANTHROPIC_API_KEY=$1
    else
        echo "Error: No API key provided. Exiting."
        exit 1
    fi
fi

# Run the terminal interface
python terminal_interface.py --api-key $ANTHROPIC_API_KEY