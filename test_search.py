#!/usr/bin/env python3
"""Test script for search command (without importing full CLI)."""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import search module directly
from commands.search import search_main

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_search.py <query> [options]")
        sys.exit(1)

    query = sys.argv[1]
    search_main(query)
