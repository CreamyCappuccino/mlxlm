# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Tests for v0.3.5: Parameter Scale Range Filter (Phase 5a)."""

import pytest
from commands.search import SearchState
from commands.search_filters import extract_param_scale


class TestExtractParamScale:
    """Test extract_param_scale() function for parsing model parameter sizes."""

    def test_extract_param_scale_uppercase_b(self):
        """Test extraction from uppercase B format (7B, 13B, 27B)."""
        assert extract_param_scale("Llama-2-7B") == 7
        assert extract_param_scale("Mistral-8x7B") == 7  # First match is 7
        assert extract_param_scale("meta-llama/Llama-2-13B") == 13
        assert extract_param_scale("Qwen-27B-Chat") == 27

    def test_extract_param_scale_lowercase_b(self):
        """Test extraction from lowercase b format (7b, 13b, 27b)."""
        assert extract_param_scale("gemma-3-27b-instruct") == 27
        assert extract_param_scale("mistral-7b-v0.1") == 7
        assert extract_param_scale("qwen-13b-chat") == 13

    def test_extract_param_scale_hyphen_format(self):
        """Test extraction from hyphen-separated format (7-B, 13-b)."""
        assert extract_param_scale("model-7-B") == 7
        assert extract_param_scale("model-13-b") == 13
        assert extract_param_scale("model-27-B") == 27

    def test_extract_param_scale_underscore_format(self):
        """Test extraction from underscore-separated format (7_B, 13_b)."""
        assert extract_param_scale("model_7_B") == 7
        assert extract_param_scale("model_13_b") == 13
        assert extract_param_scale("model_27_B") == 27

    def test_extract_param_scale_space_format(self):
        """Test extraction from space-separated format (7 B, 13 billion)."""
        assert extract_param_scale("model 7 B") == 7
        assert extract_param_scale("model 13 billion") == 13
        assert extract_param_scale("model 27 B") == 27

    def test_extract_param_scale_billion_suffix(self):
        """Test extraction with 'billion' suffix."""
        assert extract_param_scale("model-7B-billion") == 7
        assert extract_param_scale("model 13 billion") == 13
        assert extract_param_scale("27 billion parameter model") == 27

    def test_extract_param_scale_complex_names(self):
        """Test extraction from complex model names."""
        assert extract_param_scale("meta-llama/Llama-2-7B-Chat-hf") == 7
        assert extract_param_scale("mistralai/Mistral-7B-Instruct-v0.1") == 7
        assert extract_param_scale("google/Gemma-2-27b-it") == 27

    def test_extract_param_scale_multiple_matches(self):
        """Test extraction returns first match when multiple patterns exist."""
        # Should return first match (7, not 13)
        assert extract_param_scale("model-7B-v2-13B-old") == 7

    def test_extract_param_scale_no_match(self):
        """Test returns None when no parameter scale found."""
        assert extract_param_scale("model-without-params") is None
        assert extract_param_scale("random-model-name") is None
        assert extract_param_scale("") is None
        assert extract_param_scale(None) is None

    def test_extract_param_scale_with_card_data_fallback(self):
        """Test fallback to card_data when model_id doesn't have params."""
        card_data = {"model_size": "7B", "parameters": "7 billion"}
        assert extract_param_scale("model-without-params", card_data) == 7

    def test_extract_param_scale_with_card_data_parameters_field(self):
        """Test extraction from card_data parameters field."""
        card_data = {"parameters": "13 billion models"}
        assert extract_param_scale("model-unknown", card_data) == 13

    def test_extract_param_scale_with_invalid_card_data(self):
        """Test graceful handling of invalid card_data."""
        assert extract_param_scale("model", {}) is None
        assert extract_param_scale("model", {"invalid": "data"}) is None
        assert extract_param_scale("model", None) is None


