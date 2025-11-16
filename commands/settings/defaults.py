# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Default behavior settings management for mlxlm."""

from commands.run_utils import _colored


def edit_defaults(config: dict) -> dict:
    """Edit default behavior settings."""
    while True:
        defaults = config['defaults']
        show_stats = defaults.get('show_context_stats', False)
        print(f"""
💬 Default Behavior Settings:

1. Max Tokens: {defaults['max_tokens']}
2. Stream Mode: {defaults['stream_mode']}
3. Chat Mode: {defaults['chat_mode']}
4. History Mode: {defaults['history']}
5. Time Limit: {defaults['time_limit']} sec
6. Reasoning Level: {defaults['reasoning'] or 'None'}
7. Show Context Stats: {'On' if show_stats else 'Off'}
0. 🔙 Back

Select (0-7): """, end='')

        try:
            choice = input().strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if choice == '1':
            print("Enter max tokens (512/1024/2048/4096): ", end='')
            try:
                value = int(input().strip())
                if value > 0:
                    config['defaults']['max_tokens'] = value
                    print(_colored(f"✅ Max tokens set to {value}", "success"))
                else:
                    print(_colored("⚠️  Value must be positive", "warning"))
            except ValueError:
                print(_colored("⚠️  Invalid number", "warning"))

        elif choice == '2':
            print("Stream mode (all/final/off): ", end='')
            value = input().strip().lower()
            if value in ['all', 'final', 'off']:
                config['defaults']['stream_mode'] = value
                print(_colored(f"✅ Stream mode set to {value}", "success"))
            else:
                print(_colored("⚠️  Invalid mode. Use all/final/off", "warning"))

        elif choice == '3':
            print("Chat mode (auto/harmony/hf/plain): ", end='')
            value = input().strip().lower()
            if value in ['auto', 'harmony', 'hf', 'plain']:
                config['defaults']['chat_mode'] = value
                print(_colored(f"✅ Chat mode set to {value}", "success"))
            else:
                print(_colored("⚠️  Invalid mode. Use auto/harmony/hf/plain", "warning"))

        elif choice == '4':
            print("History mode (on/off): ", end='')
            value = input().strip().lower()
            if value in ['on', 'off']:
                config['defaults']['history'] = value
                print(_colored(f"✅ History mode set to {value}", "success"))
            else:
                print(_colored("⚠️  Invalid mode. Use on/off", "warning"))

        elif choice == '5':
            print("Time limit in seconds (0 for unlimited): ", end='')
            try:
                value = int(input().strip())
                if value >= 0:
                    config['defaults']['time_limit'] = value
                    print(_colored(f"✅ Time limit set to {value} sec", "success"))
                else:
                    print(_colored("⚠️  Value must be non-negative", "warning"))
            except ValueError:
                print(_colored("⚠️  Invalid number", "warning"))

        elif choice == '6':
            print("Reasoning level (low/medium/high/none): ", end='')
            value = input().strip().lower()
            if value == 'none':
                config['defaults']['reasoning'] = None
                print(_colored("✅ Reasoning level cleared", "success"))
            elif value in ['low', 'medium', 'high']:
                config['defaults']['reasoning'] = value
                print(_colored(f"✅ Reasoning level set to {value}", "success"))
            else:
                print(_colored("⚠️  Invalid level. Use low/medium/high/none", "warning"))

        elif choice == '7':
            print("Show context stats (on/off): ", end='')
            value = input().strip().lower()
            if value in ['on', 'off']:
                config['defaults']['show_context_stats'] = (value == 'on')
                print(_colored(f"✅ Show context stats set to {value}", "success"))
            else:
                print(_colored("⚠️  Invalid value. Use on/off", "warning"))

        elif choice == '0':
            break
        else:
            print(_colored("⚠️  Invalid choice. Please select 0-7.", "warning"))

    return config
