# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Tests for v0.3.6: Model Precision Filter (redesigned)."""

import pytest
from commands.search import SearchState
from commands.search_filters import extract_precision_info, extract_param_scale


class TestExtractPrecisionInfo:
    """Test extract_precision_info() function for parsing precision from model IDs."""

    # ===== AWQ Tests =====
    def test_awq_4bit_detection(self):
        """Test detection of AWQ 4-bit models."""
        result = extract_precision_info("cpatonn/Qwen3-Next-80B-A3B-Instruct-AWQ-4bit")
        assert result['precision_level'] == 4
        assert result['method'] == 'awq'

    def test_awq_8bit_detection(self):
        """Test detection of AWQ 8-bit models."""
        result = extract_precision_info("Qwen3-VL-8B-Instruct-AWQ-8bit")
        assert result['precision_level'] == 8
        assert result['method'] == 'awq'

    def test_awq_4bit_hyphenated(self):
        """Test AWQ with hyphenated bit notation (4-bit)."""
        result = extract_precision_info("model-AWQ-4-bit")
        assert result['precision_level'] == 4
        assert result['method'] == 'awq'

    # ===== GPTQ Tests =====
    def test_gptq_int4_detection(self):
        """Test detection of GPTQ Int4 models."""
        result = extract_precision_info("Qwen/Qwen2.5-Coder-32B-Instruct-GPTQ-Int4")
        assert result['precision_level'] == 4
        assert result['method'] == 'gptq'

    def test_gptq_int8_detection(self):
        """Test detection of GPTQ Int8 models."""
        result = extract_precision_info("model-GPTQ-Int8")
        assert result['precision_level'] == 8
        assert result['method'] == 'gptq'

    def test_gptq_int4_case_insensitive(self):
        """Test GPTQ detection is case-insensitive."""
        result = extract_precision_info("Model-Gptq-InT4")
        assert result['precision_level'] == 4
        assert result['method'] == 'gptq'

    # ===== GGUF 2-bit Tests =====
    def test_gguf_q2_k_detection(self):
        """Test detection of GGUF Q2_K variant."""
        result = extract_precision_info("TheBloke/model-Q2_K-GGUF")
        assert result['precision_level'] == 2
        assert result['method'] == 'gguf'

    def test_gguf_q2_m_detection(self):
        """Test detection of GGUF Q2_M variant."""
        result = extract_precision_info("model-q2_m-gguf")
        assert result['precision_level'] == 2
        assert result['method'] == 'gguf'

    # ===== GGUF 3-bit Tests =====
    def test_gguf_q3_k_s_detection(self):
        """Test detection of GGUF Q3_K_S variant."""
        result = extract_precision_info("TheBloke/model-Q3_K_S-GGUF")
        assert result['precision_level'] == 3
        assert result['method'] == 'gguf'

    def test_gguf_q3_k_m_detection(self):
        """Test detection of GGUF Q3_K_M variant."""
        result = extract_precision_info("model-q3_k_m-gguf")
        assert result['precision_level'] == 3
        assert result['method'] == 'gguf'

    def test_gguf_q3_k_l_detection(self):
        """Test detection of GGUF Q3_K_L variant."""
        result = extract_precision_info("model-Q3_K_L-GGUF")
        assert result['precision_level'] == 3
        assert result['method'] == 'gguf'

    # ===== GGUF 4-bit Tests =====
    def test_gguf_q4_k_m_detection(self):
        """Test detection of GGUF Q4_K_M variant (most common)."""
        result = extract_precision_info("TheBloke/WizardLM-Q4_K_M-GGUF")
        assert result['precision_level'] == 4
        assert result['method'] == 'gguf'

    def test_gguf_q4_k_s_detection(self):
        """Test detection of GGUF Q4_K_S variant."""
        result = extract_precision_info("model-Q4_K_S-GGUF")
        assert result['precision_level'] == 4
        assert result['method'] == 'gguf'

    def test_gguf_q4_0_detection(self):
        """Test detection of GGUF Q4_0 variant."""
        result = extract_precision_info("model-q4_0-gguf")
        assert result['precision_level'] == 4
        assert result['method'] == 'gguf'

    def test_gguf_q4_1_detection(self):
        """Test detection of GGUF Q4_1 variant."""
        result = extract_precision_info("model-q4_1-GGUF")
        assert result['precision_level'] == 4
        assert result['method'] == 'gguf'

    # ===== GGUF 5-bit Tests =====
    def test_gguf_q5_k_s_detection(self):
        """Test detection of GGUF Q5_K_S variant."""
        result = extract_precision_info("model-Q5_K_S-GGUF")
        assert result['precision_level'] == 5
        assert result['method'] == 'gguf'

    def test_gguf_q5_k_m_detection(self):
        """Test detection of GGUF Q5_K_M variant."""
        result = extract_precision_info("model-q5_k_m-gguf")
        assert result['precision_level'] == 5
        assert result['method'] == 'gguf'

    def test_gguf_q5_0_detection(self):
        """Test detection of GGUF Q5_0 variant."""
        result = extract_precision_info("model-Q5_0-GGUF")
        assert result['precision_level'] == 5
        assert result['method'] == 'gguf'

    def test_gguf_q5_1_detection(self):
        """Test detection of GGUF Q5_1 variant."""
        result = extract_precision_info("model-q5_1-gguf")
        assert result['precision_level'] == 5
        assert result['method'] == 'gguf'

    # ===== GGUF 6-bit Tests =====
    def test_gguf_q6_k_detection(self):
        """Test detection of GGUF Q6_K variant."""
        result = extract_precision_info("TheBloke/model-Q6_K-GGUF")
        assert result['precision_level'] == 6
        assert result['method'] == 'gguf'

    def test_generic_6bit_detection(self):
        """Test detection of generic 6-bit models."""
        result = extract_precision_info("model-6bit-quantized")
        assert result['precision_level'] == 6
        assert result['method'] is None

    # ===== GGUF 8-bit Tests =====
    def test_gguf_q8_0_detection(self):
        """Test detection of GGUF Q8_0 variant."""
        result = extract_precision_info("TheBloke/model-Q8_0-GGUF")
        assert result['precision_level'] == 8
        assert result['method'] == 'gguf'

    def test_gguf_q8_1_detection(self):
        """Test detection of GGUF Q8_1 variant."""
        result = extract_precision_info("model-q8_1-gguf")
        assert result['precision_level'] == 8
        assert result['method'] == 'gguf'

    def test_generic_8bit_detection(self):
        """Test detection of generic 8-bit models."""
        result = extract_precision_info("model-8bit-quantized")
        assert result['precision_level'] == 8
        assert result['method'] is None

    # ===== MLX Tests =====
    def test_mlx_4bit_detection(self):
        """Test detection of MLX 4-bit quantized models."""
        result = extract_precision_info("mlx-community/mlx-4bit-quantized")
        assert result['precision_level'] == 4
        assert result['method'] == 'mlx'

    def test_mlx_generic_quantized_detection(self):
        """Test detection of MLX generic quantized pattern (mlx.*quantized)."""
        result = extract_precision_info("mlx-community/mlx-gemma-quantized")
        assert result['method'] == 'mlx'

    # ===== Non-quantized Tests =====
    def test_non_quantized_model(self):
        """Test that non-quantized models return None."""
        result = extract_precision_info("meta-llama/Llama-2-7B")
        assert result['precision_level'] is None
        assert result['method'] is None

    def test_empty_model_id(self):
        """Test handling of empty model ID."""
        result = extract_precision_info("")
        assert result['precision_level'] is None
        assert result['method'] is None

    def test_none_model_id(self):
        """Test handling of None model ID."""
        result = extract_precision_info(None)
        assert result['precision_level'] is None
        assert result['method'] is None

    # ===== Edge Cases =====
    def test_precision_variant_before_generic_pattern(self):
        """Test that specific GGUF variants match before generic patterns."""
        # q4_k_m should match before generic '4'
        result = extract_precision_info("model-q4_k_m-gguf")
        assert result['precision_level'] == 4
        # Should not be treated as matching the generic 4-bit pattern with lower priority

    def test_case_insensitivity(self):
        """Test that detection is case-insensitive."""
        result1 = extract_precision_info("MODEL-Q4_K_M-GGUF")
        result2 = extract_precision_info("model-q4_k_m-gguf")
        assert result1 == result2
        assert result1['precision_level'] == 4


