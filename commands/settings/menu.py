# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Settings menu for mlxlm."""

from commands.run_utils import _colored
from .defaults import edit_defaults
from .colors import edit_colors
from .history import edit_history
from .export_settings import edit_export


def show_settings_menu(config: dict) -> dict:
    """
    Display interactive settings menu and return updated config.

    Args:
        config: Current configuration dictionary

    Returns:
        dict: Updated configuration dictionary
    """
    while True:
        print("""
⚙️  Settings Menu:

1. 💬 Default Behavior Settings
2. 🎨 Color Settings
3. 📚 User Prompt History
4. 💾 Export Settings
0. 🔙 Back

Select (0-4): """, end='')

        try:
            choice = input().strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if choice == '1':
            config = edit_defaults(config)
        elif choice == '2':
            config = edit_colors(config)
        elif choice == '3':
            config = edit_history(config)
        elif choice == '4':
            config = edit_export(config)
        elif choice == '0':
            break
        else:
            print(_colored("⚠️  Invalid choice. Please select 0-4.", "warning"))

    return config
