# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Export settings management for mlxlm."""

from commands.run_utils import _colored


def edit_export(config: dict) -> dict:
    """Edit export settings."""
    while True:
        exp = config['export']
        print(f"""
💾 Export Settings:

1. Default Format: {exp['default_format']}
2. Include Timestamp: {exp['include_timestamp']}
3. Auto Save on Exit: {exp['auto_save']}
0. 🔙 Back

Select (0-3): """, end='')

        try:
            choice = input().strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if choice == '1':
            print("Default format (md/txt/json): ", end='')
            value = input().strip().lower()
            if value in ['md', 'txt', 'json']:
                config['export']['default_format'] = value
                print(_colored(f"✅ Default format set to {value}", "success"))
            else:
                print(_colored("⚠️  Invalid format. Use md/txt/json", "warning"))

        elif choice == '2':
            print("Include timestamp in filename? (yes/no): ", end='')
            value = input().strip().lower()
            if value in ['yes', 'y']:
                config['export']['include_timestamp'] = True
                print(_colored("✅ Timestamp enabled", "success"))
            elif value in ['no', 'n']:
                config['export']['include_timestamp'] = False
                print(_colored("✅ Timestamp disabled", "success"))
            else:
                print(_colored("⚠️  Invalid value. Use yes/no", "warning"))

        elif choice == '3':
            print("Auto save on exit? (yes/no): ", end='')
            value = input().strip().lower()
            if value in ['yes', 'y']:
                config['export']['auto_save'] = True
                print(_colored("✅ Auto save enabled", "success"))
            elif value in ['no', 'n']:
                config['export']['auto_save'] = False
                print(_colored("✅ Auto save disabled", "success"))
            else:
                print(_colored("⚠️  Invalid value. Use yes/no", "warning"))

        elif choice == '0':
            break
        else:
            print(_colored("⚠️  Invalid choice. Please select 0-3.", "warning"))

    return config
