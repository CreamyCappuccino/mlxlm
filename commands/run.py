# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Run model in interactive chat mode command."""

from __future__ import annotations

import os
import time

from mlx_lm import load, generate, stream_generate

# prompt-toolkit imports
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import InMemoryHistory, FileHistory
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.formatted_text import ANSI
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.auto_suggest import AutoSuggest, Suggestion
    from prompt_toolkit.document import Document
    from prompt_toolkit.buffer import Buffer
    from pathlib import Path
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False

from core import (
    load_alias_dict,
    resolve_to_cache_key,
    load_config_for_model,
    _apply_reasoning_to_system,
    _render_prompt,
    _human_bytes,
    _count_tokens,
    _estimate_kv_bytes,
    _stream_final_from_harmony,
    load_user_config,
    save_user_config,
)

# ANSI color codes for terminal output
COLORS = {
    'user_prompt': '\033[1;37m',      # Bold white
    'model_output': '\033[97m',       # Bright white
    'error': '\033[91m',              # Bright red
    'success': '\033[92m',            # Bright green
    'warning': '\033[93m',            # Bright yellow
    'system': '\033[90m',             # Bright gray (for system messages)
    'reset': '\033[0m',               # Reset
}

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

def _colored(text: str, color_key: str) -> str:
    """Apply ANSI color to text."""
    return f"{COLORS.get(color_key, '')}{text}{COLORS['reset']}"


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


def export_conversation(history: list[tuple[str, str]], filename: str, format: str = 'md', model_name: str = '') -> bool:
    """
    Export conversation history to a file.

    Args:
        history: List of (role, message) tuples
        filename: Output filename
        format: Export format ('md', 'txt', or 'json')
        model_name: Model name for metadata

    Returns:
        bool: True if successful, False otherwise
    """
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        if format == 'md':
            content = f"# MLX-LM Chat Export\n"
            content += f"**Model**: {model_name}\n"
            content += f"**Date**: {timestamp}\n"
            content += f"**Total Turns**: {len(history)}\n\n"
            content += "---\n\n"

            for role, message in history:
                if role == 'user':
                    content += f"### User:\n{message}\n\n"
                else:
                    content += f"### AI:\n{message}\n\n"
                content += "---\n\n"

        elif format == 'txt':
            content = f"MLX-LM Chat Export\n"
            content += f"Model: {model_name}\n"
            content += f"Date: {timestamp}\n"
            content += f"Total Turns: {len(history)}\n\n"
            content += "=" * 80 + "\n\n"

            for role, message in history:
                if role == 'user':
                    content += f"[User]\n{message}\n\n"
                else:
                    content += f"[AI]\n{message}\n\n"
                content += "=" * 80 + "\n\n"

        elif format == 'json':
            import json
            data = {
                "model": model_name,
                "export_date": timestamp,
                "total_turns": len(history),
                "conversation": [
                    {"role": role, "content": message}
                    for role, message in history
                ]
            }
            content = json.dumps(data, indent=2, ensure_ascii=False)

        else:
            print(_colored(f"⚠️  Unknown format: {format}. Use 'md', 'txt', or 'json'.", "error"))
            return False

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)

        print(_colored(f"✅ Exported to {filename}", "success"))
        return True

    except (PermissionError, OSError) as e:
        print(_colored(f"⚠️  Error: Could not export to {filename} ({e})", "error"))
        return False


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
3. 📚 History Settings
4. 💾 Export Settings
5. 🔙 Back

Select (1-5): """, end='')

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
        elif choice == '5':
            break
        else:
            print(_colored("⚠️  Invalid choice. Please select 1-5.", "warning"))

    return config


def edit_defaults(config: dict) -> dict:
    """Edit default behavior settings."""
    while True:
        defaults = config['defaults']
        print(f"""
💬 Default Behavior Settings:

1. Max Tokens: {defaults['max_tokens']}
2. Stream Mode: {defaults['stream_mode']}
3. Chat Mode: {defaults['chat_mode']}
4. History Mode: {defaults['history']}
5. Time Limit: {defaults['time_limit']} sec
6. Reasoning Level: {defaults['reasoning'] or 'None'}
7. 🔙 Back

