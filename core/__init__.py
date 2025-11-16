# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Core utilities for model resolution, config loading, and chat rendering."""

from __future__ import annotations

import os, sys, json, inspect, importlib
from pathlib import Path
from importlib import resources
from huggingface_hub import HfApi

# ===== Alias/Paths =====
HF_CACHE_PATH = os.path.expanduser("~/.cache/huggingface/hub")
# Project root is parent directory of core/
alias_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".mlxlm_aliases.json")

def load_alias_dict() -> dict:
    try:
        with open(alias_file_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, PermissionError):
        return {}

# ===== Name resolution =====
def resolve_model_name(name_or_alias: str, alias_dict: dict) -> str:
    """
    Resolve a user input (alias, repo ID, or cache key) to a canonical repo ID.

    Args:
        name_or_alias: User input string (e.g., 'gemma3', 'google/gemma-3-27b', 'models--google--gemma-3-27b')
        alias_dict: Dictionary mapping cache keys to aliases

    Returns:
        Canonical repo ID (e.g., 'google/gemma-3-27b-it')
    """
    user_input = name_or_alias.lower()
    alias_map_lower = {alias.lower(): full_name for full_name, alias in alias_dict.items()}
    if user_input in alias_map_lower:
        resolved = alias_map_lower[user_input]
        if resolved.lower().startswith("models--"):
            return resolved.replace("models--", "", 1).replace("--", "/")
        return resolved
    # Removed auto-conversion of hyphenated names (e.g., gpt-oss-20b -> gpt-oss/20b)
    # This was causing incorrect model resolution. User input should be passed as-is.
    model_names_lower = {full_name.lower(): full_name for full_name in alias_dict.keys()}
    if user_input in model_names_lower:
        return model_names_lower[user_input]
    if user_input.startswith("models--"):
        return name_or_alias.replace("models--", "", 1).replace("--", "/")
    return name_or_alias

def repo_to_cache_name(repo_id: str) -> str:
    """
    Convert a repo ID to HuggingFace cache directory name format.

    Args:
        repo_id: Repository ID (e.g., 'google/gemma-3-27b')

    Returns:
        Cache key format (e.g., 'models--google--gemma-3-27b')
    """
    if repo_id.startswith("models--"):
        return repo_id
    if "/" in repo_id:
        org, repo = repo_id.split("/", 1)
        return f"models--{org}--{repo}"
    return repo_id

def resolve_to_cache_key(name_or_alias: str, alias_dict: dict) -> str:
    """
    Resolve any user input to a cache key (models--org--repo format).

    Args:
        name_or_alias: User input (alias, repo ID, or cache key)
        alias_dict: Dictionary mapping cache keys to aliases

    Returns:
        Cache key in models--org--repo format
    """
    user = name_or_alias.strip()
    lower = user.lower()
    alias_map_lower = {alias.lower(): full_name for full_name, alias in alias_dict.items()}
    if lower in alias_map_lower:
        return alias_map_lower[lower]
    if lower.startswith("models--"):
        return user
    repo_id = resolve_model_name(user, alias_dict)
    return repo_to_cache_name(repo_id)

# ===== Config loader (HF / local cache) =====
def load_config_for_model(model_id: str) -> dict:
    """
    Load model config.json from HuggingFace API or local cache.

    Args:
        model_id: Model cache key (e.g., 'models--google--gemma-3-27b')

    Returns:
        Dictionary containing model configuration, or empty dict if not found
    """
    if os.getenv("MLXLM_OFFLINE") != "1":
        try:
            cfg = HfApi().model_info(model_id).config
            if isinstance(cfg, dict):
                return cfg
        except (ConnectionError, TimeoutError, ValueError, KeyError) as e:
            if os.getenv("MLXLM_DEBUG") == "1":
                print(f"[DEBUG] HF API call failed: {e}")
            pass
    cache_root = Path(HF_CACHE_PATH)
    model_dir = cache_root / model_id
    snap_base = model_dir / "snapshots"
    if not snap_base.exists():
        return {}
    snaps = sorted(snap_base.iterdir(), key=os.path.getmtime)
    for snap in reversed(snaps):
        cfg_path = snap / "config.json"
        if cfg_path.exists():
            try:
                with open(cfg_path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, PermissionError, OSError) as e:
                if os.getenv("MLXLM_DEBUG") == "1":
                    print(f"[DEBUG] Failed to load {cfg_path}: {e}")
                continue
    return {}

