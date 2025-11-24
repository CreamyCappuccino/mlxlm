# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Tests for v0.3.3: Unified Menu & Slash Commands (Phase 2-3)."""

import pytest
from commands.search_interactive import parse_menu_choice, parse_slash_command
from commands.search import SearchState


class TestParseMenuChoice:
    """Test parse_menu_choice() function for menu input parsing."""

    def test_parse_menu_choice_next_page(self):
        """Test 'n' or 'N' input for next page."""
        action, param = parse_menu_choice("n", max_display=10)
        assert action == "next_page"
        assert param is None

        action, param = parse_menu_choice("N", max_display=10)
        assert action == "next_page"
        assert param is None

    def test_parse_menu_choice_filters(self):
        """Test 'f' or 'F' input for filters menu."""
        action, param = parse_menu_choice("f", max_display=10)
        assert action == "filters"
        assert param is None

        action, param = parse_menu_choice("F", max_display=10)
        assert action == "filters"
        assert param is None

    def test_parse_menu_choice_new_search(self):
        """Test 's' or 'S' input for new search."""
        action, param = parse_menu_choice("s", max_display=10)
        assert action == "new_search"
        assert param is None

        action, param = parse_menu_choice("S", max_display=10)
        assert action == "new_search"
        assert param is None

    def test_parse_menu_choice_display_count(self):
        """Test 'd' or 'D' input for display count change."""
        action, param = parse_menu_choice("d", max_display=10)
        assert action == "set_display_count"
        assert param is None

        action, param = parse_menu_choice("D", max_display=10)
        assert action == "set_display_count"
        assert param is None

    def test_parse_menu_choice_exit(self):
        """Test '0', 'exit', 'q', 'quit' input for exit."""
        action, param = parse_menu_choice("0", max_display=10)
        assert action == "exit"
        assert param is None

        action, param = parse_menu_choice("exit", max_display=10)
        assert action == "exit"
        assert param is None

        action, param = parse_menu_choice("q", max_display=10)
        assert action == "exit"
        assert param is None

        action, param = parse_menu_choice("quit", max_display=10)
        assert action == "exit"
        assert param is None

    def test_parse_menu_choice_model_selection(self):
        """Test numeric input for model selection (1-N)."""
        # Select first model
        action, param = parse_menu_choice("1", max_display=10)
        assert action == "show_detail"
        assert param == 0

        # Select tenth model
        action, param = parse_menu_choice("10", max_display=10)
        assert action == "show_detail"
        assert param == 9

        # Select fifth model
        action, param = parse_menu_choice("5", max_display=10)
        assert action == "show_detail"
        assert param == 4

    def test_parse_menu_choice_out_of_range(self):
        """Test out-of-range numeric input."""
        action, param = parse_menu_choice("15", max_display=10)
        assert action == "invalid"
        assert param is None

        action, param = parse_menu_choice("11", max_display=10)
        assert action == "invalid"
        assert param is None

        action, param = parse_menu_choice("0", max_display=10)
        assert action == "exit"  # 0 is exit, not invalid

    def test_parse_menu_choice_invalid_input(self):
        """Test invalid menu inputs."""
        action, param = parse_menu_choice("xyz", max_display=10)
        assert action == "invalid"
        assert param is None

        action, param = parse_menu_choice("!", max_display=10)
        assert action == "invalid"
        assert param is None

    def test_parse_menu_choice_dynamic_max_display(self):
        """Test parse_menu_choice with different max_display values."""
        # max_display = 5
        action, param = parse_menu_choice("5", max_display=5)
        assert action == "show_detail"
        assert param == 4

        action, param = parse_menu_choice("6", max_display=5)
        assert action == "invalid"

        # max_display = 20
        action, param = parse_menu_choice("20", max_display=20)
        assert action == "show_detail"
        assert param == 19

        action, param = parse_menu_choice("21", max_display=20)
        assert action == "invalid"


