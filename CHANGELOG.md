# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.7] - 2025-12-04

### Fixed
- `load_config_for_model` RepositoryNotFoundError 対応：HuggingFace に存在しないモデル指定時にローカルキャッシュにフォールバック（404 エラー回避）

### Added
- **Readline サポート**：全インタラクティブメニュー（search, alias, remove, settings）でコマンド履歴ナビゲーション（上下キー）を有効化
- **未タグ付きモデルフィルタ**：HuggingFace のタスクタグが未設定のモデルを表示するオプション 9 を追加。デフォルト OFF で text-generation のみ検索、toggle で拡張可能

### Changed
- **フィルタメニュー UX 改善**：プリセット操作を数字（10-12）から文字ショートカット（C/S/L/D）に変更
  - C = Clear all filters
  - S = Save preset
  - L = Load preset
  - D = Delete preset

## [0.3.6] - 2025-12-01

### Added
- **Model Precision Filter** (re-designed from v0.3.6 initial version)
  - Support for 8 precision levels: 2-bit, 3-bit, 4-bit, 5-bit, 6-bit, 8-bit, 16-bit, 32-bit
  - Quantization methods: AWQ, GPTQ, GGUF, MLX
  - GGUF variant support: q2_k, q2_m, q3_k_*, q4_k_*, q5_*, q6_k, q8_*
  - Non-quantized models (16/32-bit FP16/BF16) fully supported
  - Precision level is independent filter (specify bit count only to get all methods)
  - Optional method filtering to narrow results further
  - Dynamic menu: available methods change based on selected precision
  - CLI flags: `--precision LEVEL` and optional `--method {awq,gptq,gguf,mlx}`
  - Tag-based fallback detection for better precision inference

- **Session-based memory caching**
  - Cache precision filter results within a session
  - Reduces API calls when revisiting same precision level
  - Cache cleared between sessions

- **API search limit configuration**
  - New CLI flag: `--hf-limit N` to specify HuggingFace API result count
  - Interactive menu option: C to change API search limit
  - Slash commands: `/change N`, `/c N` for quick configuration
  - Default: 500 (no tags), 100 (with tags)

- **AND/OR/Exclude search syntax**
  - AND search: `llama+mistral` or `llama,instruct` (both keywords required)
  - OR search: `llama mistral` (space-separated, default behavior)
  - Exclude search: `!qwen` or `-gpt` (prefix notation)
  - Combined queries: `llama+mistral !qwen` (AND both, exclude qwen)
  - Exclude-only queries: `/s !qwen` shows all models except qwen
  - zsh compatibility: automatic conversion of `\!` to `!` for history expansion

### Changed
- **SearchState extended** with new attributes:
  - `precision_level`: Optional[int] for precision filtering
  - `precision_method`: Optional[str] for method filtering
  - `search_type`: "and" or "or" for AND/OR search mode
  - `search_keywords`: list[str] for parsed keywords
  - `exclude_keywords`: list[str] for exclusion keywords
  - `search_cache`: dict for session-based caching
  - `hf_search_limit`: Optional[int] for API result count limit

- **Interactive menu updated**
  - New advanced search syntax hints shown in main menu
  - Examples for AND/OR/exclude queries
  - Comma (,) confirmed as working AND delimiter alongside plus (+)

### Technical
- Comprehensive test suite: 323 tests PASS (37 new tests for v0.3.6)
- New functions:
  - `parse_search_query()`: Parse AND/OR/exclude syntax from user input
  - `extract_precision_info()`: Extract precision level and method from model ID
  - `handle_precision_filter()`: Interactive UI for precision filter selection
  - `do_precision_search()`: Search with precision filter and supplementary search for empty queries

- Supplementary search logic: When initial API results < 20 and precision_level specified, searches all relevant keywords for that precision to ensure comprehensive results

### Fixed
- Precision filter now works as independent filter (not AND condition)
- Non-quantized models (16/32-bit) now properly detected and included
- Empty query + precision filter now returns full results via supplementary search

## [0.3.5] - 2025-11-25

### Added
- **Parameter scale range filter** for `mlxlm search`
  - New `--param-scale-mode {eq,lt,gt,range}` flag to specify filtering mode
  - New `--param-scale-min N` and `--param-scale-max N` flags for range mode
  - Interactive filter menu: Mode 4 for range (min-max, both inclusive)
  - Support for partial ranges (only min or only max specified)

### Changed
- **Parameter scale filter refactored** (internal API change)
  - Renamed `param_compare` → `param_scale_mode` for clarity
  - Added `param_scale_min` and `param_scale_max` fields to SearchState
  - Filter now supports 4 modes: eq (=), lt (<), gt (≥), range (min-max)
  - Preset name generation updated (compatible with v0.3.5 format)
  - JSON output updated with new field names