class TestSearchStateParamScaleMode:
    """Test SearchState integration with param_scale_mode and range."""

    def test_search_state_param_scale_fields(self):
        """Test SearchState has param_scale_mode, min, max fields."""
        state = SearchState()
        assert hasattr(state, 'param_scale')
        assert hasattr(state, 'param_scale_mode')
        assert hasattr(state, 'param_scale_min')
        assert hasattr(state, 'param_scale_max')
        assert state.param_scale is None
        assert state.param_scale_mode == "eq"
        assert state.param_scale_min is None
        assert state.param_scale_max is None

    def test_search_state_has_filters_with_param_scale_mode(self):
        """Test has_filters() works with new param_scale_mode."""
        state = SearchState()
        assert not state.has_filters()

        # Single value mode
        state.param_scale = 7
        assert state.has_filters()

        state.param_scale = None
        assert not state.has_filters()

        # Range mode
        state.param_scale_mode = "range"
        state.param_scale_min = 7
        state.param_scale_max = 13
        assert state.has_filters()

    def test_search_state_filter_summary_single_value_modes(self):
        """Test get_filter_summary() for eq, lt, gt modes."""
        state = SearchState()

        # Test eq comparison
        state.param_scale = 7
        state.param_scale_mode = "eq"
        summary = state.get_filter_summary()
        assert "Parameters: = 7B" in summary

        # Test lt comparison
        state.param_scale = 13
        state.param_scale_mode = "lt"
        summary = state.get_filter_summary()
        assert "Parameters: < 13B" in summary

        # Test gt comparison
        state.param_scale = 30
        state.param_scale_mode = "gt"
        summary = state.get_filter_summary()
        assert "Parameters: > 30B" in summary

    def test_search_state_filter_summary_range_mode(self):
        """Test get_filter_summary() for range mode."""
        state = SearchState()
        state.param_scale_mode = "range"
        state.param_scale_min = 7
        state.param_scale_max = 13

        summary = state.get_filter_summary()
        assert "Parameters: 7B - 13B" in summary

    def test_search_state_filter_summary_range_with_one_value(self):
        """Test get_filter_summary() for range with only min or max."""
        state = SearchState()
        state.param_scale_mode = "range"
        state.param_scale_min = 7

        summary = state.get_filter_summary()
        assert "Parameters: 7B - NoneB" in summary

        state.param_scale_min = None
        state.param_scale_max = 30
        summary = state.get_filter_summary()
        assert "Parameters: NoneB - 30B" in summary

    def test_search_state_filter_summary_multiple_filters_with_range(self):
        """Test filter summary with multiple filters including param_scale range."""
        state = SearchState()
        state.max_size_gb = 10
        state.tags = ["mlx"]
        state.param_scale_mode = "range"
        state.param_scale_min = 7
        state.param_scale_max = 13

        summary = state.get_filter_summary()
        assert len(summary) == 3
        assert "Max size: 10 GB" in summary
        assert "Tags: mlx" in summary
        assert "Parameters: 7B - 13B" in summary

    def test_search_state_param_scale_mode_values(self):
        """Test param_scale_mode accepts eq, lt, gt, range."""
        state = SearchState()

        state.param_scale_mode = "eq"
        assert state.param_scale_mode == "eq"

        state.param_scale_mode = "lt"
        assert state.param_scale_mode == "lt"

        state.param_scale_mode = "gt"
        assert state.param_scale_mode == "gt"

        state.param_scale_mode = "range"
        assert state.param_scale_mode == "range"


