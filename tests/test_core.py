"""
Unit tests for core.py utility functions

Tests cover:
- Alias loading and resolution
- Model name transformations
- Config loading (mocked)
- Rendering functions
- Helper utilities (bytes, tokens, KV estimation)
"""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

# Import functions to test
from core import (
    load_alias_dict,
    resolve_model_name,
    repo_to_cache_name,
    resolve_to_cache_key,
    load_config_for_model,
    _compose_messages,
    _render_plain,
    render_harmony_simple,
    _human_bytes,
    _count_tokens,
    _estimate_kv_bytes,
    _apply_reasoning_to_system,
)


# ===== Fixture: Mock alias file =====

@pytest.fixture
def mock_alias_file(tmp_path):
    """Create a temporary alias file for testing"""
    alias_data = {
        "models--google--gemma-3-27b-it": "gemma3",
        "models--meta--llama3-8b": "llama3",
        "models--test--model": ""
    }
    alias_file = tmp_path / ".mlxlm_aliases.json"
    alias_file.write_text(json.dumps(alias_data, indent=2))
    return str(alias_file), alias_data


# ===== Tests: Alias loading =====

class TestAliasLoading:
    """Tests for alias file loading and management"""

    def test_load_alias_dict_success(self, mock_alias_file):
        """Test loading a valid alias file"""
        alias_path, expected = mock_alias_file

        with patch('core.alias_file_path', alias_path):
            result = load_alias_dict()

        assert result == expected
        assert "models--google--gemma-3-27b-it" in result
        assert result["models--google--gemma-3-27b-it"] == "gemma3"

    def test_load_alias_dict_missing_file(self):
        """Test loading when alias file doesn't exist"""
        with patch('core.alias_file_path', '/nonexistent/path/.mlxlm_aliases.json'):
            result = load_alias_dict()

        assert result == {}

    def test_load_alias_dict_invalid_json(self):
        """Test loading when alias file contains invalid JSON"""
        mock_data = "{ invalid json }"

        with patch('builtins.open', mock_open(read_data=mock_data)):
            with patch('core.alias_file_path', 'test.json'):
                result = load_alias_dict()

        assert result == {}


# ===== Tests: Name resolution =====

class TestNameResolution:
    """Tests for model name resolution and transformations"""

    def test_resolve_model_name_by_alias(self):
        """Test resolving a model by its alias"""
        alias_dict = {
            "models--google--gemma-3-27b-it": "gemma3",
            "models--meta--llama3-8b": "llama3"
        }

        result = resolve_model_name("gemma3", alias_dict)
        assert result == "google/gemma-3-27b-it"

    def test_resolve_model_name_case_insensitive(self):
        """Test that alias resolution is case-insensitive"""
        alias_dict = {
            "models--google--gemma-3-27b-it": "Gemma3"
        }

        result = resolve_model_name("GEMMA3", alias_dict)
        assert result == "google/gemma-3-27b-it"

    def test_resolve_model_name_with_slash(self):
        """Test resolving org/repo format (passthrough)"""
        alias_dict = {}

        result = resolve_model_name("google/gemma-3-27b-it", alias_dict)
        assert result == "google/gemma-3-27b-it"

    def test_resolve_model_name_cache_format(self):
        """Test resolving models-- cache format"""
        alias_dict = {}

        result = resolve_model_name("models--google--gemma-3-27b-it", alias_dict)
        assert result == "google/gemma-3-27b-it"

    def test_repo_to_cache_name(self):
        """Test converting repo_id to cache directory name"""
        assert repo_to_cache_name("google/gemma-3-27b-it") == "models--google--gemma-3-27b-it"
        assert repo_to_cache_name("models--google--gemma-3-27b-it") == "models--google--gemma-3-27b-it"
        assert repo_to_cache_name("simple-name") == "simple-name"

    def test_resolve_to_cache_key_by_alias(self):
        """Test resolving to cache key using alias"""
        alias_dict = {
            "models--google--gemma-3-27b-it": "gemma3"
        }

        result = resolve_to_cache_key("gemma3", alias_dict)
        assert result == "models--google--gemma-3-27b-it"

    def test_resolve_to_cache_key_by_repo(self):
        """Test resolving to cache key using repo_id"""
        alias_dict = {}

        result = resolve_to_cache_key("google/gemma-3-27b-it", alias_dict)
        assert result == "models--google--gemma-3-27b-it"


# ===== Tests: Config loading =====