### Technical
- Comprehensive test suite (test_search_v035a_param_range.py) with 30 tests
- Tests cover: range filtering, boundary conditions, edge cases (zero, large values)
- Range comparison logic: `min ≤ param ≤ max` (both bounds inclusive)
- Backward compatible with single-value filtering (eq/lt/gt modes)
- All 239 tests PASS

### Fixed
- **SearchState.has_filters()** now correctly detects range filters
- **get_filter_summary()** properly formats single and range parameters
- UI correctly swaps min/max if entered in wrong order

## [0.3.5] - 2025-11-25

### Added
- **Parameter scale filter** for `mlxlm search`
  - New `--param-scale N` flag to filter models by parameter size (7, 13, 30, etc.)
  - New `--param-compare {eq,lt,gt}` flag for comparison operators
    - `eq`: Exact match (e.g., 7B only)
    - `lt`: Less than (e.g., 13B or smaller)
    - `gt`: Greater than or equal (e.g., 30B or larger)
  - Interactive menu option (6) for parameter scale filtering
  - Automatic extraction from model names (7B, 7-B, 7_B, 7 B, 7 billion formats)
  - Fallback to model card data when name parsing fails

### Changed
- Filter menu reorganized: options 1-11 (presets now 9-11 for consistency)
- SearchState extended with `param_scale` (Optional[int]) and `param_compare` (str) fields
- `has_filters()` and `get_filter_summary()` updated to include parameter scale info
- JSON output now includes param_scale and param_compare in filters section

### Technical
- Added `extract_param_scale()` function to parse parameter sizes from model names
- Added `handle_param_scale_filter()` for interactive filter input
- Comprehensive test suite (test_search_v035_param_scale.py) with 24 tests covering:
  - Name format variations (case-insensitive, hyphen, underscore, space separators)
  - Comparison operators (eq, lt, gt filtering logic)
  - Edge cases (zero values, large values, None handling)
  - Integration with SearchState and JSON output

## [0.3.0] - 2025-11-24

### Added
- **New `mlxlm search` command** for searching HuggingFace models
  - Interactive menu-driven search with pagination
  - Color-coded results (Green=MLX, Yellow=Quantized, Blue=Official)
  - Rich metadata display (size, downloads, last updated)
  - Filter by tags, size, downloads, recency
  - Sort by downloads, updated date, or size
  - JSON output mode (`--json`) for AI agents and scripts
  - Non-interactive text mode (`--no-interactive`)
  - Two-tier help system (`--help` and `--help-detail`)
  - Stateful filter management (multiple conditions retained)
  - Menu navigation: 1-7 for model selection, 8 for next page, 9 for filters, 0 for exit

- **Search filters** (all combinable):
  - `--filter-tag TAG`: Filter by tag (repeatable for multiple tags)
  - `--max-size GB`: Maximum model size in gigabytes
  - `--min-downloads N`: Minimum download count threshold
  - `--updated-within DAYS`: Models updated within X days
  - `--sort {downloads,updated,size}`: Sort order (default: downloads)
  - `--limit N`: Results per page (default: 7)

- **Display improvements**:
  - ANSI color coding for model types
  - Human-readable timestamps ("2 days ago", "Yesterday")
  - Formatted download counts (1.2M, 153.4k)
  - 2-line display for long model names (>50 chars) to prevent column misalignment

- **AI-friendly features**:
  - `--help-detail` flag for comprehensive documentation
  - JSON output with structured results
  - All features accessible via CLI flags (no interactive-only features)

### Fixed
- **search**: Sort parameter now correctly maps internal "updated" to HF API "lastModified"
- **search**: Added `expand` parameter to fetch size and updated metadata from HF API
- **search**: Long model names no longer cause column misalignment (2-line display)
- **search**: `--json` flag now takes priority over `--no-interactive` when both are specified
- **search**: Pagination logic fixed to correctly display last page when total results not divisible by page size

### Changed
- **search help**: Simplified `--help` output with Quick Start examples
- **search help**: Added `--help-detail` for comprehensive documentation with 8 usage examples

