# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""User prompt history settings management for mlxlm."""

from commands.run_utils import _colored


def edit_history(config: dict) -> dict:
    """Edit user prompt history settings."""
    while True:
        hist = config['history']
        print(f"""
📚 User Prompt History Settings:

1. Max Entries: {hist['max_entries']}
2. Max Age (days): {hist['max_age_days'] or 'Unlimited'}
0. 🔙 Back

Select (0-2): """, end='')

        try:
            choice = input().strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if choice == '1':
            print("Max entries (10/25/50/100/200/0 for unlimited): ", end='')
            try:
                value = int(input().strip())
                if value >= 0:
                    config['history']['max_entries'] = value if value > 0 else 999999
                    print(_colored(f"✅ Max entries set to {value if value > 0 else 'unlimited'}", "success"))
                else:
                    print(_colored("⚠️  Value must be non-negative", "warning"))
            except ValueError:
                print(_colored("⚠️  Invalid number", "warning"))

        elif choice == '2':
            print("Max age in days (0 for unlimited): ", end='')
            try:
                value = int(input().strip())
                if value >= 0:
                    config['history']['max_age_days'] = None if value == 0 else value
                    print(_colored(f"✅ Max age set to {value if value > 0 else 'unlimited'} days", "success"))
                else:
                    print(_colored("⚠️  Value must be non-negative", "warning"))
            except ValueError:
                print(_colored("⚠️  Invalid number", "warning"))

        elif choice == '0':
            break
        else:
            print(_colored("⚠️  Invalid choice. Please select 0-2.", "warning"))

    return config
