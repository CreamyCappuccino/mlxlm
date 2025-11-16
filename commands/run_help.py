# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Help command handler for mlxlm run."""

from .run_utils import _colored


def handle_help_command() -> None:
    """Display help information for interactive commands."""
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