Select (1-7): """, end='')

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
            break
        else:
            print(_colored("⚠️  Invalid choice. Please select 1-7.", "warning"))

    return config


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
7. 🔙 Back

Select (1-7): """, end='')

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
            global COLORS
            COLORS.update(COLOR_THEMES[selected_theme])
            print(_colored(f"✅ Theme changed to {selected_theme}", "success"))

        elif choice == '6':
            # Custom theme editing
            config = edit_custom_colors(config)

        elif choice == '7':
            break
        else:
            print(_colored("⚠️  Invalid choice. Please select 1-7.", "warning"))

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
8. 🔙 Cancel

Select (1-8): """, end='')

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
            global COLORS
            COLORS.update(custom)
            print(_colored("✅ Custom theme saved!", "success"))
            break

        elif choice == '8':
            print(_colored("❌ Custom editing cancelled", "warning"))
            break

        else:
            print(_colored("⚠️  Invalid choice. Please select 1-8.", "warning"))

    return config


def edit_history(config: dict) -> dict:
    """Edit history settings."""
    while True:
        hist = config['history']
        print(f"""
📚 History Settings:

1. Max Entries: {hist['max_entries']}
2. Max Age (days): {hist['max_age_days'] or 'Unlimited'}
3. 🔙 Back

Select (1-3): """, end='')

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

        elif choice == '3':
            break
        else:
            print(_colored("⚠️  Invalid choice. Please select 1-3.", "warning"))

    return config


def edit_export(config: dict) -> dict:
    """Edit export settings."""
    while True:
        exp = config['export']
        print(f"""
💾 Export Settings:

1. Default Format: {exp['default_format']}
2. Include Timestamp: {exp['include_timestamp']}
3. Auto Save on Exit: {exp['auto_save']}
4. 🔙 Back

