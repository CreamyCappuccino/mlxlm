# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Clear command handler for mlxlm run."""

import os
from .run_utils import _colored


def handle_clear_command(history: list[tuple[str, str]]) -> None:
    """
    Handle /clear command with multiple options.

    Args:
        history: Conversation history list to potentially clear
    """
    print("""
Clear options:
1. Clear conversation only (keep screen)
2. Clear screen only (keep conversation history)
3. Clear both
4. Cancel

Select (1-4) [4]: """, end='')

    try:
        choice = input().strip()
    except (KeyboardInterrupt, EOFError):
        print()
        choice = '4'

    if choice == '1':
        history.clear()
        print(_colored("✅ Conversation history cleared (screen unchanged)", "success"))
    elif choice == '2':
        os.system('clear' if os.name != 'nt' else 'cls')
        print(_colored("✅ Screen cleared (conversation history preserved)", "success"))
    elif choice == '3':
        history.clear()
        os.system('clear' if os.name != 'nt' else 'cls')
        print("=" * 60)
        print(_colored("🧹 Everything cleared! Starting fresh...", "success"))
        print("=" * 60)
    else:
        print(_colored("❌ Cancelled", "warning"))
