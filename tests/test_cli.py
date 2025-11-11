"""
Unit tests for mlxlm.py CLI entry point

Tests cover:
- Command line argument parsing
- Command routing to appropriate handlers
- Error handling for invalid commands
"""

import pytest
import sys
from unittest.mock import patch, MagicMock, call
from io import StringIO

# Import the main function
from mlxlm import main


# ===== Tests: Command routing =====

class TestCommandRouting:
    """Tests for CLI command routing"""

    @patch('mlxlm.list_models')
    @patch('sys.argv', ['mlxlm', 'list'])
    def test_list_command(self, mock_list):
        """Test that 'list' command routes to list_models()"""
        main()
        mock_list.assert_called_once()

    @patch('mlxlm.show_info')
    @patch('mlxlm.load_alias_dict')
    @patch('mlxlm.resolve_model_name')
    @patch('sys.argv', ['mlxlm', 'show', 'gemma3'])
    def test_show_command(self, mock_resolve, mock_load_alias, mock_show):
        """Test that 'show' command routes to show_info()"""
        mock_load_alias.return_value = {"models--google--gemma-3-27b-it": "gemma3"}
        mock_resolve.return_value = "google/gemma-3-27b-it"

        main()

        mock_show.assert_called_once()

    @patch('mlxlm.cmd_doctor')
    @patch('sys.argv', ['mlxlm', 'doctor'])
    def test_doctor_command(self, mock_doctor):
        """Test that 'doctor' command routes to cmd_doctor()"""
        main()
        mock_doctor.assert_called_once()

    @patch('mlxlm.pull_model')
    @patch('mlxlm.load_alias_dict')
    @patch('mlxlm.resolve_model_name')
    @patch('sys.argv', ['mlxlm', 'pull', 'gemma3'])
    def test_pull_command(self, mock_resolve, mock_load_alias, mock_pull):
        """Test that 'pull' command routes to pull_model()"""
        mock_load_alias.return_value = {"models--google--gemma-3-27b-it": "gemma3"}
        mock_resolve.return_value = "google/gemma-3-27b-it"

        main()

        mock_pull.assert_called_once()

    @patch('mlxlm.remove_models')
    @patch('sys.argv', ['mlxlm', 'remove', 'gemma3', '--yes'])
    def test_remove_command(self, mock_remove):
        """Test that 'remove' command routes to remove_models()"""
        main()
        mock_remove.assert_called_once()

    @patch('commands.alias_main')
    @patch('sys.argv', ['mlxlm', 'alias'])
    def test_alias_command_interactive(self, mock_alias_main):
        """Test that 'alias' command without subcommand goes to interactive mode"""
        main()
        mock_alias_main.assert_called_once_with([])

    @patch('commands.alias_main')
    @patch('sys.argv', ['mlxlm', 'alias', 'add', 'google/gemma-3-27b-it', 'gemma3'])
    def test_alias_add_subcommand(self, mock_alias_main):
        """Test that 'alias add' routes correctly"""
        main()
        mock_alias_main.assert_called_once_with(['add', 'google/gemma-3-27b-it', 'gemma3'])

    @patch('mlxlm.run_model')
    @patch('mlxlm.load_alias_dict')
    @patch('mlxlm.resolve_model_name')
    @patch('mlxlm._preflight_and_maybe_adjust_chat')
    @patch('sys.argv', ['mlxlm', 'run', 'gemma3'])
    def test_run_command(self, mock_preflight, mock_resolve, mock_load_alias, mock_run):
        """Test that 'run' command routes to run_model()"""
        mock_load_alias.return_value = {"models--google--gemma-3-27b-it": "gemma3"}
        mock_resolve.return_value = "google/gemma-3-27b-it"
        mock_preflight.return_value = "auto"

        main()

        mock_run.assert_called_once()


# ===== Tests: Argument parsing =====

class TestArgumentParsing:
    """Tests for CLI argument parsing"""

    @patch('mlxlm.list_models')
    @patch('sys.argv', ['mlxlm', 'list', 'all'])
    def test_list_all_scope(self, mock_list):
        """Test parsing 'list all' argument"""
        main()
        # Should call with show_all=True
        mock_list.assert_called_once()

    @patch('mlxlm.show_info')
    @patch('mlxlm.load_alias_dict')
    @patch('mlxlm.resolve_model_name')
    @patch('sys.argv', ['mlxlm', 'show', 'gemma3', '--full'])
    def test_show_full_flag(self, mock_resolve, mock_load_alias, mock_show):
        """Test parsing '--full' flag for show command"""
        mock_load_alias.return_value = {}
        mock_resolve.return_value = "gemma3"

        main()

        # Verify show_info was called with full=True
        call_args = mock_show.call_args
        assert call_args[1]['full'] == True

    @patch('mlxlm.run_model')
    @patch('mlxlm.load_alias_dict')
    @patch('mlxlm.resolve_model_name')
    @patch('mlxlm._preflight_and_maybe_adjust_chat')
    @patch('sys.argv', ['mlxlm', 'run', 'gemma3', '--chat', 'harmony', '--max-tokens', '4096'])
    def test_run_with_options(self, mock_preflight, mock_resolve, mock_load_alias, mock_run):
        """Test parsing run command with multiple options"""
        mock_load_alias.return_value = {}
        mock_resolve.return_value = "gemma3"
        mock_preflight.return_value = "harmony"

        main()

        # Verify run_model was called with correct arguments
        call_args = mock_run.call_args
        assert call_args[1]['chat_mode'] == 'harmony'
        assert call_args[1]['max_tokens'] == 4096

    @patch('mlxlm.remove_models')
    @patch('sys.argv', ['mlxlm', 'remove', 'model1', 'model2', '--yes', '--dry-run'])
    def test_remove_multiple_targets_with_flags(self, mock_remove):
        """Test parsing remove command with multiple targets and flags"""
        main()

        call_args = mock_remove.call_args
        assert call_args[0][0] == ['model1', 'model2']
        assert call_args[1]['assume_yes'] == True
        assert call_args[1]['dry_run'] == True


# ===== Tests: Error handling =====

class TestErrorHandling:
    """Tests for CLI error handling"""

    @patch('sys.exit')
    @patch('sys.argv', ['mlxlm', 'show'])
    def test_show_without_model_name(self, mock_exit, capsys):
        """Test that 'show' without model name prints error"""
        # Make sys.exit actually raise SystemExit to stop execution
        mock_exit.side_effect = SystemExit(1)

        with pytest.raises(SystemExit):
            main()

        # Should exit with error
        mock_exit.assert_called_with(1)
        captured = capsys.readouterr()
        assert "must specify a model name" in captured.out

    @patch('sys.argv', ['mlxlm', 'help'])
    @patch('sys.exit')
    def test_help_command(self, mock_exit):
        """Test that 'help' command exits gracefully"""
        main()
        mock_exit.assert_called_with(0)

    @patch('sys.argv', ['mlxlm'])
    @patch('sys.exit')
    def test_no_command(self, mock_exit):
        """Test that running with no command shows help"""
        main()
        mock_exit.assert_called_with(0)


# ===== Summary =====

"""
Test summary:
- 8 command routing tests
- 4 argument parsing tests
- 3 error handling tests

Total: 15 unit tests for mlxlm.py
"""
