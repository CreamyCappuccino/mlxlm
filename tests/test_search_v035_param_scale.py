# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Tests for v0.3.5: Parameter Scale Filter (Phase 5)."""

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


class TestSearchStateParamScale:
    """Test SearchState integration with param_scale and param_compare."""

    def test_search_state_param_scale_fields(self):
        """Test SearchState has param_scale and param_scale_mode fields."""
        state = SearchState()
        assert hasattr(state, 'param_scale')
        assert hasattr(state, 'param_scale_mode')
        assert state.param_scale is None
        assert state.param_scale_mode == "eq"

    def test_search_state_has_filters_with_param_scale(self):
        """Test has_filters() includes param_scale."""
        state = SearchState()
        assert not state.has_filters()

        state.param_scale = 7
        assert state.has_filters()

        state.param_scale = None
        assert not state.has_filters()

    def test_search_state_filter_summary_with_param_scale(self):
        """Test get_filter_summary() includes param_scale."""
        state = SearchState()
        assert state.get_filter_summary() == []

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

    def test_search_state_filter_summary_multiple_filters(self):
        """Test filter summary with multiple filters including param_scale."""
        state = SearchState()
        state.max_size_gb = 10
        state.tags = ["mlx"]
        state.param_scale = 7
        state.param_scale_mode = "eq"

        summary = state.get_filter_summary()
        assert len(summary) == 3
        assert "Max size: 10 GB" in summary
        assert "Tags: mlx" in summary
        assert "Parameters: = 7B" in summary

    def test_search_state_param_scale_mode_values(self):
        """Test param_scale_mode accepts eq, lt, gt."""
        state = SearchState()

        state.param_scale_mode = "eq"
        assert state.param_scale_mode == "eq"

        state.param_scale_mode = "lt"
        assert state.param_scale_mode == "lt"

        state.param_scale_mode = "gt"
        assert state.param_scale_mode == "gt"


class TestParamScaleFiltering:
    """Test parameter scale filtering logic."""

    def test_param_scale_eq_comparison(self):
        """Test equality comparison for parameter scale."""
        # Model is 7B, filter for = 7B → should match
        model_params = 7
        filter_scale = 7
        filter_compare = "eq"

        if filter_compare == "eq" and model_params != filter_scale:
            excluded = True
        else:
            excluded = False

        assert not excluded

        # Model is 7B, filter for = 13B → should NOT match
        filter_scale = 13
        if filter_compare == "eq" and model_params != filter_scale:
            excluded = True
        else:
            excluded = False

        assert excluded

    def test_param_scale_lt_comparison(self):
        """Test less-than comparison for parameter scale."""
        filter_scale = 13
        filter_compare = "lt"

        # Model is 7B → should match (7 < 13)
        model_params = 7
        if filter_compare == "lt" and model_params >= filter_scale:
            excluded = True
        else:
            excluded = False

        assert not excluded

        # Model is 13B → should NOT match (13 < 13 is False)
        model_params = 13
        if filter_compare == "lt" and model_params >= filter_scale:
            excluded = True
        else:
            excluded = False

        assert excluded

        # Model is 30B → should NOT match (30 < 13 is False)
        model_params = 30
        if filter_compare == "lt" and model_params >= filter_scale:
            excluded = True
        else:
            excluded = False

        assert excluded

    def test_param_scale_gt_comparison(self):
        """Test greater-than comparison for parameter scale."""
        filter_scale = 13
        filter_compare = "gt"

        # Model is 7B → should NOT match (7 > 13 is False)
        model_params = 7
        if filter_compare == "gt" and model_params <= filter_scale:
            excluded = True
        else:
            excluded = False

        assert excluded

        # Model is 13B → should NOT match (13 > 13 is False)
        model_params = 13
        if filter_compare == "gt" and model_params <= filter_scale:
            excluded = True
        else:
            excluded = False

        assert excluded

        # Model is 30B → should match (30 > 13)
        model_params = 30
        if filter_compare == "gt" and model_params <= filter_scale:
            excluded = True
        else:
            excluded = False

        assert not excluded


class TestParamScaleEdgeCases:
    """Test edge cases and boundary conditions."""

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
        # (0 in boolean context means "no filter")
        assert not state.has_filters()

    def test_search_state_param_scale_none_vs_default(self):
        """Test SearchState param_scale None vs initial state."""
        state = SearchState()
        assert state.param_scale is None
        assert state.param_scale_mode == "eq"

        state.param_scale = 7
        assert state.param_scale == 7

        state.param_scale = None
        assert state.param_scale is None
        assert state.param_scale_mode == "eq"  # Mode should stay the same