class TestParseSlashCommand:
    """Test parse_slash_command() function for slash command parsing."""

    @pytest.fixture
    def search_state(self):
        """Create a SearchState instance for testing."""
        state = SearchState()
        state.results_per_page = 10
        return state

    @pytest.fixture
    def mock_models(self):
        """Create mock model list for testing."""
        class MockModel:
            def __init__(self, id):
                self.id = id
        return [MockModel(f"model-{i}") for i in range(50)]

    def test_parse_slash_command_search(self, search_state, mock_models):
        """Test /search <query> command."""
        result = parse_slash_command("/search llama", "", search_state, mock_models)
        assert result is not None
        # Result should contain updated models and query
        assert len(result) == 2
        # Query should be updated (though we can't easily test HF API call)

    def test_parse_slash_command_search_without_query(self, search_state, mock_models):
        """Test /search without query (should show error)."""
        # This would need capsys to capture output
        result = parse_slash_command("/search", "", search_state, mock_models)
        assert result is None

    def test_parse_slash_command_display_set_count(self, search_state, mock_models, monkeypatch):
        """Test /display <count> command to change display count."""
        monkeypatch.setattr('builtins.input', lambda _: 'n')  # Mock input to say 'no' to save
        result = parse_slash_command("/display 20", "test", search_state, mock_models)
        assert result is None
        assert search_state.results_per_page == 20
        assert search_state.page == 0

    def test_parse_slash_command_display_reset(self, search_state, mock_models, monkeypatch):
        """Test /display reset command to reset to default."""
        monkeypatch.setattr('builtins.input', lambda _: 'n')  # Mock input to say 'no' to save
        search_state.results_per_page = 20
        result = parse_slash_command("/display reset", "test", search_state, mock_models)
        assert result is None
        assert search_state.results_per_page == 10

    def test_parse_slash_command_display_invalid_count(self, search_state, mock_models):
        """Test /display with invalid count."""
        result = parse_slash_command("/display abc", "test", search_state, mock_models)
        assert result is None
        # Should maintain original count due to error

    def test_parse_slash_command_display_negative_count(self, search_state, mock_models):
        """Test /display with negative count."""
        result = parse_slash_command("/display -5", "test", search_state, mock_models)
        assert result is None
        # Should not change state due to validation

    def test_parse_slash_command_display_without_count(self, search_state, mock_models):
        """Test /display without count (should show error)."""
        result = parse_slash_command("/display", "test", search_state, mock_models)
        assert result is None

    def test_parse_slash_command_exit(self, search_state, mock_models):
        """Test /exit and /quit commands."""
        with pytest.raises(SystemExit):
            parse_slash_command("/exit", "", search_state, mock_models)

        with pytest.raises(SystemExit):
            parse_slash_command("/quit", "", search_state, mock_models)

    def test_parse_slash_command_short_format_supported(self, search_state, mock_models, monkeypatch):
        """Test that short /s and /d commands are also supported."""
        # /s qwen should work (shorthand for /search)
        result = parse_slash_command("/s qwen", "llama", search_state, mock_models)
        assert result is not None  # Should perform search

        # /d 20 should work (shorthand for /display)
        monkeypatch.setattr('builtins.input', lambda _: 'n')  # Mock input to say 'no' to save
        result = parse_slash_command("/d 20", "test", search_state, mock_models)
        assert result is None
        assert search_state.results_per_page == 20

    def test_parse_slash_command_unknown_command(self, search_state, mock_models):
        """Test unknown slash command."""
        result = parse_slash_command("/unknown", "", search_state, mock_models)
        assert result is None

    def test_parse_slash_command_next_not_supported(self, search_state, mock_models):
        """Test that /next is no longer supported (removed in v0.3.3)."""
        result = parse_slash_command("/next", "test", search_state, mock_models)
        assert result is None

    def test_parse_slash_command_filter_not_supported(self, search_state, mock_models):
        """Test that /filter is no longer supported (removed in v0.3.3)."""
        result = parse_slash_command("/filter", "test", search_state, mock_models)
        assert result is None

    def test_parse_slash_command_search_reset(self, search_state, mock_models, monkeypatch):
        """Test /search reset to reset query only."""
        # Mock search_huggingface to track calls
        search_calls = []
        def mock_search_hf(query, state):
            search_calls.append((query, state.query))
            return mock_models

        monkeypatch.setattr("commands.search_interactive.search_huggingface", mock_search_hf)

        # Set initial query
        search_state.query = "llama"
        search_state.page = 2

        # Call /search reset
        result = parse_slash_command("/search reset", "llama", search_state, mock_models)

        # Check that query was reset
        assert result is not None
        assert result == (mock_models, "")
        assert search_state.query == ""
        assert search_state.page == 0
        assert len(search_calls) == 1
        assert search_calls[0][0] == ""  # empty query passed to search_huggingface
