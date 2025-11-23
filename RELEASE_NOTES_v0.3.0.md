# 🔍 MLX-LM v0.3.0 - HuggingFace Search Feature

**Release Date:** 2025-11-23

## 🎉 What's New

v0.3.0 introduces the **`mlxlm search`** command - a powerful, interactive HuggingFace model search tool designed for both humans and AI agents.

### ✨ Key Features

🔎 **Interactive Model Search**
- Search HuggingFace's text-generation models directly from your terminal
- Beautiful color-coded results (MLX-compatible, quantized, official models)
- Pagination with intuitive menu navigation (1-7: select, 8: next, 9: filters, 0: exit)

🎛️ **Powerful Filtering System**
- Filter by tags (mlx, gguf, quantized, 4-bit, 8-bit, etc.)
- Size constraints (max GB)
- Download thresholds (minimum downloads)
- Recency filters (updated within X days)
- Multiple sort options (downloads, updated, size)

🤖 **AI-Friendly Design**
- JSON output mode for AI agents and scripts (`--json`)
- Non-interactive text mode (`--no-interactive`)
- Comprehensive help system (`--help` and `--help-detail`)
- All options accessible via CLI flags

📊 **Rich Metadata Display**
- Model size (with N/A fallback for missing data)
- Download counts (formatted: 1.2M, 153.4k, etc.)
- Last updated timestamps (human-readable: "2 days ago", "Yesterday")
- Long model names automatically use 2-line display to prevent column misalignment

---

## 📋 Usage Examples

### Basic Interactive Search
```bash
mlxlm search llama
```

### Filter MLX-Compatible Models
```bash
mlxlm search mistral --filter-tag mlx
```

### Find Small, Popular Models
```bash
mlxlm search phi --max-size 5 --min-downloads 1000
```

### Recently Updated Quantized Models
```bash
mlxlm search qwen --filter-tag quantized --updated-within 30
```

### JSON Output for AI/Scripts
```bash
mlxlm search gemma --json
```

### Get Detailed Help
```bash
mlxlm search llama --help-detail
```

---

## 🐛 Bug Fixes

- **Display alignment**: Long model names (>50 chars) now use 2-line display to maintain column alignment
- **Sort parameter mapping**: Fixed "Invalid sort parameter" error when sorting by "updated" (now correctly maps to HF API's `lastModified`)
- **Missing metadata**: Added `expand` parameter to HF API requests to fetch size and updated timestamps
- **Flag priority**: `--json` now correctly takes priority over `--no-interactive` when both are specified

---

## 🔧 Technical Details

### Color Coding Legend
- 🟢 **Green**: MLX-compatible models (`mlx`, `mlx-community` tags)
- 🟡 **Yellow**: Quantized models (`gguf`, `quantized`, `4-bit`, `8-bit` tags)
- 🔵 **Blue**: Official models (`meta-llama`, `mistralai`, `google`, `microsoft`, `Qwen` tags)
- ⚪ **White**: Other models

### Output Modes
1. **Interactive** (default): Menu-driven with pagination
2. **JSON** (`--json`): Structured output for AI/scripts
3. **Non-interactive** (`--no-interactive`): Plain text list

### API Integration
- Uses HuggingFace Hub API (`huggingface_hub` library)
- Requests expandable fields (`lastModified`, `safetensors`)
- Client-side sorting for size (HF API doesn't support it)
- Filters limited to `text-generation` task models

---

## 📦 Installation

No changes to installation process. If you're upgrading from v0.2.x:

```bash
cd ~/mlxlm
git pull origin main
```

Ensure you have `huggingface_hub` installed:
```bash
pip install huggingface_hub
```

---

## 🙏 Credits

This release represents a collaboration between:
- **Claude Cloud** (Planning, implementation, code review)
- **Claude Code Local** (Testing, GitHub integration, release management)
- **Previous contributors**: GPT-4, Codex (v0.1.x - v0.2.x foundations)

Special thanks to the user for driving the vision and providing invaluable testing feedback! 🎯

---

## 📚 Documentation

- Full command reference: `mlxlm search --help-detail`
- Updated USAGE.md with search examples
- CHANGELOG.md updated with all v0.3.0 changes

---

## 🔜 What's Next?

v0.3.0 focuses exclusively on search functionality. Future features (registry sync, WebUI) remain under consideration but are not part of this release.

Enjoy searching! 🚀