class TestConfigLoading:
    """Tests for model config loading"""

    @patch('core.HfApi')
    def test_load_config_from_hf_api(self, mock_hf_api):
        """Test loading config from HuggingFace API"""
        mock_config = {"model_type": "gemma", "hidden_size": 4096}
        mock_hf_api.return_value.model_info.return_value.config = mock_config

        result = load_config_for_model("models--google--gemma-3-27b-it")

        assert result == mock_config

    @patch('core.HfApi')
    def test_load_config_offline_fallback(self, mock_hf_api):
        """Test fallback to local cache when API fails"""
        mock_hf_api.return_value.model_info.side_effect = Exception("Network error")

        # Mock local cache
        with patch.dict(os.environ, {'MLXLM_OFFLINE': '1'}):
            result = load_config_for_model("models--test--model")

        # Should return empty dict when no local cache exists
        assert result == {}


# ===== Tests: Rendering functions =====

class TestRendering:
    """Tests for prompt rendering functions"""

    def test_compose_messages_with_system(self):
        """Test composing messages with system prompt"""
        system = "You are helpful"
        history = [("user", "Hello"), ("assistant", "Hi there")]

        result = _compose_messages(system, history)

        assert len(result) == 3
        assert result[0] == {"role": "system", "content": "You are helpful"}
        assert result[1] == {"role": "user", "content": "Hello"}
        assert result[2] == {"role": "assistant", "content": "Hi there"}

    def test_compose_messages_without_system(self):
        """Test composing messages without system prompt"""
        history = [("user", "Hello")]

        result = _compose_messages("", history)

        assert len(result) == 1
        assert result[0] == {"role": "user", "content": "Hello"}

    def test_render_plain(self):
        """Test plain text rendering"""
        system = "You are helpful"
        history = [("user", "First"), ("assistant", "Response"), ("user", "Second")]

        result = _render_plain(system, history)

        assert "You are helpful" in result
        assert "User: Second" in result
        assert "Assistant:" in result

    def test_render_harmony_simple(self):
        """Test Harmony format rendering"""
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
        ]

        result = render_harmony_simple(messages)

        assert "<|start|>system<|message|>You are helpful<|end|>" in result
        assert "<|start|>user<|message|>Hello<|end|>" in result
        assert "<|start|>assistant" in result

    def test_apply_reasoning_to_system(self):
        """Test applying reasoning level to system prompt"""
        system = "You are helpful"

        result = _apply_reasoning_to_system(system, "high")
        assert result == "Reasoning: high\nYou are helpful"

        result_no_reasoning = _apply_reasoning_to_system(system, None)
        assert result_no_reasoning == "You are helpful"


# ===== Tests: Helper utilities =====

class TestHelpers:
    """Tests for utility helper functions"""

    def test_human_bytes(self):
        """Test human-readable byte formatting"""
        assert _human_bytes(0) == "0.00 B"
        assert _human_bytes(1024) == "1.00 KB"
        assert _human_bytes(1024 * 1024) == "1.00 MB"
        assert _human_bytes(1024 * 1024 * 1024) == "1.00 GB"
        assert _human_bytes(5.5 * 1024 * 1024) == "5.50 MB"

    def test_count_tokens_with_encode(self):
        """Test token counting with encode method"""
        mock_tokenizer = MagicMock()
        mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5]

        result = _count_tokens(mock_tokenizer, "Hello world")
        assert result == 5

    def test_count_tokens_fallback(self):
        """Test token counting fallback (char count / 4)"""
        mock_tokenizer = MagicMock()
        mock_tokenizer.encode.side_effect = Exception("No encode method")
        mock_tokenizer.side_effect = Exception("No call method")

        result = _count_tokens(mock_tokenizer, "Hello world")
        # len("Hello world") = 11, 11/4 = 2.75 -> max(1, int(2.75)) = 2
        assert result == 2

    def test_estimate_kv_bytes(self):
        """Test KV cache memory estimation"""
        layers = 32
        hidden_size = 4096
        ctx_tokens = 1000
        dtype_bytes = 2  # 16-bit

        result = _estimate_kv_bytes(layers, hidden_size, ctx_tokens, dtype_bytes)

        # Expected: 32 * 1000 * (2 * 4096 * 2) = 524,288,000
        expected = 32 * 1000 * (2 * 4096 * 2)
        assert result == expected

    def test_estimate_kv_bytes_zero_values(self):
        """Test KV estimation with zero values"""
        assert _estimate_kv_bytes(0, 4096, 1000) == 0
        assert _estimate_kv_bytes(32, 0, 1000) == 0
        assert _estimate_kv_bytes(32, 4096, 0) == 0


# ===== Summary =====

"""
Test summary:
- 3 alias loading tests
- 7 name resolution tests
- 2 config loading tests
- 5 rendering tests
- 5 helper utility tests

Total: 22 unit tests for core.py
"""