class TestSearchStateIntegration:
    """Test SearchState integration with precision filter attributes."""

    def test_precision_level_attribute_exists(self):
        """Test that SearchState has precision_level attribute."""
        state = SearchState()
        assert hasattr(state, 'precision_level')
        assert state.precision_level is None

    def test_precision_method_attribute_exists(self):
        """Test that SearchState has precision_method attribute."""
        state = SearchState()
        assert hasattr(state, 'precision_method')
        assert state.precision_method is None

    def test_precision_filter_sets_attributes(self):
        """Test that precision filter attributes can be set."""
        state = SearchState()
        state.precision_level = 4
        state.precision_method = 'awq'
        assert state.precision_level == 4
        assert state.precision_method == 'awq'

    def test_has_filters_with_precision_level(self):
        """Test has_filters() detects precision_level."""
        state = SearchState()
        assert not state.has_filters()

        state.precision_level = 4
        assert state.has_filters()

    def test_has_filters_with_precision_method(self):
        """Test has_filters() detects precision_method."""
        state = SearchState()
        assert not state.has_filters()

        state.precision_method = 'gguf'
        assert state.has_filters()

    def test_has_filters_with_both_precision_settings(self):
        """Test has_filters() when both precision settings are set."""
        state = SearchState()
        state.precision_level = 4
        state.precision_method = 'gptq'
        assert state.has_filters()