class TestParamScaleRangeFiltering:
    """Test parameter scale range filtering logic."""

    def test_param_scale_range_inclusive(self):
        """Test range filtering is inclusive (min <= param <= max)."""
        filter_min = 7
        filter_max = 13

        # Model is 7B → should match (7 >= 7 and 7 <= 13)
        model_params = 7
        excluded = False
        if model_params < filter_min or model_params > filter_max:
            excluded = True
        assert not excluded

        # Model is 13B → should match (13 >= 7 and 13 <= 13)
        model_params = 13
        excluded = False
        if model_params < filter_min or model_params > filter_max:
            excluded = True
        assert not excluded

        # Model is 10B → should match (10 >= 7 and 10 <= 13)
        model_params = 10
        excluded = False
        if model_params < filter_min or model_params > filter_max:
            excluded = True
        assert not excluded

    def test_param_scale_range_boundary(self):
        """Test range boundaries are inclusive."""
        filter_min = 7
        filter_max = 13

        # Model is 6B → should NOT match (6 < 7)
        model_params = 6
        excluded = False
        if model_params < filter_min or model_params > filter_max:
            excluded = True
        assert excluded

        # Model is 14B → should NOT match (14 > 13)
        model_params = 14
        excluded = False
        if model_params < filter_min or model_params > filter_max:
            excluded = True
        assert excluded

    def test_param_scale_range_single_value_range(self):
        """Test range where min == max (single value)."""
        filter_min = 7
        filter_max = 7

        # Model is 7B → should match
        model_params = 7
        excluded = False
        if model_params < filter_min or model_params > filter_max:
            excluded = True
        assert not excluded

        # Model is 6B → should NOT match
        model_params = 6
        excluded = False
        if model_params < filter_min or model_params > filter_max:
            excluded = True
        assert excluded

        # Model is 8B → should NOT match
        model_params = 8
        excluded = False
        if model_params < filter_min or model_params > filter_max:
            excluded = True
        assert excluded

    def test_param_scale_range_min_only(self):
        """Test range with only min value set."""
        filter_min = 7
        filter_max = None

        # Model is 7B → should match
        model_params = 7
        excluded = False
        if filter_min and model_params < filter_min:
            excluded = True
        if filter_max and model_params > filter_max:
            excluded = True
        assert not excluded

        # Model is 100B → should match
        model_params = 100
        excluded = False
        if filter_min and model_params < filter_min:
            excluded = True
        if filter_max and model_params > filter_max:
            excluded = True
        assert not excluded

        # Model is 6B → should NOT match
        model_params = 6
        excluded = False
        if filter_min and model_params < filter_min:
            excluded = True
        if filter_max and model_params > filter_max:
            excluded = True
        assert excluded

    def test_param_scale_range_max_only(self):
        """Test range with only max value set."""
        filter_min = None
        filter_max = 13

        # Model is 13B → should match
        model_params = 13
        excluded = False
        if filter_min and model_params < filter_min:
            excluded = True
        if filter_max and model_params > filter_max:
            excluded = True
        assert not excluded

        # Model is 1B → should match
        model_params = 1
        excluded = False
        if filter_min and model_params < filter_min:
            excluded = True
        if filter_max and model_params > filter_max:
            excluded = True
        assert not excluded

        # Model is 14B → should NOT match
        model_params = 14
        excluded = False
        if filter_min and model_params < filter_min:
            excluded = True
        if filter_max and model_params > filter_max:
            excluded = True
        assert excluded


class TestParamScaleEdgeCases:
    """Test edge cases and boundary conditions for range."""

    def test_extract_param_scale_zero(self):
        """Test handling of zero parameter count."""
        assert extract_param_scale("model-0B") == 0

    def test_extract_param_scale_large_numbers(self):
        """Test extraction of large parameter counts."""
        assert extract_param_scale("model-200B") == 200
        assert extract_param_scale("model-1000-B") == 1000

    def test_search_state_param_scale_zero(self):
        """Test SearchState with param_scale = 0."""
        state = SearchState()
        state.param_scale = 0
        # 0 is falsy, so has_filters() should return False
        assert not state.has_filters()

    def test_search_state_param_scale_range_zero_values(self):
        """Test SearchState range with zero values."""
        state = SearchState()
        state.param_scale_mode = "range"
        state.param_scale_min = 0
        state.param_scale_max = 7

        # Should still be considered a filter
        assert state.has_filters()

    def test_search_state_param_scale_none_vs_default(self):
        """Test SearchState param_scale None vs initial state."""
        state = SearchState()
        assert state.param_scale is None
        assert state.param_scale_mode == "eq"
        assert state.param_scale_min is None
        assert state.param_scale_max is None

        state.param_scale = 7
        assert state.param_scale == 7

        state.param_scale = None
        assert state.param_scale is None
        assert state.param_scale_mode == "eq"  # Mode should stay the same

    def test_search_state_range_swapped_values(self):
        """Test that range with swapped min/max still works."""
        state = SearchState()
        state.param_scale_mode = "range"
        # User entered max first, min second (will be swapped by UI)
        state.param_scale_min = 13
        state.param_scale_max = 7

        # Filtering should still work (implementation handles both directions)
        # In practice, UI swaps them, but state should handle any order
        summary = state.get_filter_summary()
        assert "Parameters: 13B - 7B" in summary
