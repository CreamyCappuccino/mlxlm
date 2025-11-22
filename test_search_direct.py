#!/usr/bin/env python3
"""Direct test of search functionality."""

import sys
import os

# Execute the search.py file directly
search_file = os.path.join(os.path.dirname(__file__), 'commands', 'search.py')

# Read and execute
with open(search_file) as f:
    code = f.read()
    exec(code, {'__name__': '__main__'})

# Now call search_main
if len(sys.argv) < 2:
    print("Usage: python test_search_direct.py <query>")
    sys.exit(1)

search_main(sys.argv[1])
