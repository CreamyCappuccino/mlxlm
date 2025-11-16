# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Utility functions for mlxlm run command."""

# ANSI color codes for terminal output (global state)
COLORS = {
    'user_prompt': '\033[1;37m',      # Bold white
    'model_output': '\033[97m',       # Bright white
    'error': '\033[91m',              # Bright red
    'success': '\033[92m',            # Bright green
    'warning': '\033[93m',            # Bright yellow
    'system': '\033[90m',             # Bright gray (for system messages)
    'reset': '\033[0m',               # Reset
}


def _colored(text: str, color_key: str) -> str:
    """Apply ANSI color to text."""
    return f"{COLORS.get(color_key, '')}{text}{COLORS['reset']}"


def ansi_to_prompt_toolkit_style(ansi_code: str) -> str:
    """
    Convert ANSI color code to prompt-toolkit style string.

    Args:
        ansi_code: ANSI escape code (e.g., '\033[1;37m')

    Returns:
        prompt-toolkit style string (e.g., 'bold ansiwhite')
    """
    import re

    # Handle RGB format: \033[38;2;R;G;Bm
    rgb_match = re.search(r'\033\[38;2;(\d+);(\d+);(\d+)m', ansi_code)
    if rgb_match:
        r, g, b = rgb_match.groups()
        return f'#{int(r):02x}{int(g):02x}{int(b):02x}'

    # Map basic ANSI codes to prompt-toolkit style names
    ansi_map = {
        '\033[30m': 'ansiblack',
        '\033[31m': 'ansired',
        '\033[32m': 'ansigreen',
        '\033[33m': 'ansiyellow',
        '\033[34m': 'ansiblue',
        '\033[35m': 'ansimagenta',
        '\033[36m': 'ansicyan',
        '\033[37m': 'ansiwhite',
        '\033[90m': 'ansibrightblack',
        '\033[91m': 'ansibrightred',
        '\033[92m': 'ansibrightgreen',
        '\033[93m': 'ansibrightyellow',
        '\033[94m': 'ansibrightblue',
        '\033[95m': 'ansibrightmagenta',
        '\033[96m': 'ansibrightcyan',
        '\033[97m': 'ansibrightwhite',
        '\033[1;37m': 'bold ansiwhite',
    }

    return ansi_map.get(ansi_code, 'ansiwhite')