Select (1-4): """, end='')

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

        elif choice == '4':
            break
        else:
            print(_colored("⚠️  Invalid choice. Please select 1-4.", "warning"))

    return config


def run_model(
    model_name: str,
    chat_mode: str = "auto",
    system_prompt: str = "You are a helpful assistant. Answer concisely and helpfully.",
    reasoning: str | None = None,
    max_tokens: int = 2048,
    stream_mode: str = "all",
    stop: list[str] | None = None,
    time_limit: int = 0,
    history_mode: str = "on",
) -> None:
    """
    Run a model in interactive chat mode.

    Args:
        model_name: Model name, alias, or cache key
        chat_mode: Chat rendering mode ('auto', 'harmony', 'hf', 'plain')
        system_prompt: System prompt text
        reasoning: Reasoning verbosity hint ('low', 'medium', 'high')
        max_tokens: Maximum tokens to generate per turn
        stream_mode: Streaming output mode ('all', 'final', 'off')
        stop: List of stop sequences
        time_limit: Hard time limit per turn in seconds (0=off)
        history_mode: Conversation history mode ('on'=full context, 'off'=Q&A only)
    """
    print(f"🚀 Loading model {model_name}...")
    try:
        model, tokenizer = load(model_name)
    except Exception as e:
        print(f"❌ Failed to load model: {e}"); return
    print("✅ Model loaded. Enter your prompts! Type '/help' for commands or '/exit' to quit.\n")

    history: list[tuple[str,str]] = []
    sys_prompt = _apply_reasoning_to_system(system_prompt, reasoning)
    remember_assistant = (history_mode == "on") or (os.getenv("MLXLM_REMEMBER_ASSISTANT") == "1")
    if os.getenv("MLXLM_DEBUG") == "1":
        print(f"[DEBUG] History mode: {history_mode} (remember_assistant={remember_assistant})")
        if not remember_assistant:
            print("[DEBUG] Assistant responses will NOT be stored in history (Q&A mode).")

    # Initialize prompt session (with fallback to plain input)
    if PROMPT_TOOLKIT_AVAILABLE:
        # Set up history file path (mlxlm_data/input_history)
        project_root = Path(__file__).parent.parent
        data_dir = project_root / "mlxlm_data"
        data_dir.mkdir(exist_ok=True)
        history_file = data_dir / "input_history"

        # Create custom key bindings
        kb = KeyBindings()

        # Option+Enter (Mac) / Alt+Enter (Linux): Insert newline (for multiline input)
        # Note: Shift+Enter is not directly supported in prompt-toolkit
        @kb.add('escape', 'enter')
        def _(event):
            event.current_buffer.insert_text('\n')

        # Also support Ctrl+J for newline (common in terminals)
        @kb.add('c-j')
        def _(event):
            event.current_buffer.insert_text('\n')

        # Ctrl+R : Move cursor to beginning of line (alternative to Ctrl+A)
        @kb.add('c-r')
        def _(event):
            event.current_buffer.cursor_position = 0

        # Ctrl+O : Move cursor to end of line (alternative to Ctrl+E)
        @kb.add('c-o')
        def _(event):
            event.current_buffer.cursor_position = len(event.current_buffer.text)

        # Note: History navigation uses default Emacs bindings (Ctrl+P/Ctrl+N)
        # Note: Command key is not directly supported in prompt-toolkit

        # Custom completer that only shows commands when input starts with /
        class SlashCommandCompleter(Completer):
            """Completer that only suggests /exit and /bye when user types /"""
            def __init__(self, commands):
                self.commands = commands

            def get_completions(self, document, complete_event):
                text = document.text_before_cursor
                # Only show completions if text starts with /
                if text.startswith('/'):
                    word = text[1:].lower()  # Remove / and get lowercase for matching
                    for cmd in self.commands:
                        cmd_name = cmd[1:].lower()  # Remove / from command name
                        if cmd_name.startswith(word):
                            yield Completion(cmd, start_position=-len(text))

        # Custom auto-suggest that shows inline suggestions for slash commands
        class SlashCommandAutoSuggest(AutoSuggest):
            """AutoSuggest that shows gray inline text for /exit and /bye commands"""
            def __init__(self, commands):
                self.commands = commands

            def get_suggestion(self, buffer: Buffer, document: Document):
                text = document.text
                # Only suggest if text starts with / and is not complete
                if text.startswith('/') and text not in self.commands:
                    word = text[1:].lower()  # Remove / and lowercase
                    for cmd in self.commands:
                        cmd_name = cmd[1:].lower()  # Remove / from command
                        if cmd_name.startswith(word) and cmd != text:
                            # Return the remaining part as gray suggestion
                            suggestion_text = cmd[len(text):]
                            return Suggestion(suggestion_text)
                return None

        # Create command completer and auto-suggest for slash commands
        commands = ['/exit', '/bye', '/quit', '/help', '/clear', '/status', '/export', '/setting']
        completer = SlashCommandCompleter(commands)
        auto_suggest = SlashCommandAutoSuggest(commands)

        session = PromptSession(
            history=FileHistory(str(history_file)),  # Persistent history
            key_bindings=kb,
            completer=completer,
            complete_while_typing=False,  # Only show completions when Tab is pressed
            auto_suggest=auto_suggest,  # Show gray inline suggestions
            multiline=False,  # Single-line by default, but Shift+Enter adds newlines
        )
    else:
        session = None

    while True:
        try:
            if session:
                # Use prompt-toolkit for enhanced input experience with colored prompt
                prompt_text = ANSI(_colored("📝 Prompt: ", "user_prompt"))
                user_input = session.prompt(prompt_text).strip()
            else:
                # Fallback to plain input if prompt-toolkit not available
                user_input = input(_colored("📝 Prompt: ", "user_prompt")).strip()
        except KeyboardInterrupt:
            # Ctrl+C: Cancel current input, don't exit
            print(_colored("\n⚠️  Cancelled. Type '/exit' or '/bye' to quit.", "warning"))
            continue
        except EOFError:
            # Ctrl+D: Exit
            print(_colored("\n👋 Bye!", "success"))
            break
        # Handle slash commands
        if user_input.lower() in ["/exit", "/bye", "/quit"]:
            print(_colored("👋 Bye!", "success"))
            break

        if user_input.lower() == "/help":
            help_text = """
