# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Color settings management for mlxlm."""

from commands.run_utils import _colored, COLORS

# Preset color themes
COLOR_THEMES = {
    'default': {
        'user_prompt': '\033[1;37m',
        'model_output': '\033[97m',
        'error': '\033[91m',
        'success': '\033[92m',
        'warning': '\033[93m',
        'system': '\033[90m',
        'reset': '\033[0m',
    },
    'nord': {
        'user_prompt': '\033[96m',     # Cyan
        'model_output': '\033[97m',    # White
        'error': '\033[91m',           # Bright red
        'success': '\033[92m',         # Bright green
        'warning': '\033[93m',         # Bright yellow
        'system': '\033[90m',          # Gray
        'reset': '\033[0m',
    },
    'dracula': {
        'user_prompt': '\033[95m',     # Magenta
        'model_output': '\033[97m',    # White
        'error': '\033[91m',           # Bright red
        'success': '\033[92m',         # Bright green
        'warning': '\033[93m',         # Bright yellow
        'system': '\033[90m',          # Gray
        'reset': '\033[0m',
    },
    'monokai': {
        'user_prompt': '\033[93m',     # Bright yellow
        'model_output': '\033[97m',    # White
        'error': '\033[91m',           # Bright red
        'success': '\033[92m',         # Bright green
        'warning': '\033[93m',         # Bright yellow
        'system': '\033[90m',          # Gray
        'reset': '\033[0m',
    },
    'solarized': {
        'user_prompt': '\033[96m',     # Cyan
        'model_output': '\033[37m',    # White
        'error': '\033[31m',           # Red
        'success': '\033[32m',         # Green
        'warning': '\033[33m',         # Yellow
        'system': '\033[90m',          # Gray
        'reset': '\033[0m',
    },
}


def parse_color_input(user_input: str) -> str | None:
    """
    Convert user input to ANSI color code.

    Supports:
    - 16-color codes: 30-37, 90-97
    - RGB hex: #RRGGBB
    - RGB comma-separated: R,G,B

    Args:
        user_input: User's color input

    Returns:
        ANSI color code string, or None if invalid
    """
    user_input = user_input.strip()

    # Number only (16 colors)
    if user_input.isdigit():
        code = int(user_input)
        if 30 <= code <= 37 or 90 <= code <= 97:
            return f"\033[{code}m"

    # #RRGGBB format
    if user_input.startswith('#') and len(user_input) == 7:
        try:
            r = int(user_input[1:3], 16)
            g = int(user_input[3:5], 16)
            b = int(user_input[5:7], 16)
            return f"\033[38;2;{r};{g};{b}m"
        except ValueError:
            pass

    # R,G,B format
    if ',' in user_input:
        try:
            parts = user_input.split(',')
            if len(parts) == 3:
                r, g, b = map(int, parts)
                if all(0 <= c <= 255 for c in [r, g, b]):
                    return f"\033[38;2;{r};{g};{b}m"
        except ValueError:
            pass

    return None


def edit_colors(config: dict) -> dict:
    """Edit color settings with preset themes and custom editing."""
    while True:
        current_theme = config.get('colors', {}).get('theme', 'default')
        print(f"""
🎨 Color Settings (Current: {current_theme}):

1. Default
2. Nord
3. Dracula
4. Monokai
5. Solarized
6. Custom (create your own)
0. 🔙 Back

Select (0-6): """, end='')

        try:
            choice = input().strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if choice in ['1', '2', '3', '4', '5']:
            theme_map = {'1': 'default', '2': 'nord', '3': 'dracula', '4': 'monokai', '5': 'solarized'}
            selected_theme = theme_map[choice]
            config['colors'] = {
                'theme': selected_theme,
                **COLOR_THEMES[selected_theme]
            }
            # Update global COLORS
            COLORS.update(COLOR_THEMES[selected_theme])
            print(_colored(f"✅ Theme changed to {selected_theme}", "success"))

        elif choice == '6':
            # Custom theme editing
            config = edit_custom_colors(config)

        elif choice == '0':
            break
        else:
            print(_colored("⚠️  Invalid choice. Please select 0-6.", "warning"))

    return config


