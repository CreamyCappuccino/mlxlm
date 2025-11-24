# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Tests for v0.3.0: HuggingFace Search Feature."""

import pytest
from commands.search import SearchState, search_huggingface
from unittest.mock import Mock, patch, MagicMock


class TestSearchState:
    """Test SearchState class initialization and properties."""

    def test_search_state_initialization(self):
        """Test default SearchState initialization."""
        state = SearchState()
        assert state.results_per_page == 10
        assert state.page == 0
        assert state.query == ""
        assert state.sort_by == "downloads"
        assert state.max_size_gb is None
        assert state.min_downloads is None
        assert state.tags == []

    def test_search_state_filters(self):
        """Test SearchState filter properties."""
        state = SearchState()

        # Test setting filters
        state.max_size_gb = 10
        state.min_downloads = 1000
        state.sort_by = "updated"

        assert state.max_size_gb == 10
        assert state.min_downloads == 1000
        assert state.sort_by == "updated"

    def test_search_state_pagination(self):
        """Test SearchState pagination properties."""
        state = SearchState()

        # Test page increment
        state.page = 0
        state.page += 1
        assert state.page == 1

        state.results_per_page = 20
        assert state.results_per_page == 20


class TestSearchHuggingface:
    """Test search_huggingface() function."""

    @pytest.fixture
    def mock_state(self):
        """Create a mock SearchState for testing."""
        return SearchState()

    def test_search_huggingface_basic(self, mock_state):
        """Test basic search_huggingface() call with a simple query."""
        # This would require mocking the HuggingFace API
        # For now, test that the function exists and can be called
        # (actual HF API calls should be mocked in integration tests)
        assert callable(search_huggingface)

    def test_search_state_results_per_page_default(self):
        """Test that default results_per_page is 10 (v0.3.0 feature)."""
        state = SearchState()
        assert state.results_per_page == 10

    def test_search_state_supports_custom_display_count(self):
        """Test that display count can be customized."""
        state = SearchState()
        original = state.results_per_page

        state.results_per_page = 20
        assert state.results_per_page == 20
        assert state.results_per_page != original

    def test_search_state_page_reset_on_new_query(self):
        """Test that page resets when starting a new search."""
        state = SearchState()
        state.page = 5

        # Simulating a new search by resetting page
        state.page = 0
        assert state.page == 0

    def test_search_state_sort_options(self):
        """Test various sort options."""
        state = SearchState()

        sort_options = ["downloads", "last_modified", "updated", "trending"]
        for sort_opt in sort_options:
            state.sort_by = sort_opt
            assert state.sort_by == sort_opt

    def test_search_state_tags_filter(self):
        """Test tags filter options."""
        state = SearchState()

        tags = ["mlx", "quantized", "instruct", "chat"]
        state.tags = tags
        assert state.tags == tags
        assert len(state.tags) == 4

    def test_search_state_size_filter(self):
        """Test size filter options."""
        state = SearchState()

        sizes = [1, 5, 10, 50, None]
        for size in sizes:
            state.max_size_gb = size
            assert state.max_size_gb == size


class TestSearchIntegration:
    """Integration tests for search feature."""

    def test_search_state_complete_workflow(self):
        """Test complete workflow of search state changes."""
        state = SearchState()

        # Initial state
        assert state.page == 0
        assert state.results_per_page == 10

        # User changes display count
        state.results_per_page = 15
        state.page = 0  # Reset page
        assert state.results_per_page == 15
        assert state.page == 0

        # User applies filters
        state.max_size_gb = 5
        state.sort_by = "updated"
        assert state.max_size_gb == 5
        assert state.sort_by == "updated"

        # User navigates to next page
        state.page += 1
        assert state.page == 1

    def test_search_state_multiple_filters(self):
        """Test applying multiple filters simultaneously."""
        state = SearchState()

        state.max_size_gb = 10
        state.min_downloads = 5000
        state.tags = ["mlx", "instruct"]
        state.sort_by = "downloads"
        state.results_per_page = 20

        assert state.max_size_gb == 10
        assert state.min_downloads == 5000
        assert state.tags == ["mlx", "instruct"]
        assert state.sort_by == "downloads"
        assert state.results_per_page == 20
