"""
Pytest configuration and fixtures for mlxlm tests

This file automatically mocks MLX-specific dependencies that are not available
in the test environment (Linux sandbox without Apple Silicon).
"""

import sys
from unittest.mock import MagicMock


# ===== Mock MLX dependencies =====

def pytest_configure(config):
    """
    Configure pytest to mock MLX-specific modules before test collection.

    This allows tests to import modules that depend on mlx_lm and mlx.core
    without actually having these packages installed.
    """
    # Mock mlx_lm module
    mock_mlx_lm = MagicMock()
    mock_mlx_lm.load = MagicMock(return_value=(MagicMock(), MagicMock()))
    mock_mlx_lm.generate = MagicMock(return_value="Generated text")
    mock_mlx_lm.stream_generate = MagicMock(return_value=iter([]))
    sys.modules['mlx_lm'] = mock_mlx_lm

    # Mock mlx.core module (if needed)
    mock_mlx_core = MagicMock()
    sys.modules['mlx'] = MagicMock()
    sys.modules['mlx.core'] = mock_mlx_core


# ===== Shared fixtures =====

# Additional fixtures can be added here for use across all test modules
