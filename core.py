import os, sys, json, inspect, importlib
from pathlib import Path
from importlib import resources
from huggingface_hub import HfApi

# ===== Alias/Paths =====
alias_file_path = os.path.join(os.path.dirname(__file__), ".mlxlm_aliases.json")

def load_alias_dict() -> dict:
    try:
        with open(alias_file_path, "r") as f:
            return json.load(f)
    except Exception:
        return {}

# ===== Name resolution =====
def resolve_model_name(name_or_alias, alias_dict):
    user_input = name_or_alias.lower()
    alias_map_lower = {alias.lower(): full_name for full_name, alias in alias_dict.items()}
    if user_input in alias_map_lower:
        resolved = alias_map_lower[user_input]
        if resolved.lower().startswith("models--"):
            return resolved.replace("models--", "", 1).replace("--", "/")
        return resolved
    if "/" not in name_or_alias and name_or_alias.count("-") >= 2 and not name_or_alias.startswith("models--"):
        parts = name_or_alias.split("-", 2)
        org = f"{parts[0]}-{parts[1]}"
        repo = parts[2]
        return f"{org}/{repo}"
    model_names_lower = {full_name.lower(): full_name for full_name in alias_dict.keys()}
    if user_input in model_names_lower:
        return model_names_lower[user_input]
    if user_input.startswith("models--"):
        return name_or_alias.replace("models--", "", 1).replace("--", "/")
    return name_or_alias

def repo_to_cache_name(repo_id: str) -> str:
    if repo_id.startswith("models--"):
        return repo_id
    if "/" in repo_id:
        org, repo = repo_id.split("/", 1)
        return f"models--{org}--{repo}"
    return repo_id

def resolve_to_cache_key(name_or_alias: str, alias_dict: dict) -> str:
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
    if os.getenv("MLXLM_OFFLINE") != "1":
        try:
            cfg = HfApi().model_info(model_id).config
            if isinstance(cfg, dict):
                return cfg
        except Exception:
            pass
    cache_root = Path.home() / ".cache" / "huggingface" / "hub"
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
            except Exception:
                continue
    return {}

# ===== Runtime / Harmony detection =====
def _probe_mlx_runtime():
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
    except Exception:
        return None

def _load_callable_from_path(spec: str):
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

def _detect_harmony_renderer():
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
    return (f"Reasoning: {reasoning_level}\n{system_prompt}".strip()
            if reasoning_level else system_prompt)

def _render_plain(system_prompt: str, history: list[tuple[str,str]]) -> str:
    last_user = ""
    for role, content in reversed(history):
        if role == "user":
            last_user = content; break
    return f"{system_prompt}\n\nUser: {last_user}\nAssistant:"

def _render_hf_template(tokenizer, messages: list[dict]) -> str | None:
    try:
        if hasattr(tokenizer, "apply_chat_template"):
            return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    except Exception:
        pass
    return None

def _compose_messages(system_prompt: str, history: list[tuple[str,str]]) -> list[dict]:
    msgs = []
    if system_prompt:
        msgs.append({"role":"system","content":system_prompt})
    for role, content in history:
        msgs.append({"role":role,"content":content})
    return msgs

def render_harmony_simple(messages: list[dict]) -> str:
    parts=[]
    for m in messages:
        role=m.get("role","user")
        content=m.get("content","")
        parts.append(f"<|start|>{role}<|message|>{content}<|end|>")
    parts.append("<|start|>assistant")
    return "\n".join(parts)

def _render_prompt(chat_mode: str, tokenizer, system_prompt: str, history: list[tuple[str,str]]):
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
    units=["B","KB","MB","GB","TB"]; s=float(n)
    for u in units:
        if s<1024.0: return f"{s:.2f} {u}"
        s/=1024.0
    return f"{s:.2f} PB"

def _count_tokens(tokenizer, text: str) -> int:
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

def _estimate_kv_bytes(layers:int, hidden_size:int, ctx_tokens:int, dtype_bytes:int=2, batch:int=1)->int:
    if layers<=0 or hidden_size<=0 or ctx_tokens<=0: return 0
    per_tok_per_layer = 2*hidden_size*dtype_bytes
    return int(layers*ctx_tokens*per_tok_per_layer*batch)

# ===== Streaming helper (Harmony final only) =====
def _stream_final_from_harmony(token_iter):
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
