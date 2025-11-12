# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-01-12

### Added
- Comprehensive test suite with 49 unit tests
  - `test_core.py`: 22 tests for alias loading, name resolution, rendering, helper utilities
  - `test_commands.py`: 12 tests for model listing, info display, alias management, diagnostics
  - `test_cli.py`: 15 tests for CLI routing, argument parsing, error handling
- Test coverage: 58% overall, 100% for critical components
- pytest configuration and development dependencies (`requirements-dev.txt`)
- MLX mocking support for cross-platform testing (works on Linux)
- **USAGE.md** (759 lines): Comprehensive user guide with:
  - Complete command reference with examples
  - Environment variables documentation
  - Common workflows and use cases
  - Troubleshooting guide
  - Advanced usage patterns
  - Tips and tricks
- **CONTRIBUTING.md**: Developer contribution guidelines
- Module docstrings for all core Python files
- License headers (MIT) in all source files
- `__version__` constant for version tracking
- `HF_CACHE_PATH` constant to reduce code duplication

### Changed
- All code and comments now in English for international collaboration
- Refactored HuggingFace cache path references to use `HF_CACHE_PATH` constant

### Fixed
- `resolve_model_name()` in `core.py` incorrectly handling `models--` format
  - Before: `models--google--gemma-3-27b-it` → Error (invalid conversion)
  - After: `models--google--gemma-3-27b-it` → `google/gemma-3-27b-it` ✅
- Bug affected direct cache key usage; alias-based usage was unaffected

## [0.1.0] - 2025-01-10

### Added
- Initial release of mlxlm CLI tool
- Core commands:
  - `list`: Show list of installed models
  - `show`: Display model information and config
  - `pull`: Download models from HuggingFace Hub
  - `remove`: Delete cached models
  - `run`: Interactive model execution with streaming support
  - `alias`: Model alias management (add/edit/remove)
  - `doctor`: Environment diagnostics
- Harmony chat renderer support for GPT-OSS models
- HuggingFace `chat_template` support
- Plain text fallback rendering
- Conversation history modes
- Streaming output modes (all/final/off)
- Custom system prompts and reasoning levels
- Environment variable configuration
- `.mlxlm_aliases.json` for model aliases
- MIT License
- README.md with feature overview and quick start
- Installation script (`install.sh`)

[0.2.0]: https://github.com/CreamyCappuccino/mlxlm/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/CreamyCappuccino/mlxlm/releases/tag/v0.1.0
