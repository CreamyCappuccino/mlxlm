"""
Unit tests for commands.py command implementations

Tests cover:
- list_models: Model listing with alias display
- show_info: Model information display
- alias_main: Alias management (add/edit/remove)
- cmd_doctor: Environment diagnostics
- Helper functions for alias syncing
"""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock, call
from io import StringIO

# Import functions to test
from commands import (
    list_models,
    show_info,
    alias_main,
    cmd_doctor,
    _list_cached_models_all,
    _sync_alias_from_cache,
)


# ===== Fixtures =====

@pytest.fixture
def mock_hub_dir(tmp_path):
    """Create a mock HuggingFace hub directory structure"""
    hub = tmp_path / ".cache" / "huggingface" / "hub"
    hub.mkdir(parents=True)

    # Create model directories
    model1 = hub / "models--google--gemma-3-27b-it"
    model1.mkdir()
    (model1 / "snapshots").mkdir()
    (model1 / "snapshots" / "abc123").mkdir()

    model2 = hub / "models--meta--llama3-8b"
    model2.mkdir()
    (model2 / "snapshots").mkdir()
    (model2 / "snapshots" / "def456").mkdir()

    return str(hub)


@pytest.fixture
def mock_alias_data():
    """Mock alias dictionary for testing"""
    return {
        "models--google--gemma-3-27b-it": "gemma3",
        "models--meta--llama3-8b": "llama3",
        "models--test--model": ""
    }


# ===== Tests: list_models =====

class TestListModels:
    """Tests for model listing functionality"""

    @patch('commands.list.os.path.expanduser')
    @patch('commands.list.os.path.exists')
    @patch('commands.list.os.listdir')
    @patch('commands.list.os.path.isdir')
    @patch('commands.list.os.scandir')
    @patch('commands.list.load_alias_dict')
    @patch('commands.list.subprocess.check_output')
    @patch('commands.list.os.walk')
    @patch('commands.list.os.path.getmtime')
    def test_list_models_with_aliases(
        self, mock_getmtime, mock_walk, mock_subprocess, mock_load_alias,
        mock_scandir, mock_isdir, mock_listdir, mock_exists, mock_expanduser, capsys
    ):
        """Test listing models with aliases displayed"""
        # Setup mocks
        mock_expanduser.return_value = "/home/user/.cache/huggingface/hub"
        mock_exists.return_value = True
        mock_listdir.return_value = ["models--google--gemma-3-27b-it", "models--meta--llama3-8b"]
        mock_isdir.return_value = True

        # Mock scandir for snapshots
        mock_entry = MagicMock()
        mock_entry.is_dir.return_value = True
        mock_scandir.return_value = [mock_entry]

        mock_load_alias.return_value = {
            "models--google--gemma-3-27b-it": "gemma3",
            "models--meta--llama3-8b": ""
        }
        mock_subprocess.return_value = b"5.2G\t/path"
        mock_walk.return_value = [("/root", [], ["file1.txt"])]
        mock_getmtime.return_value = 1700000000.0

        # Run
        list_models()

        # Verify output
        captured = capsys.readouterr()
        assert "Installed MLX Models" in captured.out
        assert "models--google--gemma-3-27b-it" in captured.out
        assert "gemma3" in captured.out

    @patch('commands.list.os.path.exists')
    def test_list_models_no_directory(self, mock_exists, capsys):
        """Test listing when model directory doesn't exist"""
        mock_exists.return_value = False

        list_models()

        captured = capsys.readouterr()
        assert "Model directory not found" in captured.out


# ===== Tests: show_info =====

class TestShowInfo:
    """Tests for model info display"""

    @patch('commands.show.load_alias_dict')
    @patch('commands.show.os.path.exists')
    @patch('commands.show.subprocess.check_output')
    @patch('commands.show.load_config_for_model')
    def test_show_info_success(
        self, mock_load_config, mock_subprocess, mock_exists, mock_load_alias, capsys
    ):
        """Test showing model info successfully"""
        mock_load_alias.return_value = {"models--google--gemma-3-27b-it": "gemma3"}
        mock_exists.return_value = True
        mock_subprocess.return_value = b"5.2G\t/path"
        mock_load_config.return_value = {
            "architectures": ["GemmaForCausalLM"],
            "hidden_size": 4096,
            "num_hidden_layers": 32,
            "num_attention_heads": 32
        }

        show_info("gemma3")

        captured = capsys.readouterr()
        assert "MODEL INFO" in captured.out
        assert "gemma3" in captured.out
        assert "4096" in captured.out

    @patch('commands.show.load_alias_dict')
    @patch('commands.show.os.path.exists')
    def test_show_info_not_found(self, mock_exists, mock_load_alias, capsys):
        """Test showing info for non-existent model"""
        mock_load_alias.return_value = {}
        mock_exists.return_value = False

        show_info("nonexistent")

        captured = capsys.readouterr()
        assert "Model not found" in captured.out


# ===== Tests: alias_main =====

