# 🧠 MLX-LM CLI Tool

This repository provides a simple CLI interface for working with MLX-based language models on Apple Silicon.  
It aims to offer a friendly, scriptable, and consistent way to explore and manage MLX-LM models.

---

## 📦 Features

- 📋 **List models** - View all installed MLX-LM models with sizes and aliases
- ℹ️ **Model info** - Inspect model configuration, architecture, and precision
- 💬 **Interactive chat** - Conversational mode with full context awareness
- 🎭 **Multiple renderers** - Harmony, HuggingFace, or plain text formatting
- 💾 **Conversation history** - Toggle between full context or Q&A mode
- 🛑 **Stop sequences** - Fine-grained output control
- 🏷️ **Alias management** - Quick shortcuts for long model names

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
  - `final`: Stream only Harmony final channel content
  - `off`: Wait for complete response before displaying
- 🛑 `--stop "seq"`: Add stop sequences (can be repeated)
- ⏱️ `--time-limit N`: Hard time limit per turn in seconds (0=off)
- 🧠 `--reasoning {low|medium|high}`: Hint for reasoning verbosity

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

## 📁 Folder Structure

```
MLX-LM/
├── mlxlm.py            # Main CLI entry point
├── commands.py         # Core command implementations (list, show, pull, run, alias, doctor)
├── core.py             # Utility functions (model loading, rendering, streaming, Harmony support)
├── cli_flags.py        # CLI argument parser definitions
├── .mlxlm_aliases.json # Model alias mappings (auto-generated)
├── README.md           # This file
└── .gitignore
```

**Main source files:**
- 🎯 `mlxlm.py`: Entry point, command routing
- ⚙️ `commands.py`: All command handlers (list, show, pull, remove, run, alias, doctor)
- 🔧 `core.py`: Core utilities (config loading, model type detection, prompt rendering, streaming helpers)
- 📋 `cli_flags.py`: Argument parser setup
- 🔐 `LICENSE`: MIT License
- 📄 `README.md`: This documentation

---

## 📝 Notes

- **Ollama-inspired**: Built to bring Ollama-like simplicity to MLX-LM
- **Apple Silicon optimized**: Leverages MLX framework for native performance
- **Model agnostic**: Works with any MLX-compatible model
- **Extensible**: Alias system and multiple chat modes for flexibility

---

## 🤝 Contributing

Feedback and contributions welcome! Found a bug or have an idea? Feel free to open an issue.

---

## 📄 License

MIT License - See LICENSE file for details