📖 MLX-LM Interactive Commands:

Commands:
  /exit, /bye, /quit  - Exit the chat
  /help               - Show this help message
  /clear              - Clear conversation history (with options)
  /status             - Show current session status
  /export [filename]  - Export conversation (md/txt/json)
  /setting            - Open settings menu

Keyboard Shortcuts:
  Ctrl+C              - Interrupt model generation
  Ctrl+D              - Exit (EOF)
  Ctrl+P / Ctrl+N     - Navigate history (previous/next)
  Ctrl+R / Ctrl+A     - Move to beginning of line
  Ctrl+O / Ctrl+E     - Move to end of line
  Ctrl+J              - Insert newline
  Option+Enter        - Insert newline (Mac/Linux)
  Tab                 - Show command completions
  → or Ctrl+E         - Accept inline suggestion
"""
            print(_colored(help_text, "system"))
            continue

        if user_input.lower() == "/clear":
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
                import os
                os.system('clear' if os.name != 'nt' else 'cls')
                print(_colored("✅ Screen cleared (conversation history preserved)", "success"))
            elif choice == '3':
                history.clear()
                import os
                os.system('clear' if os.name != 'nt' else 'cls')
                print("=" * 60)
                print(_colored("🧹 Everything cleared! Starting fresh...", "success"))
                print("=" * 60)
            else:
                print(_colored("❌ Cancelled", "warning"))
            continue

        if user_input.lower() == "/status":
            # Calculate statistics
            user_count = sum(1 for r, _ in history if r == "user")
            assistant_count = sum(1 for r, _ in history if r == "assistant")

            # Calculate current token usage
            try:
                full_prompt = _render_prompt(chat_mode, tokenizer, sys_prompt, history)
                current_tokens = _count_tokens(tokenizer, full_prompt)
            except Exception:
                current_tokens = 0

            # Estimate model's context limit (rough estimate)
            estimated_limit = 8192  # Default rough estimate

            status_text = f"""
📊 Current Status:

Model: {model_name}
Chat Mode: {chat_mode}
History Mode: {history_mode}

💬 Conversation:
  User messages: {user_count}
  Assistant messages: {assistant_count}
  Total turns: {len(history)}

🧮 Token Usage:
  Current context: ~{current_tokens} tokens
  Max tokens per response: {max_tokens}
  Estimated limit: ~{estimated_limit} tokens (model dependent)
  Usage: {(current_tokens / estimated_limit * 100):.1f}%

⚙️  Settings:
  Stream mode: {stream_mode}
  Time limit: {time_limit or 'none'} sec
