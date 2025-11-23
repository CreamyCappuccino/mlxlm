# Search Command - Addition to USAGE.md

**Add this section to USAGE.md after the existing commands section**

---

## 🔍 Search Models on HuggingFace

The `mlxlm search` command lets you discover and explore text-generation models on HuggingFace directly from your terminal.

### Basic Usage

```bash
mlxlm search <query>
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

### 🎨 Color Coding

Results are color-coded for quick identification:
- 🟢 **Green**: MLX-compatible models
- 🟡 **Yellow**: Quantized models (GGUF, 4-bit, 8-bit)
- 🔵 **Blue**: Official models (meta-llama, mistralai, google, etc.)
- ⚪ **White**: Other models

### 🎮 Interactive Menu Navigation

```
1-7  → Select a model to view details
8    → Next page
9    → Open filters menu
0    → Exit search
```

### 🎛️ Filters & Options

#### Filter by Tags
```bash
mlxlm search mistral --filter-tag mlx
mlxlm search phi --filter-tag mlx --filter-tag quantized
```

**Common tags:** `mlx`, `gguf`, `quantized`, `4-bit`, `8-bit`, `f16`, `f32`

#### Filter by Size
```bash
mlxlm search qwen --max-size 10
```
Shows only models under 10GB.

#### Filter by Popularity
```bash
mlxlm search gemma --min-downloads 5000
```
Shows only models with at least 5000 downloads.

#### Filter by Recency
```bash
mlxlm search llama --updated-within 30
```
Shows only models updated in the last 30 days.

#### Sort Results
```bash
mlxlm search mistral --sort downloads  # Default
mlxlm search llama --sort updated      # Recently updated first
mlxlm search phi --sort size           # Smallest first
```

#### Combine Multiple Filters
```bash
mlxlm search qwen \
  --filter-tag mlx \
  --max-size 5 \
  --min-downloads 1000 \
  --updated-within 90 \
  --sort updated
```

### 🤖 AI-Friendly Modes

#### JSON Output
```bash
mlxlm search llama --json
```

Returns structured JSON with:
```json
{
  "query": "llama",
  "total": 142,
  "filters": { ... },
  "results": [
    {
      "repo_id": "meta-llama/Llama-3.2-3B",
      "size_bytes": 3200000000,
      "downloads": 152340,
      "last_modified": "2025-11-20T14:32:10Z",
      "tags": ["llama", "text-generation"]
    }
  ]
}
```

Perfect for AI agents and scripts.

#### Non-Interactive Mode
```bash
mlxlm search mistral --no-interactive
```

Displays results as plain text without pagination menu. Useful for piping to other commands.

### 📚 Help & Documentation

#### Quick Help
```bash
mlxlm search --help
```
Shows concise option summary and Quick Start examples.

#### Detailed Help
```bash
mlxlm search llama --help-detail
```
Shows comprehensive documentation including:
- All options with detailed explanations
- 8 practical usage examples
- Output modes comparison
- Color coding legend
- Technical notes

### 💡 Tips & Tricks

**1. Find small MLX models for testing:**
```bash
mlxlm search phi --filter-tag mlx --max-size 5 --sort size
```

**2. Discover newly released models:**
```bash
mlxlm search qwen --updated-within 7 --sort updated
```

**3. Popular quantized models:**
```bash
mlxlm search mistral --filter-tag gguf --min-downloads 10000
```

**4. Export search results for later:**
```bash
mlxlm search llama --json > llama_models.json
```

### ⚠️ Notes

- **Task filter**: All searches are limited to `text-generation` models
- **Size metadata**: Some models may show "N/A" for size if safetensors metadata is unavailable
- **Sorting by size**: Performed client-side (may be slower for large result sets)
- **Tag matching**: Case-insensitive and partial matches supported

### 🔗 Related Commands

After finding a model with `search`, you can:
```bash
mlxlm pull <model-name>   # Download the model
mlxlm show <model-name>   # View model details
mlxlm run <model-name>    # Run the model
```

---

**Example Workflow:**

```bash
# 1. Search for small MLX models
mlxlm search phi --filter-tag mlx --max-size 5

# 2. Select a model from the interactive menu (e.g., #3)
# → View details and copy repo ID

# 3. Download the model
mlxlm pull mlxlm-community/Phi-3.5-mini-instruct-4bit

# 4. Create an alias
mlxlm alias add mlxlm-community/Phi-3.5-mini-instruct-4bit phi

# 5. Run it
mlxlm run phi
```
