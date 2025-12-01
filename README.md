# 🧠 MLX-LM CLI Tool

**mlxlm is an Ollama-inspired CLI tool that complements Ollama by focusing on model discovery, exploration, and MLX-optimized experimentation on Apple Silicon.**

While [MLX LM](https://github.com/ml-explore/mlx-lm) focuses on the model execution framework, mlxlm adds a complete user-facing layer: **powerful HuggingFace model search, precision filtering, interactive menus, session management, multiple chat renderers, and more.**

## Why mlxlm?

**vs. mlx-lm (official):**
- mlx-lm provides Python APIs and minimal CLI → mlxlm adds rich CLI + interactive UI
- mlx-lm has no model search → mlxlm searches HuggingFace with advanced filters
- mlx-lm requires manual model management → mlxlm provides aliases, sessions, and presets

**vs. Ollama (Different purposes, natural partners):**

Ollama excels at integrated model management and inference serving with cross-platform support. mlxlm serves a different purpose: **deep model discovery and MLX-optimized experimentation**.

| Feature | Ollama | mlxlm |
|---------|--------|-------|
| **Model Discovery** | No search | Advanced → Search (AND/OR/exclude, precision filters) |
| **Quantization Support** | Primarily GGUF | All HF formats (GGUF/AWQ/GPTQ/MLX/FP16) |
| **Runtime Type** | Inference server | Lightweight CLI tool |
| **Apple Silicon** | Good (Metal) | Optimized (MLX native) |
| **Use Case** | Production serving | Research & exploration |

**In practice:** Many users run Ollama for production inference while using mlxlm to discover and compare models before pulling. They're complementary tools.

---

## ✨ Features (v0.3.6+)

### 🔍 Powerful Model Search (HuggingFace)
- **Advanced search syntax**: AND (`llama+instruct`), OR (`llama mistral`), exclude (`!qwen`)
- **Precision filter**: 2-bit to 32-bit (supports GGUF/AWQ/GPTQ/MLX quantization methods)
- **Parameter scale filter**: Filter by model size (7B, 13B, 30B, etc.) with comparison operators
- **Rich filtering**: Tags, size, downloads, recency, sorting, pagination
- **Session caching**: Lightning-fast re-queries within same session
- **Configurable API limits**: Control HuggingFace API result count with `--hf-limit`
- **Multiple output modes**: Interactive menu, JSON (for automation/AI agents), or plain text

### 🧭 Dual-Mode UI: CLI Flags + Interactive Menu
- Use CLI flags for automation and scripting
- Use interactive menu for exploration and visual filtering
- Switch seamlessly between both modes
- Slash commands for quick actions (`/search`, `/display`, `/change`)

### 💬 Flexible Chat Interface
- Run MLX-LM models in conversational mode
- **Multiple renderers**: Harmony, HuggingFace chat_template, or plain text
- **Streaming modes**: Real-time output, final-only, or batch
- **Session management**: Resume previous chats, autosave, start fresh with `/new`
- **Custom controls**: System prompts, stop sequences, reasoning hints, token limits

### 🏷️ Smart Model Management
- **Alias system**: Shorten long HuggingFace names (`mlxlm run llama3` instead of full repo ID)
- **Interactive alias menu**: Browse, add, edit, or remove aliases visually
- **Model info**: Inspect configuration, architecture, precision, and metadata
- **Pull & remove**: Download models from HuggingFace or clean up local cache

### 🔧 Developer-Friendly Tools
- **JSON output mode**: Perfect for automation, scripting, and AI agents
- **Environment diagnostics**: `mlxlm doctor` checks MLX runtime, Harmony, HF cache
- **Offline mode**: Work with local cache only (no API calls)
- **Debug output**: Detailed internal state and prompt inspection
- **Custom renderers**: Override default chat rendering behavior

---

## 🎯 Use Cases

### For Ollama users:
- **Model discovery**: Search HuggingFace's vast model collection using AND/OR/exclude syntax
- **Precision comparison**: Filter by quantization method, bit depth, and model size
- **MLX experimentation**: Try Apple Silicon–optimized models before deciding where to deploy
- **Quick evaluation**: Use interactive search to preview models before pulling to Ollama

### For MLX-LM users:
- **Dual-mode workflow**: CLI flags for automation, interactive menus for exploration
- **Session-based search**: Cache results and iterate quickly across multiple searches
- **Model metadata**: Deep dive into configuration, architecture, and precision details
- **Advanced filtering**: Combine AND/OR/exclude searches with precision and parameter filters

### For researchers & developers:
- **Model curation**: Systematically evaluate models by quantization, size, and performance
- **Automated workflows**: JSON output for integration with scripts and AI pipelines
- **Custom chat modes**: Multiple renderers, streaming control, and reasoning hints
- **Reproducible experiments**: Save search presets and model configurations for team collaboration

---

## 🛠️ Installation

### Prerequisites

- 🐍 **Python 3.10+**
- 🍎 **MLX framework** (Apple Silicon required)
- 📚 **mlx-lm library** (and huggingface-hub)

### Quick Start

1. 📥 **Clone the repository:**

```bash
git clone https://github.com/username/mlxlm.git
cd mlxlm
```

2. 📦 **(Optional) Create a virtual environment:**

```bash
conda create -n mlxlm_env python=3.10
conda activate mlxlm_env
```

3. ⬇️ **Install dependencies:**

```bash
pip install mlx-lm huggingface-hub
```

4. 🔗 **Run the install script:**

```bash
chmod +x install.sh
./install.sh
```

This creates a symlink in `/usr/local/bin/mlxlm` so you can use `mlxlm` from anywhere.

5. ✅ **Verify installation:**

```bash
mlxlm list
```

### Manual Setup (Alternative)

If you prefer not to use the install script:

```bash
chmod +x mlxlm.py
sudo ln -s $(pwd)/mlxlm.py /usr/local/bin/mlxlm
```

---

## 🚀 Usage

### 🔍 Search HuggingFace models:

The search feature is the star of v0.3.6 - discover models with powerful filtering and advanced query syntax.

**Basic search:**
```bash
# Interactive search (recommended)
mlxlm search llama

# Non-interactive output
mlxlm search mistral --no-interactive

# JSON output (for automation/AI agents)
mlxlm search qwen --json
```

**Advanced search syntax:**
```bash
# AND search: both keywords required
mlxlm search 'llama+instruct'
mlxlm search 'qwen,mistral'  # comma also works

# OR search: either keyword (default with spaces)
mlxlm search 'llama mistral'

# Exclude: filter out unwanted models
mlxlm search 'llama !qwen'
mlxlm search '!gpt !deepseek'  # exclude-only query

# Combined: AND + exclude
mlxlm search 'llama+instruct !qwen !120B'
```

**Precision filter (v0.3.6):**
```bash
# Get all 4-bit models (any quantization method)
mlxlm search --precision 4

# Get 4-bit GGUF models only
mlxlm search llama --precision 4 --method gguf

# Get non-quantized 16-bit models
mlxlm search mistral --precision 16
```

**Parameter scale filter:**
```bash
# Exact size: 7B models
mlxlm search --param-scale 7

# Range: 7B to 13B
mlxlm search --param-scale-min 7 --param-scale-max 13 --param-scale-mode range

# Less than 13B
mlxlm search --param-scale 13 --param-scale-mode lt
```

**Other filters:**
```bash
# Filter by tags
mlxlm search llama --filter-tag mlx --filter-tag quantized

# Size and download constraints
mlxlm search --max-size 10 --min-downloads 1000

# Recently updated models
mlxlm search --updated-within 30

# Sort options
mlxlm search --sort downloads  # default
mlxlm search --sort updated
mlxlm search --sort size
```

**Interactive menu:**
Once in search results, you can:
- Press 1-10 to view model details
- Press `F` to open filter menu
- Press `N` for next page, `P` for previous
- Use `/s llama+instruct` for quick re-search
- Use `/display 20` to change results per page
- Use `/change 100` to adjust API search limit

### 📋 List all models:

```bash
mlxlm list
```

### ℹ️ Show model info:

```bash
mlxlm show <model-name>
```

### 💬 Launch model in interactive chat mode:

```bash
mlxlm run <model-name>
```

**Options:**
- 🎭 `--chat {auto|harmony|hf|plain}`: Chat rendering mode (default: auto)
  - `auto`: Tries Harmony → HuggingFace template → plain
  - `harmony`: Official Harmony format (requires openai-harmony)
  - `hf`: HuggingFace chat_template
  - `plain`: Simple user/assistant format
- 💾 `--history {on|off}`: Enable/disable conversation history (default: on)
  - `on`: Full conversation context (better for ongoing chats)
  - `off`: Q&A mode (each query independent, lower memory usage)
- 🎤 `--system "text"`: Custom system prompt
- 📝 `--max-tokens N`: Maximum tokens to generate per turn (default: 2048)
- ⚡ `--stream-mode {all|final|off}`: Control streaming output (default: all)
  - `all`: Stream all tokens in real-time
  - `final`: Stream only Harmony final channel (memory-efficient for long outputs)
  - `off`: Wait for complete response before displaying
- 🛑 `--stop "seq"`: Add stop sequences (can be repeated, combined with MLXLM_STOP env var)
- ⏱️ `--time-limit N`: Hard time limit per turn in seconds (0=off) - stops output mid-stream if exceeded
- 🧠 `--reasoning {low|medium|high}`: Reasoning verbosity hint (prepended to system prompt)

**Examples:**
```bash
# 💬 Full conversation with context
mlxlm run gemma3:27b --history on

# ❓ Q&A mode (independent questions)
mlxlm run gemma3:27b --history off

# 🎤 Custom system prompt
mlxlm run gemma3:27b --system "You are a helpful coding assistant"

# 📄 Plain text mode with max tokens limit
mlxlm run gemma3:27b --chat plain --max-tokens 512
```

### 🏷️ Manage model aliases:

#### 🎯 Interactive menu mode (recommended):

```bash
mlxlm alias
```

This launches an interactive menu where you can:
1. **Browse installed models** with their current aliases
2. **Select a model** by entering its number
3. **Add/edit alias** by typing a new name, or **remove** by pressing Enter with no input
4. **Confirm changes** and return to the menu for more operations

**Example flow:**
```
🧠 Installed models:

1. models--google--gemma-3-27b-it  [gemma3]
2. models--meta--llama3-8b  [No alias]
0. Exit

💡 Tip: You can type /exit at any time to cancel the operation.

Enter model number: 1
Enter new alias to add or change, or leave blank to remove:
(Current: 'gemma3')
> gpt
Assign alias 'gpt' to 'models--google--gemma-3-27b-it'? [(y)/n]: y
✅ Alias 'gpt' changed successfully!

🧠 Installed models:
...
```

#### 🔧 CLI alias commands:

```bash
# ➕ Add alias for a model
mlxlm alias add <model-name> <alias>

# ✏️ Edit existing alias
mlxlm alias edit <old-alias> <new-alias>

# ❌ Remove an alias
mlxlm alias remove <alias>
```

### 🩺 Diagnose environment:

```bash
mlxlm doctor
```

✅ Checks MLX runtime, Harmony renderer, HuggingFace cache, and required dependencies.

---

## ⚙️ Environment Variables

mlxlm supports several environment variables for advanced configuration:

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `MLXLM_DEBUG` | Enable debug output (prints internal state, prompt details, etc.) | `0` (off) | `export MLXLM_DEBUG=1` |
| `MLXLM_OFFLINE` | Force offline mode (skip HuggingFace API calls, use local cache only) | `0` (off) | `export MLXLM_OFFLINE=1` |
| `MLXLM_RENDERER` | Custom Harmony renderer module path (format: `module:attribute`) | Auto-detect | `export MLXLM_RENDERER=openai_harmony:render_chat` |
| `MLXLM_REMEMBER_ASSISTANT` | Force conversation history mode (remember assistant responses) | Follows `--history` flag | `export MLXLM_REMEMBER_ASSISTANT=1` |
| `MLXLM_STOP` | Additional stop sequences (comma-separated) | None | `export MLXLM_STOP="STOP,END"` |
| `MLXLM_NO_DEFAULT_STOPS` | Disable default stop sequences for Harmony mode (`<\|end\|>`, `<\|start\|>`) | `0` (off) | `export MLXLM_NO_DEFAULT_STOPS=1` |
| `MLXLM_KV_BYTES` | KV cache dtype size in bytes (1=int8, 2=float16, 4=float32) for memory estimation | `2` (float16) | `export MLXLM_KV_BYTES=4` |

**Example usage:**

```bash
# Enable debug mode to see internal processing
export MLXLM_DEBUG=1
mlxlm run gemma3:27b

# Use offline mode (no HuggingFace API calls)
export MLXLM_OFFLINE=1
mlxlm show gemma3:27b

# Add custom stop sequences (combined with CLI --stop)
export MLXLM_STOP="### END,<|stop|>"
mlxlm run gemma3:27b

# Override Harmony renderer detection
export MLXLM_RENDERER=openai_harmony:render_chat
mlxlm run gemma3:27b --chat harmony

# Force conversation history to always be remembered
export MLXLM_REMEMBER_ASSISTANT=1
mlxlm run gemma3:27b --history off  # History still saved due to env var

# Disable default Harmony stop sequences
export MLXLM_NO_DEFAULT_STOPS=1
mlxlm run gemma3:27b --chat harmony  # Uses only CLI --stop sequences

# Estimate KV cache for float32 dtype instead of default float16
export MLXLM_KV_BYTES=4
mlxlm run gemma3:27b --max-tokens 4096
```

---

## 📁 Folder Structure

```
MLX-LM/
├── mlxlm.py                      # Main CLI entry point
├── cli_flags.py                  # CLI argument parser definitions
├── core.py                       # Utility functions (config, model loading, rendering)
├── commands/                     # Command implementations (v0.2.7+ modular architecture)
│   ├── __init__.py
│   ├── list.py                   # List installed models
│   ├── show.py                   # Show model info
│   ├── pull.py                   # Download models
│   ├── remove.py                 # Remove cached models
│   ├── run.py                    # Interactive chat (v0.2.5-v0.2.8 enhanced)
│   ├── alias.py                  # Alias management
│   ├── doctor.py                 # Environment diagnostics
│   ├── search.py                 # HuggingFace search (v0.3.0+)
│   ├── search_display.py         # Search result rendering
│   ├── search_filters.py         # Filter UI & logic (v0.3.5-v0.3.6)
│   └── search_interactive.py     # Interactive search menu
├── tests/                        # Test suite (323 tests)
├── .mlxlm_aliases.json           # Model alias mappings (auto-generated)
├── mlxlm_config.json             # User settings (auto-generated, v0.3.4+)
├── mlxlm_data/                   # Session history, presets (v0.2.8+, not tracked)
├── CHANGELOG.md                  # Version history
├── README.md                     # This file
└── LICENSE                       # MIT License
```

**Architecture evolution:**
- **v0.1.0**: Monolithic design (mlxlm.py + commands.py + core.py)
- **v0.2.7**: Modularized commands/ directory (12 modules, 62% code reduction)
- **v0.3.0**: Search feature added (4 search-related modules)
- **v0.3.4**: Persistent config & filter presets
- **v0.3.6**: Advanced search filters (precision, param scale, AND/OR/exclude)

---

## 📝 Notes

- **Ollama-complementary**: Designed to work alongside Ollama by adding deep model discovery and MLX-optimized tools
- **Apple Silicon optimized**: Leverages MLX framework for native performance
- **Model agnostic**: Works with any HuggingFace model compatible with MLX-LM
- **Extensible**: Alias system, custom renderers, and flexible chat modes for experimentation

---

## 🤝 Contributing

Feedback and contributions welcome! Found a bug or have an idea? Feel free to open an issue.

---

## 📄 License

MIT License - See LICENSE file for details