# ===== Runtime / Harmony detection =====
def _probe_mlx_runtime() -> tuple[bool, str, str | None]:
    """
    Probe MLX runtime availability and check libmlx.dylib.

    Returns:
        Tuple of (success: bool, info_message: str, lib_path: str | None)
    """
    try:
        base = resources.files('mlx')
        lib  = base / 'lib' / 'libmlx.dylib'
        if not lib.exists():
            return (False, f"{lib} not found", str(lib))
        import mlx.core as _mx  # noqa
        return (True, "mlx.core import OK", str(lib))
    except Exception as e:
        return (False, str(e), None)

def _get_model_type(model_name: str, alias_dict: dict) -> str | None:
    """
    Extract model_type from model configuration.

    Args:
        model_name: Model name or alias
        alias_dict: Alias dictionary

    Returns:
        Model type string (e.g., 'gpt_oss', 'llama'), or None if not found
    """
    try:
        repo_id = resolve_model_name(model_name, alias_dict)
        cache_key = repo_to_cache_name(repo_id)
        cfg = load_config_for_model(cache_key)
        if isinstance(cfg, dict):
            mt = (cfg.get("model_type") or cfg.get("model_architecture") or "").strip().lower()
            if mt:
                return mt
            arch = cfg.get("architectures")
            if isinstance(arch, list) and arch:
                return str(arch[0]).strip().lower()
        return None
    except (KeyError, ValueError, TypeError) as e:
        if os.getenv("MLXLM_DEBUG") == "1":
            print(f"[DEBUG] Failed to get model type for {model_name}: {e}")
        return None

def _load_callable_from_path(spec: str) -> callable | None:
    """
    Load a callable (function or class method) from a module path specification.

    Args:
        spec: Module path in format 'module.path' or 'module.path:attribute'

    Returns:
        Callable object if found, None otherwise
    """
    if not spec:
        return None
    if ":" in spec:
        mod_name, attr = spec.split(":", 1)
    else:
        mod_name, attr = spec, ""
    try:
        mod = importlib.import_module(mod_name)
    except Exception:
        return None
    if not attr:
        for name in dir(mod):
            if name.startswith(("render","format")):
                fn = getattr(mod, name, None)
                if callable(fn):
                    return fn
        for attr_name in ("Harmony","Renderer","HarmonyRenderer","ChatRenderer"):
            cls = getattr(mod, attr_name, None)
            if cls:
                try:
                    inst = cls()
                    if callable(getattr(inst, "render", None)):
                        return inst.render
                except Exception:
                    pass
        return None
    obj = mod
    for part in attr.split("."):
        obj = getattr(obj, part, None)
        if obj is None:
            return None
    if inspect.isclass(obj):
        try:
            inst = obj()
            if callable(getattr(inst, "render", None)):
                return inst.render
        except Exception:
            return None
    return obj if callable(obj) else None

def _detect_harmony_renderer() -> callable | None:
    """
    Detect and load Harmony chat renderer from installed packages.

    Checks MLXLM_RENDERER environment variable first, then searches for
    openai-harmony, openai.harmony, or harmony packages.

    Returns:
        Callable renderer function if found, None otherwise
    """
    env_spec = os.getenv("MLXLM_RENDERER", "").strip()
    if env_spec:
        fn = _load_callable_from_path(env_spec)
        if fn:
            if os.getenv("MLXLM_DEBUG") == "1":
                print(f"[DEBUG] Using renderer from MLXLM_RENDERER={env_spec}")
            return fn
        else:
            print(f"⚠️  MLXLM_RENDERER set to '{env_spec}' but callable not found.")
    explicit_names = ("render_chat","render","render_messages","format_chat","format_messages","render_chatml","to_chatml","format","chat_format")
    submods = ("", "chat", "renderer", "render", "core")
    bases = ("openai_harmony", "openai.harmony", "harmony")
    def _pick_renderer(mod):
        for name in explicit_names:
            fn = getattr(mod, name, None)
            if callable(fn): return fn
        for name in dir(mod):
            if name.startswith(("render","format")):
                fn = getattr(mod, name, None)
                if callable(fn):
                    try:
                        sig = inspect.signature(fn)
                        if any(p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD) for p in sig.parameters.values()):
                            return fn
                    except Exception:
                        return fn
        for attr in ("Harmony","Renderer","HarmonyRenderer","ChatRenderer"):
            cls = getattr(mod, attr, None)
            if cls:
                try:
                    inst = cls()
                    if callable(getattr(inst, "render", None)):
                        return inst.render
                except Exception:
                    continue
        return None
    import importlib as _il
    for base in bases:
        for sub in submods:
            mod_name = f"{base}.{sub}" if sub else base
            try:
                mod = _il.import_module(mod_name)
            except Exception:
                continue
            fn = _pick_renderer(mod)
            if callable(fn):
                return fn
    return None