class TestAliasManagement:
    """Tests for alias add/edit/remove commands"""

    @patch('commands.alias._sync_alias_from_cache')
    @patch('commands.alias.load_alias_dict')
    @patch('builtins.open', new_callable=mock_open)
    @patch('commands.alias.alias_file_path', '/tmp/.mlxlm_aliases.json')
    def test_alias_add(self, mock_file, mock_load_alias, mock_sync, capsys):
        """Test adding a new alias"""
        mock_load_alias.return_value = {}

        alias_main(["add", "google/gemma-3-27b-it", "gemma3"])

        # Verify file was written
        mock_file.assert_called()
        captured = capsys.readouterr()
        assert "Added alias" in captured.out or "gemma3" in captured.out

    @patch('commands.alias._sync_alias_from_cache')
    @patch('commands.alias.load_alias_dict')
    @patch('builtins.open', new_callable=mock_open)
    @patch('commands.alias.alias_file_path', '/tmp/.mlxlm_aliases.json')
    def test_alias_remove(self, mock_file, mock_load_alias, mock_sync, capsys):
        """Test removing an alias"""
        mock_load_alias.return_value = {
            "models--google--gemma-3-27b-it": "gemma3"
        }

        alias_main(["remove", "gemma3"])

        captured = capsys.readouterr()
        assert "Removed" in captured.out or "gemma3" in captured.out

    @patch('commands.alias._sync_alias_from_cache')
    @patch('commands.alias.load_alias_dict')
    def test_alias_list(self, mock_load_alias, mock_sync, capsys):
        """Test listing all aliases"""
        mock_load_alias.return_value = {
            "models--google--gemma-3-27b-it": "gemma3",
            "models--meta--llama3-8b": "llama3"
        }

        alias_main(["list"])

        captured = capsys.readouterr()
        assert "gemma3" in captured.out
        assert "llama3" in captured.out

    @patch('commands.alias._sync_alias_from_cache')
    @patch('commands.alias.load_alias_dict')
    @patch('builtins.open', new_callable=mock_open)
    @patch('commands.alias.alias_file_path', '/tmp/.mlxlm_aliases.json')
    def test_alias_edit(self, mock_file, mock_load_alias, mock_sync, capsys):
        """Test editing an existing alias"""
        mock_load_alias.return_value = {
            "models--google--gemma-3-27b-it": "gemma3"
        }

        alias_main(["edit", "gemma3", "gemma-new"])

        captured = capsys.readouterr()
        assert "Changed" in captured.out or "gemma" in captured.out


# ===== Tests: cmd_doctor =====

class TestDoctor:
    """Tests for environment diagnostics"""

    @patch('importlib.metadata.version')
    @patch('importlib.util.find_spec')
    @patch('core._probe_mlx_runtime')
    @patch('core._detect_harmony_renderer')
    @patch('commands.doctor.os.path.isdir')
    def test_doctor_all_ok(
        self, mock_isdir, mock_harmony, mock_probe, mock_find_spec, mock_version, capsys
    ):
        """Test doctor when everything is OK"""
        mock_version.side_effect = lambda x: "0.29.2" if x == "mlx" else "0.28.2"
        mock_find_spec.return_value = MagicMock()
        mock_probe.return_value = (True, "OK", "/path/to/libmlx.dylib")
        mock_harmony.return_value = MagicMock()  # Renderer found
        mock_isdir.return_value = True

        cmd_doctor()

        captured = capsys.readouterr()
        assert "mlxlm doctor" in captured.out
        assert "Python" in captured.out

    @patch('importlib.metadata.version')
    @patch('importlib.util.find_spec')
    @patch('core._probe_mlx_runtime')
    @patch('core._detect_harmony_renderer')
    @patch('commands.doctor.os.path.isdir')
    def test_doctor_missing_dependencies(
        self, mock_isdir, mock_harmony, mock_probe, mock_find_spec, mock_version, capsys
    ):
        """Test doctor when dependencies are missing"""
        mock_version.side_effect = Exception("Not installed")
        mock_find_spec.return_value = None
        mock_probe.return_value = (False, "Not found", None)
        mock_harmony.return_value = None  # No renderer
        mock_isdir.return_value = False

        cmd_doctor()

        captured = capsys.readouterr()
        assert "mlxlm doctor" in captured.out


# ===== Tests: Helper functions =====

class TestHelperFunctions:
    """Tests for internal helper functions"""

    @patch('commands.alias.os.path.isdir')
    @patch('commands.alias.os.listdir')
    @patch('commands.alias.os.scandir')
    def test_list_cached_models_all(self, mock_scandir, mock_listdir, mock_isdir):
        """Test listing all cached models"""
        mock_isdir.side_effect = lambda path: "hub" in path or "models--" in path
        mock_listdir.return_value = [
            "models--google--gemma-3-27b-it",
            "models--meta--llama3-8b",
            "not-a-model"
        ]

        # Mock scandir for snapshots
        mock_entry = MagicMock()
        mock_entry.is_dir.return_value = True
        mock_scandir.return_value = [mock_entry]

        with patch('commands.alias.os.path.expanduser', return_value="/home/user/.cache/huggingface/hub"):
            result = _list_cached_models_all()

        assert "models--google--gemma-3-27b-it" in result
        assert "models--meta--llama3-8b" in result
        assert "not-a-model" not in result

    @patch('commands.alias._list_cached_models_all')
    @patch('commands.alias.load_alias_dict')
    @patch('builtins.open', new_callable=mock_open)
    @patch('commands.alias.alias_file_path', '/tmp/.mlxlm_aliases.json')
    def test_sync_alias_from_cache_new_models(
        self, mock_file, mock_load_alias, mock_list_models, capsys
    ):
        """Test syncing aliases when new models are found"""
        mock_list_models.return_value = [
            "models--google--gemma-3-27b-it",
            "models--meta--llama3-8b"
        ]
        mock_load_alias.return_value = {
            "models--google--gemma-3-27b-it": "gemma3"
        }

        _sync_alias_from_cache()

        # Should add the new model to alias file
        captured = capsys.readouterr()
        # Sync should update file when new models found
        # (File write is mocked, just verify no crash)


# ===== Summary =====

"""
Test summary:
- 2 list_models tests
- 2 show_info tests
- 4 alias_main tests (add/edit/remove/list)
- 2 cmd_doctor tests
- 2 helper function tests

Total: 12 unit tests for commands.py
"""
