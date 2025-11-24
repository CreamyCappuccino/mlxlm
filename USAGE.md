# 📖 MLX-LM CLI Tool - Usage Guide

Comprehensive guide to using the MLX-LM CLI tool for managing and running language models on Apple Silicon.

---

## 📑 Table of Contents

- [Getting Started](#-getting-started)
- [Commands Reference](#-commands-reference)
  - [mlxlm search](#mlxlm-search)
  - [mlxlm list](#mlxlm-list)
  - [mlxlm show](#mlxlm-show)
  - [mlxlm pull](#mlxlm-pull)
  - [mlxlm remove](#mlxlm-remove)
  - [mlxlm run](#mlxlm-run)
  - [mlxlm alias](#mlxlm-alias)
  - [mlxlm doctor](#mlxlm-doctor)
- [Environment Variables](#-environment-variables)
- [Common Workflows](#-common-workflows)
- [Troubleshooting](#-troubleshooting)
- [Advanced Usage](#-advanced-usage)

---

## 🚀 Getting Started

After installation, verify everything is working:

```bash
mlxlm doctor
```

This checks your MLX runtime, dependencies, and environment setup.

---

## 📋 Commands Reference

### `mlxlm search`

**Purpose:** Search and discover text-generation models on HuggingFace directly from your terminal.

**Usage:**
```bash
mlxlm search <query> [options]
```

**Example:**
```bash
mlxlm search llama
```

This opens an interactive menu showing search results with:
- Model names (color-coded by type)
- Size (in GB)
- Download counts
- Last updated timestamps

#### 🎨 Color Coding

Results are color-coded for quick identification:
- 🟢 **Green**: MLX-compatible models
- 🟡 **Yellow**: Quantized models (GGUF, 4-bit, 8-bit)
- 🔵 **Blue**: Official models (meta-llama, mistralai, google, etc.)
- ⚪ **White**: Other models

#### 🎮 Interactive Menu Navigation

```
1-7  → Select a model to view details
8    → Next page
9    → Open filters menu
0    → Exit search
```

#### 🎛️ Filters & Options

**Filter by Tags:**
```bash
mlxlm search mistral --filter-tag mlx
mlxlm search phi --filter-tag mlx --filter-tag quantized
```

Common tags: `mlx`, `gguf`, `quantized`, `4-bit`, `8-bit`, `f16`, `f32`

**Filter by Size:**
```bash
mlxlm search qwen --max-size 10
```
Shows only models under 10GB.

**Filter by Popularity:**
```bash
mlxlm search gemma --min-downloads 5000
```
Shows only models with at least 5000 downloads.

**Filter by Recency:**
```bash
mlxlm search llama --updated-within 30
```
Shows only models updated in the last 30 days.

**Sort Results:**
```bash
mlxlm search mistral --sort downloads  # Default
mlxlm search llama --sort updated      # Recently updated first
mlxlm search phi --sort size           # Smallest first
```

**Combine Multiple Filters:**
```bash
mlxlm search qwen \
  --filter-tag mlx \
  --max-size 5 \
  --min-downloads 1000 \
  --updated-within 90 \
  --sort updated
```

#### 🤖 AI-Friendly Modes

**JSON Output:**
```bash
mlxlm search llama --json
```

Returns structured JSON with query metadata and results - perfect for AI agents and scripts.

**Non-Interactive Mode:**
```bash
mlxlm search mistral --no-interactive
```

Displays results as plain text without pagination menu. Useful for piping to other commands.

#### 📚 Help & Documentation

**Quick Help:**
```bash
mlxlm search --help
```
Shows concise option summary and Quick Start examples.

**Detailed Help:**
```bash
mlxlm search --help-detail          # Works without query
mlxlm search llama --help-detail    # Or with query
```
Shows comprehensive documentation including all options, 8 practical usage examples, output modes, and technical notes.

#### 💡 Tips & Tricks

Find small MLX models for testing:
```bash
mlxlm search phi --filter-tag mlx --max-size 5 --sort size
```

Discover newly released models:
```bash
mlxlm search qwen --updated-within 7 --sort updated
```

Popular quantized models:
```bash
mlxlm search mistral --filter-tag gguf --min-downloads 10000
```

Export search results for later:
```bash
mlxlm search llama --json > llama_models.json
```

#### 🔗 After Search

After finding a model with `search`, you can:
```bash
mlxlm pull <model-name>   # Download the model
mlxlm show <model-name>   # View model details
mlxlm run <model-name>    # Run the model
```

---

### `mlxlm list`

**Purpose:** Display all installed MLX models with their metadata.

**Usage:**
```bash
mlxlm list [all]
```

**Examples:**
```bash
# List all installed models
mlxlm list

# Show all organizations (if implemented)
mlxlm list all
```

**Output:**
```
🧠 Installed MLX Models:

MODEL NAME                                  ALIAS           SIZE    LAST MODIFIED
models--google--gemma-3-27b-it             gemma3          153G    6 days ago
models--meta--llama3-8b                    llama3          38G     30 days ago
```

**Notes:**
- Shows model size, alias, and last modified date
- Models without aliases show as blank in the ALIAS column
- Sizes are calculated using `du -sh`

---

### `mlxlm show`

**Purpose:** Display detailed information about a specific model.

**Usage:**
```bash
mlxlm show <model-name-or-alias> [--full]
```

**Arguments:**
- `<model-name-or-alias>`: Model identifier (repo ID, cache key, or alias)
- `--full`: Show complete config.json (optional)

**Examples:**
```bash
# Show model info using alias
mlxlm show gemma3

# Show using repo ID
mlxlm show google/gemma-3-27b-it

# Show using cache key format
mlxlm show models--google--gemma-3-27b-it

# Show full configuration
mlxlm show gemma3 --full
```

**Output (standard):**
```
MODEL INFO

Name                   : models--google--gemma-3-27b-it
Size                   : 153G
Alias                  : gemma3

[CONFIG INFO]
Model Architecture     : Gemma3ForConditionalGeneration
Hidden Size            : 5376
Layers                 : 62
Heads                  : 32
Precision              : N/A

[PATH]                 : /Users/you/.cache/huggingface/hub/models--google--gemma-3-27b-it
```

**Notes:**
- Accepts multiple name formats (repo ID, cache key, or alias)
- `--full` flag dumps the entire config.json using pprint
- Config is loaded from HuggingFace API or local cache

---

### `mlxlm pull`

**Purpose:** Download a model from HuggingFace to local cache.

**Usage:**
```bash
mlxlm pull <model-repo-id>
```

**Arguments:**
- `<model-repo-id>`: HuggingFace repository ID (e.g., `google/gemma-3-27b-it`)

**Examples:**
```bash
# Pull a model from HuggingFace
mlxlm pull google/gemma-3-27b-it

# Pull with org and repo format
mlxlm pull meta-llama/Llama-3-8B-Instruct
```

**Notes:**
- Downloads to `~/.cache/huggingface/hub/`
- Requires active internet connection
- Large models may take significant time and disk space
- After pulling, use `mlxlm alias add` to assign a short name

---

### `mlxlm remove`

**Purpose:** Delete cached models and their aliases.

**Usage:**
```bash
mlxlm remove <model-identifiers...> [--yes] [--dry-run]
```

**Arguments:**
- `<model-identifiers...>`: One or more models to remove (repo ID, cache key, or alias)
- `--yes`: Skip confirmation prompt
- `--dry-run`: Show what would be removed without actually deleting

**Examples:**
```bash
# Remove a single model
mlxlm remove gemma3

# Remove multiple models
mlxlm remove gemma3 llama3

# Remove without confirmation
mlxlm remove gemma3 --yes

# Preview removal (safe)
mlxlm remove gemma3 --dry-run
```

**Output:**
```
🗑️  Removal plan:

 - models--google--gemma-3-27b-it -> /path/to/cache [FOUND]

Proceed to delete the FOUND items above? This cannot be undone. [(y)/n]:
```

**Notes:**
- ⚠️ This operation is irreversible
- Removes both the model files and associated alias
- Use `--dry-run` to preview before deleting
- Accepts multiple identifiers at once

---

### `mlxlm run`

**Purpose:** Launch a model in interactive chat mode.

**Usage:**
```bash
mlxlm run <model-name-or-alias> [options]
```

**Arguments:**
- `<model-name-or-alias>`: Model identifier

**Options:**

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `--chat` | `auto`, `harmony`, `hf`, `plain` | `auto` | Chat rendering mode |
| `--history` | `on`, `off` | `on` | Conversation history mode |
| `--system` | `"text"` | Default prompt | Custom system prompt |
| `--max-tokens` | Integer | `2048` | Max tokens per response |
| `--stream-mode` | `all`, `final`, `off` | `all` | Streaming output mode |
| `--stop` | `"sequence"` | None | Stop sequence (repeatable) |
| `--time-limit` | Integer | `0` | Time limit per turn (seconds) |
| `--reasoning` | `low`, `medium`, `high` | None | Reasoning verbosity hint |

**Chat Modes:**
- `auto`: Try Harmony → HuggingFace template → plain (smart default)
- `harmony`: Official Harmony format (requires `openai-harmony` package)
- `hf`: HuggingFace chat_template (if available in tokenizer)
- `plain`: Simple `User: / Assistant:` format

**History Modes:**
- `on`: Full conversation context (multi-turn chat)
- `off`: Q&A mode (each query independent, lower memory)

**Examples:**

```bash
# Basic chat
mlxlm run gemma3

# Q&A mode (no history)
mlxlm run gemma3 --history off

# Custom system prompt
mlxlm run gemma3 --system "You are a helpful coding assistant specializing in Python"

# Force Harmony mode
mlxlm run gemma3 --chat harmony

# Limit response length
mlxlm run gemma3 --max-tokens 512

# Add custom stop sequences
mlxlm run gemma3 --stop "<END>" --stop "##"

# Combine options
mlxlm run gemma3 --chat harmony --history off --max-tokens 1024
```

**Interactive Commands:**
- Type your message and press Enter to chat
- `/exit` or `/bye` to quit
- `Ctrl+D` (EOF) also exits

**Memory Estimation:**
The tool displays estimated KV cache memory usage before each turn:
```
🧮 Context tokens: prompt≈245, new≤2048, total≤2293
🧠 KV cache est.: 1.76 GB (layers=62, hidden=5376, dtype=16-bit)
```

---

### `mlxlm alias`

**Purpose:** Manage short aliases for long model names.

**Usage:**

#### Interactive Mode (Recommended):
```bash
mlxlm alias
```

Launches a menu where you can browse models and add/edit/remove aliases interactively.

#### CLI Mode:
```bash
# Add a new alias
mlxlm alias add <model-name> <alias>

# Edit existing alias
mlxlm alias edit <old-alias> <new-alias>

# Remove an alias
mlxlm alias remove <alias>

# List all aliases
mlxlm alias list
```

**Examples:**

```bash
# Interactive mode
mlxlm alias

# Add alias for a model
mlxlm alias add google/gemma-3-27b-it gemma3

# Change existing alias
mlxlm alias edit gemma3 gpt

# Remove an alias
mlxlm alias remove gemma3

# View all aliases
mlxlm alias list
```

**Interactive Menu Flow:**
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
```

**Notes:**
- Aliases are stored in `.mlxlm_aliases.json`
- Case-insensitive matching
- Empty input in interactive mode removes the alias
- Type `/exit` anytime to cancel

---

### `mlxlm doctor`

**Purpose:** Diagnose environment and dependencies.

**Usage:**
```bash
mlxlm doctor
```

**Checks:**
- ✅ Python version and architecture
- ✅ MLX framework installation and runtime
- ✅ mlx-lm library version
- ✅ Harmony renderer availability
- ✅ libmlx.dylib presence
- ✅ HuggingFace cache directory

**Example Output:**
```
🩺 mlxlm doctor

✅ Python : 3.10.12 (arm64)
✅ mlx    : 0.29.2 → /path/to/mlx/__init__.py
✅ mlx-lm : 0.28.2
✅ harmony: OK (renderer found)
✅ libmlx : OK → /path/to/libmlx.dylib
✅ HF hub : /Users/you/.cache/huggingface/hub → exists

If everything shows a checkmark✅, you're good to run `mlxlm run ...`
```

**Notes:**
- Run this if you encounter any runtime errors
- Checks for common configuration issues
- Verifies Apple Silicon compatibility
- Shows extended probe information if issues detected

---

## 🌍 Environment Variables

MLX-LM respects several environment variables for customization:

### `MLXLM_OFFLINE`
**Purpose:** Force offline mode (no HuggingFace API calls)
**Values:** `0` (default) or `1`
**Example:**
```bash
export MLXLM_OFFLINE=1
mlxlm show gemma3  # Uses only local cache
```

### `MLXLM_RENDERER`
**Purpose:** Override default Harmony renderer
**Values:** Module path (e.g., `openai_harmony:render_chat`)
**Example:**
```bash
export MLXLM_RENDERER="openai_harmony.chat:render"
mlxlm run gemma3 --chat harmony
```

### `MLXLM_DEBUG`
**Purpose:** Enable debug output
**Values:** `0` (default) or `1`
**Example:**
```bash
export MLXLM_DEBUG=1
mlxlm run gemma3  # Shows detailed debug info
```

**Debug output includes:**
- Rendered prompt character count
- Chat mode and stream mode
- History tracking (user/assistant message counts)
- Stop sequence handling
- MLX runtime probe details

### `MLXLM_STOP`
**Purpose:** Default stop sequences (comma-separated)
**Values:** String of sequences
**Example:**
```bash
export MLXLM_STOP="<END>,##,STOP"
mlxlm run gemma3
```

### `MLXLM_NO_DEFAULT_STOPS`
**Purpose:** Disable default Harmony stop sequences
**Values:** `0` (default) or `1`
**Example:**
```bash
export MLXLM_NO_DEFAULT_STOPS=1
mlxlm run gemma3 --chat harmony  # No <|end|>, <|start|> by default
```

### `MLXLM_REMEMBER_ASSISTANT`
**Purpose:** Force assistant history tracking (overrides `--history off`)
**Values:** `0` (default) or `1`
**Example:**
```bash
export MLXLM_REMEMBER_ASSISTANT=1
mlxlm run gemma3 --history off  # Still remembers assistant responses
```

### `MLXLM_KV_BYTES`
**Purpose:** Bytes per KV cache element (for memory estimation)
**Values:** `1`, `2` (default), or `4`
**Example:**
```bash
export MLXLM_KV_BYTES=4  # 32-bit precision
mlxlm run gemma3  # Shows adjusted memory estimates
```

---

## 🔄 Common Workflows

### Installing and Running a New Model

```bash
# 1. Pull the model
mlxlm pull google/gemma-3-27b-it

# 2. Verify it's downloaded
mlxlm list

# 3. Create a short alias
mlxlm alias add google/gemma-3-27b-it gemma3

# 4. Test with show
mlxlm show gemma3

# 5. Start chatting!
mlxlm run gemma3
```

---

### Managing Multiple Models

```bash
# View all models
mlxlm list

# Assign friendly names
mlxlm alias add models--google--gemma-3-27b-it gemma3
mlxlm alias add models--meta--llama3-8b llama3

# Quick switching
mlxlm run gemma3
mlxlm run llama3

# Remove unused models
mlxlm remove old-model --yes
```

---

### Customizing Chat Behavior

```bash
# Coding assistant
mlxlm run gemma3 \
  --system "You are an expert Python developer" \
  --max-tokens 1024

# Q&A mode (no context)
mlxlm run gemma3 --history off

# Harmony mode with custom stops
mlxlm run gemma3 \
  --chat harmony \
  --stop "<END>" \
  --stop "##"

# Memory-conscious chat
mlxlm run gemma3 \
  --history off \
  --max-tokens 512
```

---

### Debugging Issues

```bash
# Check environment
mlxlm doctor

# Enable debug mode
export MLXLM_DEBUG=1
mlxlm run gemma3

# Test with plain mode
mlxlm run gemma3 --chat plain

# Force offline mode
export MLXLM_OFFLINE=1
mlxlm show gemma3
```

---

## 🛠️ Troubleshooting

### Model Not Found

**Symptom:**
```
❓ Model not found
```

**Solutions:**
1. Verify model is installed: `mlxlm list`
2. Check spelling of model name/alias
3. Try using full repo ID: `google/gemma-3-27b-it`
4. Try cache key format: `models--google--gemma-3-27b-it`

---

### MLX Runtime Errors

**Symptom:**
```
❌ MLX runtime check failed: libmlx.dylib not found
```

**Solutions:**
```bash
# Reinstall MLX
pip uninstall -y mlx mlx-metal mlx-lm
pip install --no-cache-dir mlx==0.29.2 mlx-metal==0.29.2 mlx-lm==0.28.2

# Verify
mlxlm doctor
```

---

### Harmony Renderer Issues

**Symptom:**
```
❌ Harmony renderer not available.
```

**Solutions:**
```bash
# Install Harmony
pip install openai-harmony

# Or use alternative mode
mlxlm run gemma3 --chat hf

# Or plain text
mlxlm run gemma3 --chat plain
```

---

### Memory Issues

**Symptom:** System runs out of memory during generation

**Solutions:**
1. Reduce max tokens: `--max-tokens 512`
2. Use Q&A mode: `--history off`
3. Close other applications
4. Use a smaller model

---

### Model Type Not Detected

**Symptom:** Chat mode not working correctly

**Solutions:**
```bash
# Force a specific chat mode
mlxlm run gemma3 --chat harmony
mlxlm run gemma3 --chat hf
mlxlm run gemma3 --chat plain

# Check config
mlxlm show gemma3 --full
```

---

## 🎓 Advanced Usage

### Custom Stop Sequences

Stop sequences terminate generation when encountered:

```bash
# Single stop sequence
mlxlm run gemma3 --stop "END"

# Multiple sequences
mlxlm run gemma3 --stop "<END>" --stop "##" --stop "STOP"

# Via environment
export MLXLM_STOP="<END>,##,STOP"
mlxlm run gemma3
```

**Note:** For Harmony models, `<|end|>` and `<|start|>` are added by default unless `MLXLM_NO_DEFAULT_STOPS=1`.

---

### Memory Optimization

For large models, optimize memory usage:

```bash
# Q&A mode (no conversation history)
mlxlm run large-model --history off

# Shorter responses
mlxlm run large-model --max-tokens 256

# Monitor estimates
export MLXLM_DEBUG=1
mlxlm run large-model  # Shows KV cache estimates
```

---

### Offline Mode

Work without internet connection:

```bash
# Enable offline mode
export MLXLM_OFFLINE=1

# All commands use local cache only
mlxlm list
mlxlm show gemma3
mlxlm run gemma3
```

**Note:** Models must be downloaded (`mlxlm pull`) before offline use.

---

### Time Limits

Prevent runaway generation:

```bash
# 30 second limit per turn
mlxlm run gemma3 --time-limit 30

# 5 second limit
mlxlm run gemma3 --time-limit 5
```

When the limit is reached:
```
⏱️ Time limit reached, stopping.
```

---

### Streaming Modes

Control how output is displayed:

```bash
# Stream everything (default)
mlxlm run gemma3 --stream-mode all

# Stream only final Harmony channel
mlxlm run gemma3 --stream-mode final

# Wait for complete response
mlxlm run gemma3 --stream-mode off
```

---

## 📚 Additional Resources

- **Repository:** [github.com/your-org/mlxlm](https://github.com/your-org/mlxlm)
- **Issues:** Report bugs or request features on GitHub
- **MLX Documentation:** [ml-explore.github.io/mlx](https://ml-explore.github.io/mlx)
- **Contributing:** See [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 💡 Tips & Tricks

1. **Alias Everything:** Short names save typing
   ```bash
   mlxlm alias add models--long--name-here shortname
   ```

2. **Use Doctor First:** When troubleshooting, always run `mlxlm doctor`

3. **Q&A Mode for Scripts:** Use `--history off` for scripting/automation

4. **Debug Mode is Your Friend:** `export MLXLM_DEBUG=1` shows everything

5. **Test Before Committing:** Use `--dry-run` with `mlxlm remove`

6. **Check Config:** Use `mlxlm show model --full` to see all settings

---

**Happy chatting! 🚀**