def _preflight_and_maybe_adjust_chat(chat_mode: str, model_name: str, alias_dict: dict) -> str:
    """
    Validate runtime environment and adjust chat mode if needed.

    Performs MLX runtime checks and automatically switches to Harmony mode
    for gpt_oss models.

    Args:
        chat_mode: Requested chat mode ('auto', 'harmony', 'hf', 'plain')
        model_name: Model name or alias
        alias_dict: Alias dictionary

    Returns:
        Validated/adjusted chat mode string
    """
    ok, info, lib = _probe_mlx_runtime()
    if not ok:
        print("❌ MLX runtime check failed:", info)
        print("👉 Try reinstalling:")
        print("   pip uninstall -y mlx mlx-metal mlx-lm")
        print("   pip install --no-cache-dir mlx==0.29.2 mlx-metal==0.29.2 mlx-lm==0.28.2\n")
        sys.exit(1)
    mtype = _get_model_type(model_name, alias_dict) or ""
    needs_harmony = ("gpt_oss" in mtype)
    if needs_harmony and chat_mode in ("auto","hf","plain"):
        print("ℹ️ Detected model_type 'gpt_oss' → using Harmony chat renderer.")
        chat_mode = "harmony"
    if chat_mode == "harmony":
        renderer = _detect_harmony_renderer()
        if renderer is None:
            print("❌ Harmony renderer not available.")
            print("👉 Install one: pip install openai-harmony  # or: pip install harmony\n")
            sys.exit(1)
    if os.getenv("MLXLM_DEBUG") == "1":
        print(f"[DEBUG] MLX libmlx: {lib}")
        print(f"[DEBUG] Model type : {mtype or 'unknown'}")
        print(f"[DEBUG] Chat mode  : {chat_mode}")
    return chat_mode

# ===== Rendering / messages =====
def _apply_reasoning_to_system(system_prompt: str, reasoning_level: str | None) -> str:
    """
    Add reasoning level hint to system prompt if specified.

    Args:
        system_prompt: Base system prompt
        reasoning_level: Reasoning verbosity level ('low', 'medium', 'high'), or None

    Returns:
        Modified system prompt with reasoning hint prepended
    """
    return (f"Reasoning: {reasoning_level}\n{system_prompt}".strip()
            if reasoning_level else system_prompt)

def _render_plain(system_prompt: str, history: list[tuple[str, str]]) -> str:
    """
    Render conversation in plain text format.

    Args:
        system_prompt: System prompt text
        history: List of (role, content) tuples

    Returns:
        Plain text formatted prompt
    """
    last_user = ""
    for role, content in reversed(history):
        if role == "user":
            last_user = content; break
    return f"{system_prompt}\n\nUser: {last_user}\nAssistant:"

def _render_hf_template(tokenizer: any, messages: list[dict]) -> str | None:
    """
    Render messages using HuggingFace chat_template.

    Args:
        tokenizer: Tokenizer with apply_chat_template method
        messages: List of message dicts with 'role' and 'content' keys

    Returns:
        Rendered prompt string, or None if template not available
    """
    try:
        if hasattr(tokenizer, "apply_chat_template"):
            return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    except Exception:
        pass
    return None

def _compose_messages(system_prompt: str, history: list[tuple[str, str]]) -> list[dict]:
    """
    Convert system prompt and history into standard message format.

    Args:
        system_prompt: System prompt text
        history: List of (role, content) tuples

    Returns:
        List of message dicts with 'role' and 'content' keys
    """
    msgs = []
    if system_prompt:
        msgs.append({"role":"system","content":system_prompt})
    for role, content in history:
        msgs.append({"role":role,"content":content})
    return msgs