"""
            print(_colored(status_text, "system"))
            continue

        if user_input.lower().startswith("/export"):
            # Parse /export command: /export [filename]
            parts = user_input.split(maxsplit=1)

            if len(history) == 0:
                print(_colored("⚠️  No conversation to export", "warning"))
                continue

            # Default filename with timestamp
            from datetime import datetime
            default_filename = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

            filename = parts[1].strip() if len(parts) > 1 else default_filename

            # Detect format from extension
            if filename.endswith('.txt'):
                format = 'txt'
            elif filename.endswith('.json'):
                format = 'json'
            else:
                # Default to markdown, add .md if no extension
                format = 'md'
                if not filename.endswith('.md'):
                    filename += '.md'

            export_conversation(history, filename, format, model_name)
            continue

        if user_input.lower() == "/setting":
            # Load current config, open settings menu, and save if changed
            user_config = load_user_config()
            updated_config = show_settings_menu(user_config)
            if save_user_config(updated_config):
                print(_colored("✅ Settings saved successfully", "success"))
            continue

        if not user_input: continue
        history.append(("user", user_input))

        try:
            full_prompt = _render_prompt(chat_mode, tokenizer, sys_prompt, history)
        except Exception as e:
            print(f"⚠️  Prompt rendering error ({chat_mode}): {e}")
            full_prompt = f"{system_prompt}\n\nUser: {user_input}\nAssistant:"

        if os.getenv("MLXLM_DEBUG") == "1":
            u_cnt = sum(1 for r,_ in history if r=="user")
            a_cnt = sum(1 for r,_ in history if r=="assistant")
            print(f"[DEBUG] chat_mode={chat_mode} stream_mode={stream_mode} history(user={u_cnt}, assistant={a_cnt})")
            print(f"[DEBUG] rendered_prompt_chars={len(full_prompt)}")

        # RAM estimate（KV）
        try:
            alias_dict_cfg = load_alias_dict()
            cache_key = resolve_to_cache_key(model_name, alias_dict_cfg)
            cfg = load_config_for_model(cache_key) or {}
            if isinstance(cfg.get("text_config"), dict):
                cfg = {**cfg, **cfg["text_config"]}
            layers = cfg.get("num_hidden_layers") or cfg.get("n_layer") or cfg.get("layers") or 0
            hidden = cfg.get("hidden_size") or cfg.get("n_embd") or 0
            prompt_tok = _count_tokens(tokenizer, full_prompt)
            ctx_tok = prompt_tok + int(max_tokens)
            dtype_bytes = int(os.getenv("MLXLM_KV_BYTES","2"))
            if dtype_bytes not in (1,2,4): dtype_bytes=2
            est_bytes = _estimate_kv_bytes(int(layers or 0), int(hidden or 0), int(ctx_tok), dtype_bytes=dtype_bytes)
            print(
                f"\n🧮 Context tokens: prompt≈{prompt_tok}, new≤{max_tokens}, total≤{ctx_tok}\n"
                f"🧠 KV cache est.: {_human_bytes(est_bytes)} (layers={layers or 'unknown'}, hidden={hidden or 'unknown'}, dtype={dtype_bytes*8}-bit)\n"
            )
        except Exception as _e:
            if os.getenv("MLXLM_DEBUG") == "1":
                print(f"[DEBUG] RAM estimate failed: {_e}")

        # stop sequences
        stop_seqs = stop[:] if isinstance(stop, list) else None
        env_stop = os.getenv("MLXLM_STOP", "").strip()
        if env_stop:
            extra = [s.strip() for s in env_stop.split(",") if s.strip()]
            stop_seqs = (stop_seqs or []) + extra
        no_default = os.getenv("MLXLM_NO_DEFAULT_STOPS", "0") == "1"
        if (stop_seqs is None or len(stop_seqs) == 0) and chat_mode == "harmony" and not no_default:
            stop_seqs = ["<|end|>", "<|start|>"]
        if os.getenv("MLXLM_DEBUG") == "1":
            print(f"[DEBUG] stop sequences: {stop_seqs} (no_default={no_default})")

        # generate
        try:
            print("\n🧠 Output:\n", end="", flush=True)
            start_ts = time.time()

            # Helper: try call with stop; if TypeError (unexpected 'stop'), retry without it
            def _call_generate_with_stop(prompt):
                try:
                    return generate(model, tokenizer, prompt, max_tokens=max_tokens, stop=stop_seqs)
                except TypeError as te:
                    if "unexpected keyword argument 'stop'" in str(te):
                        if os.getenv("MLXLM_DEBUG") == "1":
                            print("[DEBUG] generate(): 'stop' not supported by this mlx-lm version → retrying without stop")
                        return generate(model, tokenizer, prompt, max_tokens=max_tokens)
                    raise

            def _iter_stream_with_stop(prompt):
                try:
                    return stream_generate(model, tokenizer, prompt, max_tokens=max_tokens, stop=stop_seqs)
                except TypeError as te:
                    if "unexpected keyword argument 'stop'" in str(te):
                        if os.getenv("MLXLM_DEBUG") == "1":
                            print("[DEBUG] stream_generate(): 'stop' not supported → retrying without stop")
                        return stream_generate(model, tokenizer, prompt, max_tokens=max_tokens)
                    raise

            if stream_mode == "off":
                output = _call_generate_with_stop(full_prompt)
                print(output, end="\n", flush=True)
                if remember_assistant:
                    history.append(("assistant", output))

            elif stream_mode == "final":
                # Stream only the <|channel|>final content in real time
                _buf = [] if remember_assistant else None
                try:
                    token_iter_resp = stream_generate(
                        model, tokenizer, full_prompt, max_tokens=max_tokens, stop=stop_seqs
                    )
                    token_iter = (resp.text for resp in token_iter_resp)
                    for chunk in _stream_final_from_harmony(token_iter):
                        if _buf is not None: _buf.append(chunk)
                        print(chunk, end="", flush=True)
                        if time_limit>0 and (time.time()-start_ts)>time_limit:
                            print("\n⏱️ Time limit reached, stopping.\n", flush=True); break
                except TypeError as te:
                    if "unexpected keyword argument 'stop'" in str(te):
                        if os.getenv("MLXLM_DEBUG") == "1":
                            print("[DEBUG] final-stream: 'stop' failed during iteration → retrying without stop")
                        token_iter_resp = stream_generate(
                            model, tokenizer, full_prompt, max_tokens=max_tokens
                        )
                        token_iter = (resp.text for resp in token_iter_resp)
                        for chunk in _stream_final_from_harmony(token_iter):
                            if _buf is not None: _buf.append(chunk)
                            print(chunk, end="", flush=True)
                            if time_limit>0 and (time.time()-start_ts)>time_limit:
                                print("\n⏱️ Time limit reached, stopping.\n", flush=True); break
                    else:
                        raise
                print("\n")
                if _buf is not None: history.append(("assistant","".join(_buf)))

            else:  # all
                _buf = [] if remember_assistant else None
                tail = ""
                stop_supported = True
                try:
                    stream_it = stream_generate(model, tokenizer, full_prompt, max_tokens=max_tokens, stop=stop_seqs)
                except TypeError as te:
                    if "unexpected keyword argument 'stop'" in str(te):
                        if os.getenv("MLXLM_DEBUG") == "1":
                            print("[DEBUG] stream_generate(): 'stop' not supported → streaming without stop, using marker-based break for Harmony")
                        stop_supported = False
                        stream_it = stream_generate(model, tokenizer, full_prompt, max_tokens=max_tokens)
                    else:
                        raise
                try:
                    for resp in stream_it:
                        if _buf is not None: _buf.append(resp.text)
                        print(resp.text, end="", flush=True)
                        if time_limit>0 and (time.time()-start_ts)>time_limit:
                            print("\n⏱️ Time limit reached, stopping.\n", flush=True); break
                        if not stop_supported and chat_mode == "harmony":
                            tail += resp.text
                            if "<|end|>" in tail or "<|start|>" in tail:
                                break
                            if len(tail) > 256:
                                tail = tail[-128:]
                except TypeError as te:
                    if "unexpected keyword argument 'stop'" in str(te):
                        if os.getenv("MLXLM_DEBUG") == "1":
                            print("[DEBUG] all-stream: 'stop' failed during iteration → retrying without stop")
                        stream_it = stream_generate(model, tokenizer, full_prompt, max_tokens=max_tokens)
                        for resp in stream_it:
                            if _buf is not None: _buf.append(resp.text)
                            print(resp.text, end="", flush=True)
                            if time_limit>0 and (time.time()-start_ts)>time_limit:
                                print("\n⏱️ Time limit reached, stopping.\n", flush=True); break
                    else:
                        raise
                print("\n")
                if _buf is not None: history.append(("assistant","".join(_buf)))
        except KeyboardInterrupt:
            # Ctrl+C during generation: Stop generation and return to prompt
            print(_colored("\n\n⚠️  Generation interrupted. Returning to prompt.", "warning"))
            continue
        except Exception as e:
            print(f"\n⚠️ Error generating response: {e}\n")
