# Changelog Entry for v0.3.0

**Add this section to CHANGELOG.md under a new "## [0.3.0] - 2025-11-23" heading**

---

## [0.3.0] - 2025-11-23

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
- Added: `commands/search.py` (847 lines)
- Modified: `commands/__init__.py`
- Modified: `cli_flags.py`
- Modified: `mlxlm.py`

**Commit summary:**
- 7 commits total
- Initial implementation (Phase 1-7)
- Code review fixes (pagination, timezone)
- Bug fixes (expand parameter, sort mapping)
- UX improvements (2-line display, help detail)
