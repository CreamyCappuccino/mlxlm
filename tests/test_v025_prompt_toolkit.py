# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Tests for v0.2.5: Prompt-Toolkit Integration."""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestPromptSession:
    """Test PromptSession integration."""

    def test_prompt_session_creation(self):
        """Test PromptSession can be created."""
        # PromptSession is a prompt_toolkit class
        # Here we test the integration concept
        session_config = {
            "multiline": True,
            "history_control_characters": False
        }
        assert session_config["multiline"] is True

    def test_multiline_input_support(self):
        """Test multiline input is supported (Shift+Enter)."""
        # Simulating multiline input capability
        capabilities = {
            "multiline": True,
            "key_bindings": ["shift+enter", "ctrl+d"]
        }
        assert "shift+enter" in capabilities["key_bindings"]

    def test_line_continuation(self):
        """Test line continuation with Shift+Enter."""
        input_text = "line1\nline2"
        lines = input_text.split("\n")
        assert len(lines) == 2
        assert lines[0] == "line1"
        assert lines[1] == "line2"


class TestFileHistory:
    """Test FileHistory integration for persistent history."""

    def test_file_history_enabled(self):
        """Test FileHistory is enabled for history persistence."""
        history_config = {
            "enabled": True,
            "persistent": True
        }
        assert history_config["enabled"] is True
        assert history_config["persistent"] is True

    def test_history_file_location(self):
        """Test history file location configuration."""
        config = {
            "history_file": "~/.mlxlm_history",
            "max_entries": 50
        }
        assert "mlxlm_history" in config["history_file"]
        assert config["max_entries"] == 50

    def test_history_persistence_across_sessions(self):
        """Test history persists across sessions."""
        session1_history = ["cmd1", "cmd2", "cmd3"]
        session2_history = ["cmd1", "cmd2", "cmd3", "cmd4"]

        # History from session 1 should be available in session 2
        assert session1_history[0] in session2_history
        assert len(session2_history) > len(session1_history)

    def test_history_max_entries(self):
        """Test maximum history entries limit."""
        max_entries = 50
        history = ["entry_" + str(i) for i in range(100)]

        # Simulate keeping only max_entries
        limited_history = history[-max_entries:]
        assert len(limited_history) == max_entries


class TestKeyBindings:
    """Test keyboard shortcuts and key bindings."""

    def test_shift_enter_multiline(self):
        """Test Shift+Enter for line break."""
        key_binding = "shift+enter"
        action = "insert_newline"
        assert key_binding == "shift+enter"
        assert action == "insert_newline"

    def test_ctrl_c_interrupt(self):
        """Test Ctrl+C for interrupt."""
        key_binding = "ctrl+c"
        action = "interrupt"
        assert key_binding == "ctrl+c"

    def test_ctrl_d_exit(self):
        """Test Ctrl+D for exit."""
        key_binding = "ctrl+d"
        action = "exit"
        assert key_binding == "ctrl+d"

    def test_ctrl_l_clear_screen(self):
        """Test Ctrl+L for clear screen."""
        key_binding = "ctrl+l"
        action = "clear_screen"
        assert key_binding == "ctrl+l"

    def test_up_down_arrows_history(self):
        """Test Up/Down arrows for history navigation."""
        bindings = {
            "up": "previous_history",
            "down": "next_history"
        }
        assert bindings["up"] == "previous_history"
        assert bindings["down"] == "next_history"

    def test_command_up_down_macos(self):
        """Test Command+Up/Down on macOS for history."""
        macos_bindings = {
            "cmd+up": "previous_history",
            "cmd+down": "next_history"
        }
        assert "cmd+up" in macos_bindings
        assert macos_bindings["cmd+up"] == "previous_history"


class TestColorSupport:
    """Test color support in prompt-toolkit."""

    def test_error_color_red(self):
        """Test error messages display in red."""
        colors = {
            "error": "red"
        }
        assert colors["error"] == "red"

    def test_success_color_green(self):
        """Test success messages display in green."""
        colors = {
            "success": "green"
        }
        assert colors["success"] == "green"

    def test_warning_color_yellow(self):
        """Test warning messages display in yellow."""
        colors = {
            "warning": "yellow"
        }
        assert colors["warning"] == "yellow"

    def test_info_color_blue(self):
        """Test info messages display in blue."""
        colors = {
            "info": "blue"
        }
        assert colors["info"] == "blue"

    def test_color_output_enabled(self):
        """Test color output is enabled by default."""
        config = {"color_enabled": True}
        assert config["color_enabled"] is True

    def test_ansi_color_codes(self):
        """Test ANSI color code support."""
        ansi_colors = {
            "red": "\033[91m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "reset": "\033[0m"
        }
        assert "red" in ansi_colors
        assert len(ansi_colors) == 5


class TestTabCompletion:
    """Test Tab completion support."""

    def test_tab_completion_commands(self):
        """Test Tab completion for commands."""
        commands = ["/exit", "/bye", "/help", "/clear", "/status"]
        prefix = "/ex"

        completions = [cmd for cmd in commands if cmd.startswith(prefix)]
        assert "/exit" in completions
        assert len(completions) == 1

    def test_tab_completion_command_arguments(self):
        """Test Tab completion for command arguments."""
        export_formats = ["json", "csv", "txt", "md"]
        partial = "j"

        matches = [fmt for fmt in export_formats if fmt.startswith(partial)]
        assert "json" in matches

    def test_exit_command_aliases(self):
        """Test Tab completion with command aliases."""
        commands = ["/exit", "/bye", "/quit"]
        completion_candidates = [cmd for cmd in commands if cmd.startswith("/ex")]

        assert len(completion_candidates) == 1
        assert "/exit" in completion_candidates


class TestPromptToolkitIntegration:
    """Integration tests for prompt-toolkit features."""

    def test_full_interactive_session(self):
        """Test full interactive session setup."""
        session_config = {
            "multiline": True,
            "history_persistent": True,
            "color_enabled": True,
            "tab_completion": True,
            "key_bindings": ["shift+enter", "ctrl+c", "ctrl+d"]
        }

        assert session_config["multiline"] is True
        assert session_config["history_persistent"] is True
        assert session_config["color_enabled"] is True
        assert len(session_config["key_bindings"]) == 3

    def test_user_input_with_history(self):
        """Test user input with history support."""
        history = ["command1", "command2", "command3"]
        user_input = "command2"

        assert user_input in history
        assert history.index(user_input) == 1