def render_harmony_simple(messages: list[dict]) -> str:
    """
    Simple Harmony format renderer (fallback implementation).

    Args:
        messages: List of message dicts with 'role' and 'content' keys

    Returns:
        Harmony-formatted prompt string
    """
    parts=[]
    for m in messages:
        role=m.get("role","user")
        content=m.get("content","")
        parts.append(f"<|start|>{role}<|message|>{content}<|end|>")
    parts.append("<|start|>assistant")
    return "\n".join(parts)

def _render_prompt(chat_mode: str, tokenizer: any, system_prompt: str, history: list[tuple[str, str]]) -> str:
    """
    Render conversation prompt using the specified chat mode.

    Args:
        chat_mode: Chat rendering mode ('harmony', 'hf', 'plain', 'auto')
        tokenizer: Model tokenizer
        system_prompt: System prompt text
        history: Conversation history as (role, content) tuples

    Returns:
        Rendered prompt string ready for model input
    """
    messages = _compose_messages(system_prompt, history)
    if chat_mode == "plain":
        return _render_plain(system_prompt, history)
    if chat_mode == "harmony":
        renderer = _detect_harmony_renderer()
        if not renderer:
            raise RuntimeError("Harmony renderer not available. Please install the official harmony package.")
        return renderer(messages)
    if chat_mode == "hf":
        rendered = _render_hf_template(tokenizer, messages)
        if rendered is None:
            raise RuntimeError("HF chat_template not available for this tokenizer.")
        return rendered
    renderer = _detect_harmony_renderer()
    if renderer:
        try:
            return renderer(messages)
        except Exception:
            pass
    rendered = _render_hf_template(tokenizer, messages)
    if rendered is not None:
        return rendered
    return _render_plain(system_prompt, history)

# ===== Token / memory helpers =====
def _human_bytes(n: int) -> str:
    """
    Convert byte count to human-readable format.

    Args:
        n: Number of bytes

    Returns:
        Formatted string (e.g., '1.5 GB', '512.00 MB')
    """
    units=["B","KB","MB","GB","TB"]; s=float(n)
    for u in units:
        if s<1024.0: return f"{s:.2f} {u}"
        s/=1024.0
    return f"{s:.2f} PB"

def _count_tokens(tokenizer: any, text: str) -> int:
    """
    Count tokens in text using the provided tokenizer.

    Args:
        tokenizer: Model tokenizer
        text: Text to tokenize

    Returns:
        Approximate token count (fallback: len(text)/4)
    """
    try:
        if hasattr(tokenizer,"encode"):
            ids = tokenizer.encode(text)
            if isinstance(ids,list): return len(ids)
            if hasattr(ids,"ids"): return len(ids.ids)
    except Exception: pass
    try:
        out = tokenizer(text)
        if isinstance(out,dict) and "input_ids" in out:
            ids = out["input_ids"]
            if isinstance(ids,list): return len(ids)
            try: return len(ids[0])
            except Exception: pass
        if hasattr(out,"input_ids"):
            ids=out.input_ids
            if isinstance(ids,list): return len(ids)
            try: return len(ids[0])
            except Exception: pass
    except Exception: pass
    return max(1,int(len(text)/4))

def _estimate_kv_bytes(layers: int, hidden_size: int, ctx_tokens: int, dtype_bytes: int = 2, batch: int = 1) -> int:
    """
    Estimate KV cache memory usage.

    Args:
        layers: Number of transformer layers
        hidden_size: Hidden dimension size
        ctx_tokens: Context length in tokens
        dtype_bytes: Bytes per value (1=int8, 2=float16, 4=float32)
        batch: Batch size

    Returns:
        Estimated memory usage in bytes
    """
    if layers<=0 or hidden_size<=0 or ctx_tokens<=0: return 0
    per_tok_per_layer = 2*hidden_size*dtype_bytes
    return int(layers*ctx_tokens*per_tok_per_layer*batch)

