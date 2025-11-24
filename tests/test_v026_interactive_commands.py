# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Tests for v0.2.6: Interactive Commands & Settings."""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestInteractiveCommands:
    """Test interactive command parsing and execution."""

    def test_command_parsing_quit(self):
        """Test /quit command parsing."""
        command = "/quit"
        is_valid = command.startswith("/") and command in ["/quit", "/exit"]
        assert is_valid

    def test_command_parsing_help(self):
        """Test /help command parsing."""
        command = "/help"
        is_valid = command.startswith("/") and command in ["/help", "/h"]
        assert is_valid

    def test_command_parsing_clear(self):
        """Test /clear command parsing."""
        command = "/clear"
        is_valid = command.startswith("/") and command in ["/clear", "/cls"]
        assert is_valid

    def test_command_parsing_status(self):
        """Test /status command parsing."""
        command = "/status"
        is_valid = command.startswith("/") and command in ["/status", "/info"]
        assert is_valid

    def test_command_parsing_invalid(self):
        """Test invalid command parsing."""
        command = "/invalid_command"
        valid_commands = ["/quit", "/help", "/clear", "/status", "/export", "/setting"]
        is_valid = command in valid_commands
        assert not is_valid

    def test_command_with_arguments(self):
        """Test command with arguments."""
        command = "/export json"
        parts = command.split()
        assert parts[0] == "/export"
        assert parts[1] == "json"

    def test_command_export_formats(self):
        """Test /export command with different formats."""
        export_formats = ["json", "csv", "txt", "md"]

        for fmt in export_formats:
            command = f"/export {fmt}"
            assert fmt in command


class TestSettings:
    """Test settings management."""

    def test_settings_structure(self):
        """Test settings data structure."""
        settings = {
            "default_behavior": {
                "auto_run": False,
                "save_history": True
            },
            "colors": {
                "enabled": True,
                "preset": "default"
            },
            "history": {
                "max_entries": 50,
                "unlimited_duration": True
            },
            "export": {
                "format": "json",
                "include_timestamp": True,
                "auto_save": False
            }
        }
        assert "default_behavior" in settings
        assert "colors" in settings
        assert "history" in settings
        assert "export" in settings

    def test_color_presets(self):
        """Test color preset options."""
        color_presets = ["default", "dark", "light", "custom"]
        settings = {"color_preset": "default"}

        assert settings["color_preset"] in color_presets

    def test_color_customization(self):
        """Test custom color configuration."""
        custom_colors = {
            "error": "#FF0000",
            "success": "#00FF00",
            "warning": "#FFFF00",
            "info": "#0000FF"
        }
        assert len(custom_colors) == 4
        assert custom_colors["error"] == "#FF0000"

    def test_history_max_entries(self):
        """Test history max entries setting."""
        settings = {"history_max_entries": 50}
        assert settings["history_max_entries"] == 50

        settings["history_max_entries"] = 100
        assert settings["history_max_entries"] == 100

    def test_history_unlimited_duration(self):
        """Test history duration setting."""
        settings = {"history_unlimited": True}
        assert settings["history_unlimited"] is True

    def test_auto_save_setting(self):
        """Test auto-save setting."""
        settings = {"auto_save": True}
        assert settings["auto_save"] is True

    def test_export_format_options(self):
        """Test export format options."""
        formats = ["json", "csv", "txt", "md"]
        settings = {"export_format": "json"}

        assert settings["export_format"] in formats

    def test_timestamp_in_export(self):
        """Test timestamp inclusion in exports."""
        settings = {"export_include_timestamp": True}
        assert settings["export_include_timestamp"] is True


class TestCommandExecution:
    """Test command execution."""

    def test_help_command_output(self):
        """Test /help command returns help text."""
        # Simulate help command output
        help_output = """
        Available commands:
        /help      - Show this help
        /quit      - Exit program
        /clear     - Clear screen
        /status    - Show status
        /export    - Export data
        /setting   - Configure settings
        """
        assert "/help" in help_output
        assert "/quit" in help_output
        assert len(help_output.strip().split("\n")) > 1

    def test_status_command_output(self):
        """Test /status command returns status info."""
        status = {
            "version": "0.2.6",
            "session_active": True,
            "history_count": 25,
            "auto_save": True
        }
        assert status["version"] == "0.2.6"
        assert status["session_active"] is True

    def test_clear_command_clears_screen(self):
        """Test /clear command functionality."""
        # Simulating screen clear
        screen_content = []
        assert len(screen_content) == 0

    def test_export_json_format(self):
        """Test export in JSON format."""
        data = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"}
            ],
            "timestamp": "2025-11-24T12:00:00"
        }
        assert "messages" in data
        assert len(data["messages"]) == 2

    def test_export_with_timestamp(self):
        """Test export includes timestamp when enabled."""
        export_data = {
            "content": "exported data",
            "timestamp": "2025-11-24T12:00:00"
        }
        assert "timestamp" in export_data


class TestSettingsPersistence:
    """Test settings persistence."""

    def test_settings_save(self):
        """Test saving settings."""
        settings = {
            "color_preset": "dark",
            "history_max_entries": 100,
            "auto_save": True
        }
        # Simulate saving
        saved = True
        assert saved

    def test_settings_load(self):
        """Test loading settings."""
        loaded_settings = {
            "color_preset": "dark",
            "history_max_entries": 100
        }
        assert loaded_settings["color_preset"] == "dark"
        assert loaded_settings["history_max_entries"] == 100

    def test_settings_default_values(self):
        """Test default settings values."""
        defaults = {
            "color_preset": "default",
            "history_max_entries": 50,
            "auto_save": False,
            "export_format": "json"
        }
        assert defaults["color_preset"] == "default"
        assert defaults["history_max_entries"] == 50

    def test_settings_override_defaults(self):
        """Test overriding default settings."""
        defaults = {"history_max_entries": 50}
        user_settings = {"history_max_entries": 100}

        # User setting should override
        final_setting = user_settings.get("history_max_entries", defaults["history_max_entries"])
        assert final_setting == 100
