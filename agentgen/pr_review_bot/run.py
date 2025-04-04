#!/usr/bin/env python3
"""
Simple wrapper script to run the PR Review Bot without package installation.
This script adds the current directory to the Python path so that local imports work.
"""

import os
import sys
import argparse

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Now we can import from the launch module directly
from launch import main

if __name__ == "__main__":
    # Run the main function directly - the arguments will be parsed in launch.py
    main()