# ===== Streaming helper (Harmony final only) =====
def _stream_final_from_harmony(token_iter: any) -> any:
    """
    Extract and stream only the final channel content from Harmony output.

    Filters Harmony streaming output to extract only text between
    <|channel|>final<|message|> and <|end|> markers.

    Args:
        token_iter: Iterator yielding token strings

    Yields:
        Cleaned text chunks from the final channel
    """
    import re
    buf=""; in_final=False
    marker="<|channel|>final<|message|>"; end_markers=("<|end|>","<|start|>")
    marker_max_len = max(len(m) for m in end_markers)  # = 10 (<|start|>)
    keep_buffer = marker_max_len + 64  # marker length + buffer margin

    def _clean(s:str)->str: return re.sub(r"<\|[^>]*\|>","",s)
    for t in token_iter:
        buf+=t
        if not in_final:
            idx=buf.find(marker)
            if idx!=-1:
                in_final=True
                leftover=buf[idx+len(marker):]
                if leftover: yield _clean(leftover)
                buf=""
            else:
                if len(buf)>len(marker)+64: buf=buf[-(len(marker)+64):]
        else:
            end_idx=-1
            for m in end_markers:
                i=buf.find(m)
                if i!=-1:
                    end_idx = i if end_idx==-1 else min(end_idx,i)
            if end_idx!=-1:
                chunk=buf[:end_idx]
                if chunk: yield _clean(chunk)
                break
            # Buffer size management (dynamic, previously fixed at 256)
            if len(buf) > keep_buffer * 4:  # flush when buffer exceeds 4x marker length
                flush=buf[:-keep_buffer]
                buf=buf[-keep_buffer:]
                if flush: yield _clean(flush)
    if in_final and buf:
        yield _clean(buf)

# ===== User Configuration Management =====

def get_default_config() -> dict:
    """
    Return the default configuration for mlxlm.

    Returns:
        dict: Default configuration with all settings
    """
    return {
        "version": "1.0",
        "defaults": {
            "max_tokens": 2048,
            "stream_mode": "all",
            "chat_mode": "auto",
            "history": "on",
            "time_limit": 0,
            "reasoning": None,
            "show_context_stats": False
        },
        "history": {
            "max_entries": 50,
            "max_age_days": None
        },
        "colors": {
            "user_prompt": "\033[1;37m",
            "model_output": "\033[97m",
            "error": "\033[91m",
            "success": "\033[92m",
            "warning": "\033[93m",
            "reset": "\033[0m"
        },
        "export": {
            "default_format": "md",
            "include_timestamp": True,
            "auto_save": False
        },
        "sessions": {
            "auto_save_interval": 300
        }
    }

def get_config_path() -> Path:
    """
    Get the path to the user config file.

    Returns:
        Path: Path to mlxlm_data/config.json
    """
    # Project root is parent.parent because we're in core/__init__.py
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "mlxlm_data"
    data_dir.mkdir(exist_ok=True)
    return data_dir / "config.json"

def get_mlxlm_data_dir() -> Path:
    """
    Get the path to the mlxlm_data directory.

    Returns:
        Path: Path to mlxlm_data/ directory
    """
    # Project root is parent.parent because we're in core/__init__.py
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "mlxlm_data"
    data_dir.mkdir(exist_ok=True)
    return data_dir

def load_user_config() -> dict:
    """
    Load user configuration from mlxlm_data/config.json.
    If file doesn't exist or is invalid, return default config.

    Returns:
        dict: Merged configuration (default + user overrides)
    """
    config_path = get_config_path()
    default_config = get_default_config()

    if not config_path.exists():
        return default_config

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)

        # Merge user config with defaults (user config takes precedence)
        return merge_configs(default_config, user_config)
    except (json.JSONDecodeError, PermissionError, OSError) as e:
        # If config is corrupted, return defaults
        print(f"⚠️  Warning: Could not load config.json ({e}), using defaults")
        return default_config

def save_user_config(config: dict) -> bool:
    """
    Save user configuration to mlxlm_data/config.json.

    Args:
        config: Configuration dictionary to save

    Returns:
        bool: True if successful, False otherwise
    """
    config_path = get_config_path()

    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except (PermissionError, OSError) as e:
        print(f"⚠️  Error: Could not save config.json ({e})")
        return False

def merge_configs(default: dict, user: dict) -> dict:
    """
    Recursively merge user configuration with default configuration.
    User values take precedence over defaults.

    Args:
        default: Default configuration dictionary
        user: User configuration dictionary

    Returns:
        dict: Merged configuration
    """
    merged = default.copy()

    for key, value in user.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            merged[key] = merge_configs(merged[key], value)
        else:
            # Override with user value
            merged[key] = value

    return merged