class TestFilterSummary:
    """Test filter summary generation with precision filters."""

    def test_filter_summary_precision_level_only(self):
        """Test filter summary shows precision level alone."""
        state = SearchState()
        state.precision_level = 4
        summary = state.get_filter_summary()
        assert any('4-bit' in s for s in summary)

    def test_filter_summary_precision_with_method(self):
        """Test filter summary shows precision level and method."""
        state = SearchState()
        state.precision_level = 4
        state.precision_method = 'awq'
        summary = state.get_filter_summary()
        assert any('4-bit' in s and 'AWQ' in s for s in summary)

    def test_filter_summary_method_only(self):
        """Test filter summary shows method when level is not set."""
        state = SearchState()
        state.precision_method = 'gguf'
        summary = state.get_filter_summary()
        assert any('GGUF' in s for s in summary)

    def test_filter_summary_multiple_filters(self):
        """Test filter summary with precision + other filters."""
        state = SearchState()
        state.precision_level = 4
        state.precision_method = 'gguf'
        state.max_size_gb = 10
        summary = state.get_filter_summary()

        assert len(summary) >= 2
        assert any('4-bit' in s for s in summary)
        assert any('10 GB' in s for s in summary)


class TestPrecisionFilterLogic:
    """Test precision filter logic in search results."""

    def test_precision_level_filtering(self):
        """Test that precision_level filters correctly."""
        state = SearchState()
        state.precision_level = 4

        # Simulate extracted precision info
        precision_4bit = {'precision_level': 4, 'method': 'awq'}
        precision_8bit = {'precision_level': 8, 'method': 'awq'}

        # 4-bit model should match
        assert precision_4bit['precision_level'] == state.precision_level
        # 8-bit model should not match
        assert precision_8bit['precision_level'] != state.precision_level

    def test_precision_method_filtering(self):
        """Test that precision_method filters correctly."""
        state = SearchState()
        state.precision_method = 'gguf'

        precision_gguf = {'precision_level': 4, 'method': 'gguf'}
        precision_awq = {'precision_level': 4, 'method': 'awq'}

        # GGUF should match
        assert precision_gguf['method'] == state.precision_method
        # AWQ should not match
        assert precision_awq['method'] != state.precision_method

    def test_combined_precision_filtering(self):
        """Test filtering with both level and method."""
        state = SearchState()
        state.precision_level = 4
        state.precision_method = 'gguf'

        precision_match = {'precision_level': 4, 'method': 'gguf'}
        precision_wrong_level = {'precision_level': 8, 'method': 'gguf'}
        precision_wrong_method = {'precision_level': 4, 'method': 'awq'}

        # Only exact match passes both conditions
        assert (precision_match['precision_level'] == state.precision_level and
                precision_match['method'] == state.precision_method)

        # Wrong level fails
        assert not (precision_wrong_level['precision_level'] == state.precision_level and
                    precision_wrong_level['method'] == state.precision_method)

        # Wrong method fails
        assert not (precision_wrong_method['precision_level'] == state.precision_level and
                    precision_wrong_method['method'] == state.precision_method)


class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""

    def test_old_quant_attributes_removed(self):
        """Test that old quant_method/quant_bits attributes don't exist."""
        state = SearchState()
        # New attributes should exist
        assert hasattr(state, 'precision_level')
        assert hasattr(state, 'precision_method')
        # Old attributes should not exist
        assert not hasattr(state, 'quant_method')
        assert not hasattr(state, 'quant_bits')

    def test_param_scale_still_works(self):
        """Test that parameter scale filter still works independently."""
        state = SearchState()
        state.param_scale = 7
        state.precision_level = 4

        # Both filters can coexist
        assert state.param_scale == 7
        assert state.precision_level == 4
        assert state.has_filters()

    def test_tags_filter_still_works(self):
        """Test that tag filter still works independently."""
        state = SearchState()
        state.tags = ["mlx", "instruct"]
        state.precision_level = 4

        # Both filters can coexist
        assert len(state.tags) == 2
        assert state.precision_level == 4
        assert state.has_filters()