def edit_custom_colors(config: dict) -> dict:
    """Edit custom color theme."""
    # Start with current colors or default
    current_theme = config.get('colors', {}).get('theme', 'default')
    if current_theme == 'custom' and 'custom_colors' in config.get('colors', {}):
        custom = config['colors']['custom_colors'].copy()
    else:
        # Start from current theme or default
        base_theme = current_theme if current_theme != 'custom' else 'default'
        custom = COLOR_THEMES[base_theme].copy()

    color_names = {
        '1': ('user_prompt', 'User Prompt'),
        '2': ('model_output', 'Model Output'),
        '3': ('error', 'Error'),
        '4': ('success', 'Success'),
        '5': ('warning', 'Warning'),
        '6': ('system', 'System'),
    }

    def get_color_description(ansi_code: str) -> str:
        """Convert ANSI code to human-readable description."""
        color_map = {
            '\033[30m': 'black', '\033[31m': 'red', '\033[32m': 'green',
            '\033[33m': 'yellow', '\033[34m': 'blue', '\033[35m': 'magenta',
            '\033[36m': 'cyan', '\033[37m': 'white',
            '\033[90m': 'gray', '\033[91m': 'bright red', '\033[92m': 'bright green',
            '\033[93m': 'bright yellow', '\033[94m': 'bright blue', '\033[95m': 'bright magenta',
            '\033[96m': 'bright cyan', '\033[97m': 'bright white', '\033[1;37m': 'bold white',
        }
        return color_map.get(ansi_code, 'custom')

    while True:
        print(f"""
🎨 Customize Colors (based on: {current_theme}):
""")
        for key, (color_key, display_name) in color_names.items():
            ansi_code = custom.get(color_key, '')
            desc = get_color_description(ansi_code)
            # Display with color preview
            print(f"{key}. {display_name}: {ansi_code}{desc}\033[0m")

        print("""
7. ✅ Save as Custom theme
0. 🔙 Cancel

Select (0-7): """, end='')

        try:
            choice = input().strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if choice in color_names:
            color_key, display_name = color_names[choice]
            current_code = custom.get(color_key, '')
            current_desc = get_color_description(current_code)

            print(f"\nCurrent: {current_code}{current_desc}\033[0m")
            print("""
📚 Basic 16 Colors Reference:
  30: \033[30mBlack\033[0m           90: \033[90mBright Black (Gray)\033[0m
  31: \033[31mRed\033[0m             91: \033[91mBright Red\033[0m
  32: \033[32mGreen\033[0m           92: \033[92mBright Green\033[0m
  33: \033[33mYellow\033[0m          93: \033[93mBright Yellow\033[0m
  34: \033[34mBlue\033[0m            94: \033[94mBright Blue\033[0m
  35: \033[35mMagenta\033[0m         95: \033[95mBright Magenta\033[0m
  36: \033[36mCyan\033[0m            96: \033[96mBright Cyan\033[0m
  37: \033[37mWhite\033[0m           97: \033[97mBright White\033[0m
""")
            print("Enter color (30-37 or 90-97 for basic colors, #RRGGBB for RGB, or R,G,B): ", end='')

            try:
                user_input = input().strip()
            except (KeyboardInterrupt, EOFError):
                print()
                continue

            new_code = parse_color_input(user_input)
            if new_code:
                custom[color_key] = new_code
                print(f"\n✅ Preview: {new_code}{display_name}\033[0m")
                print("Apply this color? (yes/no): ", end='')
                try:
                    confirm = input().strip().lower()
                    if confirm not in ['yes', 'y']:
                        # Revert
                        custom[color_key] = current_code
                        print(_colored("❌ Change cancelled", "warning"))
                except (KeyboardInterrupt, EOFError):
                    print()
                    custom[color_key] = current_code
            else:
                print(_colored("⚠️  Invalid color format. Try again.", "warning"))

        elif choice == '7':
            # Save custom theme
            config['colors'] = {
                'theme': 'custom',
                'custom_colors': custom,
                **custom
            }
            # Update global COLORS
            COLORS.update(custom)
            print(_colored("✅ Custom theme saved!", "success"))
            break

        elif choice == '0':
            print(_colored("❌ Custom editing cancelled", "warning"))
            break

        else:
            print(_colored("⚠️  Invalid choice. Please select 0-7.", "warning"))

    return config