### Technical Notes
- Uses `huggingface_hub` library for HF API integration
- Client-side sorting for size (HF API doesn't support size sorting)
- UTC timezone handling for date comparisons
- Searches limited to `text-generation` task models
- Expandable fields requested: `lastModified`, `safetensors`

---

**Files modified:**
- Added: `commands/search.py` (930 lines)
- Modified: `commands/__init__.py`
- Modified: `cli_flags.py`
- Modified: `mlxlm.py`

## [0.2.6] - 2025-11-15

### Added
- **Interactive commands** for enhanced user experience in `mlxlm run`
  - `/quit`: Exit command (alias for /exit and /bye)
  - `/help`: Display all available commands and keyboard shortcuts (now with system color)
  - `/clear`: Improved with 3 flexible options:
    - Clear conversation only (keep screen)
    - Clear screen only (keep conversation history)
    - Clear both
    - Cancel (default)
  - `/status`: Show detailed session status including:
    - Model name and chat mode
    - Conversation statistics (user/assistant message counts)
    - Token usage with percentage
    - Current settings (stream mode, time limit)
    - Now displayed in system color for better visibility
  - `/export [filename]`: Export conversation to file
    - Supports 3 formats: md (Markdown), txt (Plain Text), json (JSON)
    - Auto-detects format from file extension
    - Default filename with timestamp if not specified
    - Pretty formatting with "### User:" and "### AI:" sections
  - `/setting`: Interactive settings menu with 4 categories:
    - Default Behavior Settings (max tokens, stream mode, chat mode, history mode, time limit, reasoning level)
    - **Color Settings** (fully implemented):
      - 5 preset themes: Default, Nord, Dracula, Monokai, Solarized
      - Custom theme creation with live color previews
      - Support for 16-color codes (30-37, 90-97) with reference table
      - 16-color reference table displayed when customizing colors (2-column layout with color previews)
      - Support for RGB hex (#RRGGBB) and comma-separated (R,G,B)
      - Real-time color preview for each element
      - Save custom themes to config
    - User Prompt History (max entries, max age in days)
    - Export Settings (default format, timestamp inclusion, auto-save on exit)

- **Color customization infrastructure**
  - Added 'system' color for command outputs (bright gray)
  - 5 built-in color themes with carefully selected palettes
  - `parse_color_input()`: Flexible color input parser supporting multiple formats
  - `edit_custom_colors()`: Interactive custom theme editor with live preview
  - Theme changes apply immediately and persist in config

- **Configuration infrastructure** in `core.py`
  - `get_default_config()`: Returns default configuration dictionary
  - `load_user_config()`: Load and merge user config from `mlxlm_data/config.json`
  - `save_user_config()`: Save configuration to disk
  - `merge_configs()`: Recursive configuration merging
  - Settings stored in `mlxlm_data/config.json` with defaults, colors, history, and export preferences

### Changed
- Startup message updated to mention `/help` for command list
- Command completer and auto-suggest now include all new slash commands
- All configuration values now customizable through `/setting` menu
- **Color themes now apply to actual conversation content**, not just prompt labels:
  - User input content displays in `user_prompt` color
  - AI output content displays in `model_output` color (all stream modes)
  - Previously only the "📝 Prompt:" label was colored

### Fixed
- Input validation for all settings with helpful error messages
- Safe Ctrl+C / Ctrl+D handling in all interactive menus
- Duplicate `os` import that caused `UnboundLocalError` at startup
- Color application now works correctly for all conversation content

## [0.2.5] - 2025-11-15

### Added
- **prompt-toolkit integration** for enhanced input experience in `mlxlm run`
  - Persistent input history across sessions (saved to `mlxlm_data/input_history`)
  - Multiline input support with Option+Enter (Mac) / Alt+Enter (Linux), or Ctrl+J
  - Command completion for `/exit` and `/bye` (shows only when typing `/` and pressing Tab)
  - **Inline auto-suggestions** with gray text for slash commands (Claude Code style)
    - Type `/e` to see `xit` in gray, accept with right arrow or Ctrl+E
    - Improves discoverability without requiring Tab press
  - Colorful ANSI terminal output (user prompts, model responses, errors, warnings)
  - Keyboard shortcuts for history navigation (Ctrl+P for previous, Ctrl+N for next)
  - Additional cursor movement shortcuts (Ctrl+R for line start, Ctrl+O for line end)
  - **Ctrl+C support during model generation** to interrupt output and return to prompt
  - Graceful fallback to basic input() when prompt-toolkit is unavailable
  - Ctrl+D exit support

### Changed
- `requirements.txt`: Added `prompt_toolkit>=3.0.43` dependency
- `.gitignore`: Added `mlxlm_data/` to exclude user data from git tracking

### Fixed
- Auto-completion popup appearing for non-slash commands
  - Implemented custom `SlashCommandCompleter` to only show completions when input starts with `/`
  - Disabled automatic completion popup (now only shows on Tab press)
- Multiple keybinding refinements to avoid system conflicts
  - Removed Option/Alt + Up/Down (conflicted with macOS system shortcuts)
  - Changed from invalid `c-,`/`c-.` to valid `c-]`/`c-\\`
  - Final keybindings: `c-r` (line start) and `c-o` (line end) for better ergonomics
- Invalid keybinding syntax in prompt-toolkit
  - Fixed: Changed from `s-enter` to `escape, enter` for Option/Alt+Enter
  - Properly enabled default Emacs history navigation (Ctrl+P/Ctrl+N)

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
