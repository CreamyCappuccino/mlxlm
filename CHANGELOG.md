# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.5] - 2025-11-14

### Added
- **prompt-toolkit integration** for enhanced input experience in `mlxlm run`
  - Persistent input history across sessions (saved to `mlxlm_data/input_history`)
  - Multiline input support with Option+Enter (Mac) / Alt+Enter (Linux), or Ctrl+J
  - Command completion for `/exit` and `/bye` (shows only when typing `/` and pressing Tab)
  - Colorful ANSI terminal output (user prompts, model responses, errors, warnings)
  - Keyboard shortcuts for history navigation (Option/Alt + Up/Down)
  - Graceful fallback to basic input() when prompt-toolkit is unavailable
  - Ctrl+C cancellation and Ctrl+D exit support

### Changed
- `requirements.txt`: Added `prompt_toolkit>=3.0.43` dependency
- `.gitignore`: Added `mlxlm_data/` to exclude user data from git tracking

### Fixed
- Auto-completion popup appearing for non-slash commands
  - Implemented custom `SlashCommandCompleter` to only show completions when input starts with `/`
  - Disabled automatic completion popup (now only shows on Tab press)
- Invalid keybinding syntax in prompt-toolkit
  - Fixed: Changed from `s-enter` to `escape, enter` for Option/Alt+Enter
  - Fixed: Changed from `c-up/c-down` to `escape, up/down` for Option/Alt+Arrow keys

## [0.2.3] - 2025-11-14

### Changed
- **Major refactoring**: Split 727-line `commands.py` into modular structure
  - Created `commands/` directory with 8 modules:
    - `list.py`: Model listing functionality
    - `show.py`: Model information display
    - `pull.py`: Model downloading from HuggingFace
    - `remove.py`: Model removal operations
    - `doctor.py`: Environment diagnostics
    - `run.py`: Interactive model execution
    - `alias.py`: Alias management commands
    - `__init__.py`: Package exports for backward compatibility
  - Total: 821 lines (+94 from headers/docstrings)
  - All 10 functions preserved with identical functionality

### Fixed
- Test suite compatibility with modular structure
  - Updated `test_commands.py` mock paths from `core.XXX` to `commands.<module>.XXX`
  - All 12 tests passing (100% success rate)

## [0.2.2] - 2025-11-13

### Fixed
- CLI help option handling: `-h` and `--help` now properly display help message
  - Bug: SystemExit exception was incorrectly caught for all cases, including help display
  - Fix: Now distinguishes between help output (exit code 0) and actual errors
  - Behavior: `mlxlm -h`, `mlxlm --help`, and `mlxlm help` all work correctly

## [0.2.1] - 2025-11-13

### Added
- Type hint completion: 100% coverage across all modules (mlxlm.py, cli_flags.py, core.py, commands.py)
- 28 new docstrings for functions in core.py and commands.py (achieving 100% documentation)
- Specific exception handling with proper exception types instead of generic `except Exception`

### Changed
- Improved exception handling in: load_alias_dict(), load_config_for_model(), _get_model_type(), pull_model(), and file operations
- Enhanced error messages and debug tracebacks for better troubleshooting

### Removed
- 3 unused imports: pathlib.Path, core.resolve_model_name, core.repo_to_cache_name

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
