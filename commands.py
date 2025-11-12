# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Command implementations for mlxlm CLI: list, show, pull, remove, run, alias, doctor."""

import os, sys, json, time, subprocess
from datetime import datetime
from pathlib import Path

from mlx_lm import load, generate, stream_generate
from huggingface_hub import snapshot_download

from core import (
    HF_CACHE_PATH, alias_file_path, load_alias_dict,
    resolve_model_name, repo_to_cache_name, resolve_to_cache_key,
    load_config_for_model, _probe_mlx_runtime, _detect_harmony_renderer,
    _apply_reasoning_to_system, _render_prompt,
    _human_bytes, _count_tokens, _estimate_kv_bytes, _stream_final_from_harmony,
)

# ----- list -----
def list_models(show_all: bool = False):
    model_dir = HF_CACHE_PATH
    alias_dict = load_alias_dict()
    if os.path.exists(model_dir):
        models = []
        for m in os.listdir(model_dir):
            # By default, include all models (models--<org>--<repo>) in the listing
            if not m.startswith("models--"):
                continue
            model_path = os.path.join(model_dir, m)
            if not os.path.isdir(model_path):
                continue
            snaps = os.path.join(model_path, "snapshots")
            if os.path.isdir(snaps):
                try:
                    has_snap = any(entry.is_dir() for entry in os.scandir(snaps))
                except Exception:
                    has_snap = False
                if has_snap:
                    models.append(m)

            # Fallback: accept repos without snapshots if they have artifacts in the repo root
            if m not in models:
                try:
                    files = os.listdir(model_path)
                    if any(f in files for f in ("config.json", "model.safetensors", "pytorch_model.bin", "model.safetensors.index.json", "tokenizer.json", "tokenizer.model")):
                        models.append(m)
                except Exception:
                    pass


        # Output
        if models:
            if os.getenv("MLXLM_DEBUG") == "1":
                print(f"[DEBUG] Scanned hub at {model_dir}; found {len(models)} model dirs (snapshots or artifacts).")
            print("🧠 Installed MLX Models:\n")
            print("MODEL NAME".ljust(65), "ALIAS".ljust(24), "SIZE".ljust(10), "LAST MODIFIED")
            for m in models:
                model_path = os.path.join(model_dir, m)
                file_paths = [os.path.join(root, f) for root, _, files in os.walk(model_path) for f in files]
                try:
                    size_str = subprocess.check_output(['du', '-sh', model_path]).decode().split()[0]
                except Exception:
                    size_str = "N/A"
                try:
                    mod_time = max(os.path.getmtime(fp) for fp in file_paths) if file_paths else os.path.getmtime(model_path)
                    dt_now = datetime.now(); dt_mod = datetime.fromtimestamp(mod_time)
                    delta = dt_now - dt_mod
                    if delta.days == 0:   mod_str = "Today"
                    elif delta.days == 1: mod_str = "Yesterday"
                    else:                 mod_str = f"{delta.days} days ago"
                except Exception:
                    mod_str = "N/A"
                alias = alias_dict.get(m, "")
                print(m.ljust(65), alias.ljust(24), size_str.ljust(10), mod_str)
        else:
            print("(No models installed)")
    else:
        print("❗ Model directory not found")

# ----- show -----
def show_info(model_name, full=False):
    if "/" in model_name and not model_name.startswith("models--"):
        org, repo = model_name.split("/", 1)
        model_name = f"models--{org}--{repo}"
    alias_dict = load_alias_dict()
    alias_map_lower = {alias.lower(): full_name for full_name, alias in alias_dict.items()}
    user_input = model_name.lower()
    if user_input in alias_map_lower:
        model_name = alias_map_lower[user_input]
    model_path = os.path.join(HF_CACHE_PATH, model_name)
    if os.path.exists(model_path):
        try: size_str = subprocess.check_output(['du','-sh',model_path]).decode().split()[0]
        except Exception: size_str="N/A"
        alias = alias_dict.get(model_name,"")
        config = load_config_for_model(model_name)
        if isinstance(config.get("text_config"), dict):
            config = {**config, **config["text_config"]}
        if not config:
            print("ℹ️ Could not load config.json for this model."); return
        if full:
            from pprint import pprint
            print("\n🔧 Model Configuration (full config.json):\n")
            pprint(config, indent=2, width=100, compact=False); return
        def pick(conf,*keys):
            for k in keys:
                if k in conf: return conf[k]
            return "Unknown"
        precision="N/A"; quant_cfg=config.get("quantization_config")
        if isinstance(quant_cfg,dict): precision=quant_cfg.get("dtype","N/A")
        print("MODEL INFO\n")
        print(f"Name{'':<19}: {model_name}")
        print(f"Size{'':<19}: {size_str}")
        print(f"Alias{'':<19}: {alias}")
        print("\n[CONFIG INFO]")
        print(f"{'Model Architecture':<22} : {pick(config,'architectures')[0] if isinstance(config.get('architectures'),list) else 'Unknown'}")
        print(f"{'Hidden Size':<22} : {pick(config,'hidden_size','n_embd')}")
        print(f"{'Layers':<22} : {pick(config,'num_hidden_layers','n_layer','layers')}")
        print(f"{'Heads':<22} : {pick(config,'num_attention_heads','n_head','heads')}")
        print(f"{'Precision':<22} : {precision}")
        print(f"\n[PATH]".ljust(22), ":", model_path)
    else:
        print("❓ Model not found")

# ----- pull -----
def pull_model(model_name):
    print(f"🔽 Downloading model '{model_name}' to local cache...")
    try:
        local_dir = snapshot_download(repo_id=model_name)
        print(f"✅ Model downloaded to: {local_dir}")
    except Exception as e:
        print(f"❌ Failed to download model: {e}")

# ----- remove -----
def remove_models(targets, assume_yes: bool = False, dry_run: bool = False):
    hub_root = HF_CACHE_PATH
    alias_dict = load_alias_dict()
    cache_keys=[]
    for t in targets:
        key = resolve_to_cache_key(t, alias_dict)
        if key not in cache_keys: cache_keys.append(key)
    plans=[]
    for key in cache_keys:
        path=os.path.join(hub_root,key)
        exists=os.path.isdir(path)
        plans.append((key,path,exists))
    print("🗑️  Removal plan:\n")
    for key, path, exists in plans:
        status="FOUND" if exists else "MISSING"
        print(f" - {key} -> {path} [{status}]")
    if dry_run:
        print("\n✅ Dry-run: no changes were made."); return
    if not assume_yes:
        confirm=input("\nProceed to delete the FOUND items above? This cannot be undone. [(y)/n]: ").strip().lower()
        if confirm not in ("","y","yes"):
            print("❌ Operation cancelled."); return
    removed=[]
    for key, path, exists in plans:
        if not exists: continue
        try:
            import shutil; shutil.rmtree(path)
            removed.append(key); print(f"✅ Deleted: {path}")
        except Exception as e:
            print(f"⚠️  Failed to delete {path}: {e}")
    if removed:
        alias_changed=False
        for full_name in list(alias_dict.keys()):
            if full_name in removed:
                alias_changed=True
                alias = alias_dict.pop(full_name, None)
                if alias: print(f"🧹 Removed alias '{alias}' for '{full_name}'.")
        if alias_changed:
            try:
                with open(alias_file_path,"w") as f: json.dump(alias_dict,f,indent=2)
                print("📝 Alias file updated.")
            except Exception as e:
                print(f"⚠️  Failed to update alias file: {e}")
    print("\n🎯 Done.")

# ----- doctor -----
def cmd_doctor():
    print("🩺 mlxlm doctor\n")
    import platform, importlib.util, importlib.metadata as _ilmd
    def mark(ok: bool) -> str: return "✅" if ok else "  "
    py_ok=True; print(f"{mark(py_ok)} Python : {sys.version.split()[0]} ({platform.machine()})")
    # MLX
    mlx_ok=False
    try:
        import mlx
        try: mlx_ver=_ilmd.version("mlx")
        except Exception: mlx_ver="unknown"
        ok, _, libpath = _probe_mlx_runtime()
        mlx_ok=ok
        loc=getattr(mlx,"__file__",None) or "unknown"
        print(f"{mark(mlx_ok)} mlx    : {mlx_ver} → {loc}")
    except Exception as e:
        print(f"{mark(False)} mlx    : (import failed) {e}")
    # mlx-lm
    try:
        import mlx_lm
        mlxlm_ver = getattr(mlx_lm,'__version__', _ilmd.version('mlx-lm'))
        print(f"{mark(True)} mlx-lm : {mlxlm_ver}")
    except Exception as e:
        print(f"{mark(False)} mlx-lm : (import failed) {e}")
    # Harmony
    try:
        installed = any(importlib.util.find_spec(n) is not None for n in ("openai_harmony","openai.harmony","harmony"))
    except Exception:
        installed=False
    try:
        renderer = _detect_harmony_renderer()
    except Exception:
        renderer = None
    if renderer:
        print(f"{mark(True)} harmony: OK (renderer found)")
    else:
        if installed:
            print(f"{mark(False)} harmony: INSTALLED (renderer not found; try updating `openai-harmony` or set MLXLM_RENDERER)")
        else:
            print(f"{mark(False)} harmony: MISSING")
    ok_lib, info_lib, lib_path = _probe_mlx_runtime()
    print(f"{mark(ok_lib)} libmlx : {'OK' if ok_lib else 'NG'} → {(lib_path or info_lib)}")
    hub = HF_CACHE_PATH
    hub_ok = os.path.isdir(hub)
    print(f"{mark(hub_ok)} HF hub : {hub} → {'exists' if hub_ok else 'missing'}")
    if not renderer:
        try:
            import importlib as _il
            candidates=[]
            for base in ("openai_harmony","openai.harmony","harmony"):
                for sub in ("","chat","renderer","render","core","api","utils"):
                    mod_name = f"{base}.{sub}" if sub else base
                    try:
                        mod = _il.import_module(mod_name)
                        names = [n for n in dir(mod) if n.startswith(('render','format'))]
                        if names: candidates.append((mod_name, names[:8]))
                    except Exception:
                        continue
            if candidates:
                print("harmony candidates:")
                for mod_name, names in candidates:
                    print("  -", mod_name, "→", ", ".join(names))
            env_spec = os.getenv("MLXLM_RENDERER","")
            if env_spec: print("harmony override (MLXLM_RENDERER):", env_spec)
        except Exception as e:
            print("harmony: extended probe error →", e)
    print("\nIf everything shows a checkmark✅, you're good to run `mlxlm run ...`")

# ----- run (interactive) -----
def run_model(
    model_name,
    chat_mode: str = "auto",
    system_prompt: str = "You are a helpful assistant. Answer concisely and helpfully.",
    reasoning: str | None = None,
    max_tokens: int = 2048,
    stream_mode: str = "all",
    stop: list[str] | None = None,
    time_limit: int = 0,
    history_mode: str = "on",
):
    print(f"🚀 Loading model {model_name}...")
    try:
        model, tokenizer = load(model_name)
    except Exception as e:
        print(f"❌ Failed to load model: {e}"); return
    print("✅ Model loaded. Enter your prompts! Type '/exit' or '/bye' to quit.\n")

    history: list[tuple[str,str]] = []
    sys_prompt = _apply_reasoning_to_system(system_prompt, reasoning)
    remember_assistant = (history_mode == "on") or (os.getenv("MLXLM_REMEMBER_ASSISTANT") == "1")
    if os.getenv("MLXLM_DEBUG") == "1":
        print(f"[DEBUG] History mode: {history_mode} (remember_assistant={remember_assistant})")
        if not remember_assistant:
            print("[DEBUG] Assistant responses will NOT be stored in history (Q&A mode).")

    while True:
        try:
            user_input = input("📝 Prompt: ").strip()
        except EOFError:
            print("\n👋 Bye!")
            break
        if user_input.lower() in ["/exit","/bye"]:
            print("👋 Bye!"); break
        if not user_input: continue
        history.append(("user", user_input))

        try:
            full_prompt = _render_prompt(chat_mode, tokenizer, sys_prompt, history)
        except Exception as e:
            print(f"⚠️  Prompt rendering error ({chat_mode}): {e}")
            full_prompt = f"{system_prompt}\n\nUser: {user_input}\nAssistant:"

        if os.getenv("MLXLM_DEBUG") == "1":
            u_cnt = sum(1 for r,_ in history if r=="user")
            a_cnt = sum(1 for r,_ in history if r=="assistant")
            print(f"[DEBUG] chat_mode={chat_mode} stream_mode={stream_mode} history(user={u_cnt}, assistant={a_cnt})")
            print(f"[DEBUG] rendered_prompt_chars={len(full_prompt)}")

        # RAM estimate（KV）
        try:
            alias_dict_cfg = load_alias_dict()
            cache_key = resolve_to_cache_key(model_name, alias_dict_cfg)
            cfg = load_config_for_model(cache_key) or {}
            if isinstance(cfg.get("text_config"), dict):
                cfg = {**cfg, **cfg["text_config"]}
            layers = cfg.get("num_hidden_layers") or cfg.get("n_layer") or cfg.get("layers") or 0
            hidden = cfg.get("hidden_size") or cfg.get("n_embd") or 0
            prompt_tok = _count_tokens(tokenizer, full_prompt)
            ctx_tok = prompt_tok + int(max_tokens)
            dtype_bytes = int(os.getenv("MLXLM_KV_BYTES","2"))
            if dtype_bytes not in (1,2,4): dtype_bytes=2
            est_bytes = _estimate_kv_bytes(int(layers or 0), int(hidden or 0), int(ctx_tok), dtype_bytes=dtype_bytes)
            print(
                f"\n🧮 Context tokens: prompt≈{prompt_tok}, new≤{max_tokens}, total≤{ctx_tok}\n"
                f"🧠 KV cache est.: {_human_bytes(est_bytes)} (layers={layers or 'unknown'}, hidden={hidden or 'unknown'}, dtype={dtype_bytes*8}-bit)\n"
            )
        except Exception as _e:
            if os.getenv("MLXLM_DEBUG") == "1":
                print(f"[DEBUG] RAM estimate failed: {_e}")

        # stop sequences
        stop_seqs = stop[:] if isinstance(stop, list) else None
        env_stop = os.getenv("MLXLM_STOP", "").strip()
        if env_stop:
            extra = [s.strip() for s in env_stop.split(",") if s.strip()]
            stop_seqs = (stop_seqs or []) + extra
        no_default = os.getenv("MLXLM_NO_DEFAULT_STOPS", "0") == "1"
        if (stop_seqs is None or len(stop_seqs) == 0) and chat_mode == "harmony" and not no_default:
            stop_seqs = ["<|end|>", "<|start|>"]
        if os.getenv("MLXLM_DEBUG") == "1":
            print(f"[DEBUG] stop sequences: {stop_seqs} (no_default={no_default})")

        # generate
        try:
            print("\n🧠 Output:\n", end="", flush=True)
            start_ts = time.time()

            # Helper: try call with stop; if TypeError (unexpected 'stop'), retry without it
            def _call_generate_with_stop(prompt):
                try:
                    return generate(model, tokenizer, prompt, max_tokens=max_tokens, stop=stop_seqs)
                except TypeError as te:
                    if "unexpected keyword argument 'stop'" in str(te):
                        if os.getenv("MLXLM_DEBUG") == "1":
                            print("[DEBUG] generate(): 'stop' not supported by this mlx-lm version → retrying without stop")
                        return generate(model, tokenizer, prompt, max_tokens=max_tokens)
                    raise

            def _iter_stream_with_stop(prompt):
                try:
                    return stream_generate(model, tokenizer, prompt, max_tokens=max_tokens, stop=stop_seqs)
                except TypeError as te:
                    if "unexpected keyword argument 'stop'" in str(te):
                        if os.getenv("MLXLM_DEBUG") == "1":
                            print("[DEBUG] stream_generate(): 'stop' not supported → retrying without stop")
                        return stream_generate(model, tokenizer, prompt, max_tokens=max_tokens)
                    raise

            if stream_mode == "off":
                output = _call_generate_with_stop(full_prompt)
                print(output, end="\n", flush=True)
                if remember_assistant:
                    history.append(("assistant", output))

            elif stream_mode == "final":
                # Stream only the <|channel|>final content in real time
                _buf = [] if remember_assistant else None
                try:
                    token_iter_resp = stream_generate(
                        model, tokenizer, full_prompt, max_tokens=max_tokens, stop=stop_seqs
                    )
                    token_iter = (resp.text for resp in token_iter_resp)
                    for chunk in _stream_final_from_harmony(token_iter):
                        if _buf is not None: _buf.append(chunk)
                        print(chunk, end="", flush=True)
                        if time_limit>0 and (time.time()-start_ts)>time_limit:
                            print("\n⏱️ Time limit reached, stopping.\n", flush=True); break
                except TypeError as te:
                    if "unexpected keyword argument 'stop'" in str(te):
                        if os.getenv("MLXLM_DEBUG") == "1":
                            print("[DEBUG] final-stream: 'stop' failed during iteration → retrying without stop")
                        token_iter_resp = stream_generate(
                            model, tokenizer, full_prompt, max_tokens=max_tokens
                        )
                        token_iter = (resp.text for resp in token_iter_resp)
                        for chunk in _stream_final_from_harmony(token_iter):
                            if _buf is not None: _buf.append(chunk)
                            print(chunk, end="", flush=True)
                            if time_limit>0 and (time.time()-start_ts)>time_limit:
                                print("\n⏱️ Time limit reached, stopping.\n", flush=True); break
                    else:
                        raise
                print("\n")
                if _buf is not None: history.append(("assistant","".join(_buf)))

            else:  # all
                _buf = [] if remember_assistant else None
                tail = ""
                stop_supported = True
                try:
                    stream_it = stream_generate(model, tokenizer, full_prompt, max_tokens=max_tokens, stop=stop_seqs)
                except TypeError as te:
                    if "unexpected keyword argument 'stop'" in str(te):
                        if os.getenv("MLXLM_DEBUG") == "1":
                            print("[DEBUG] stream_generate(): 'stop' not supported → streaming without stop, using marker-based break for Harmony")
                        stop_supported = False
                        stream_it = stream_generate(model, tokenizer, full_prompt, max_tokens=max_tokens)
                    else:
                        raise
                try:
                    for resp in stream_it:
                        if _buf is not None: _buf.append(resp.text)
                        print(resp.text, end="", flush=True)
                        if time_limit>0 and (time.time()-start_ts)>time_limit:
                            print("\n⏱️ Time limit reached, stopping.\n", flush=True); break
                        if not stop_supported and chat_mode == "harmony":
                            tail += resp.text
                            if "<|end|>" in tail or "<|start|>" in tail:
                                break
                            if len(tail) > 256:
                                tail = tail[-128:]
                except TypeError as te:
                    if "unexpected keyword argument 'stop'" in str(te):
                        if os.getenv("MLXLM_DEBUG") == "1":
                            print("[DEBUG] all-stream: 'stop' failed during iteration → retrying without stop")
                        stream_it = stream_generate(model, tokenizer, full_prompt, max_tokens=max_tokens)
                        for resp in stream_it:
                            if _buf is not None: _buf.append(resp.text)
                            print(resp.text, end="", flush=True)
                            if time_limit>0 and (time.time()-start_ts)>time_limit:
                                print("\n⏱️ Time limit reached, stopping.\n", flush=True); break
                    else:
                        raise
                print("\n")
                if _buf is not None: history.append(("assistant","".join(_buf)))
        except Exception as e:
            print(f"\n⚠️ Error generating response: {e}\n")


# ----- alias (interactive + simple subcommands) -----

def _list_cached_models_all():
    """Return all cached HF models that either have a snapshot OR root-level artifacts (config/safetensors/bin).
    Accepts repos like models--<org>--<repo> even when cloned without snapshots.
    """
    model_dir = HF_CACHE_PATH
    models = []
    if os.path.isdir(model_dir):
        for m in os.listdir(model_dir):
            if not m.startswith("models--"):
                continue
            model_path = os.path.join(model_dir, m)
            if not os.path.isdir(model_path):
                continue
            snaps = os.path.join(model_path, "snapshots")
            has_snap = False
            if os.path.isdir(snaps):
                try:
                    has_snap = any(entry.is_dir() for entry in os.scandir(snaps))
                except Exception:
                    has_snap = False
            if has_snap:
                models.append(m)
                continue
            # No snapshots — accept if common artifacts exist at repo root
            try:
                files = os.listdir(model_path)
                if any(f in files for f in ("config.json", "model.safetensors", "model.safetensors.index.json", "pytorch_model.bin", "tokenizer.json", "tokenizer.model")):
                    models.append(m)
            except Exception:
                pass
    return sorted(models)

# --- Sync alias helper ---
def _sync_alias_from_cache():
    """Ensure alias file contains keys for all cached models. New entries get an empty alias string."""
    try:
        models = _list_cached_models_all()
        alias_dict = load_alias_dict()
        changed = False
        for m in models:
            if m not in alias_dict:
                alias_dict[m] = ""
                changed = True
        if changed:
            with open(alias_file_path, "w", encoding="utf-8") as f:
                json.dump(alias_dict, f, indent=2)
            print("📝 Alias file updated from cache (added new models).")
    except Exception as e:
        print(f"⚠️ Failed to sync aliases from cache: {e}")

def alias_interactive():
    """Interactive alias management with add/edit/remove support."""
    _sync_alias_from_cache()

    while True:  # Main loop to allow returning to menu
        models = _list_cached_models_all()
        if not models:
            print("❗ No models found."); return

        alias_dict = load_alias_dict()

        print("🧠 Installed models:\n")
        for i, m in enumerate(models, start=1):
            current_alias = alias_dict.get(m, "")
            model_display = f"{i}. {m}".ljust(70)
            if current_alias:
                print(f"{model_display}  [{current_alias}]")
            else:
                print(f"{model_display}  [No alias]")
        print("0. Exit")
        print("\n💡 Tip: You can type /exit at any time to cancel the operation.\n")

        selected_model = None
        while selected_model is None:
            selected_input = input("\nEnter model number: ").strip()
            if selected_input.lower() == "/exit" or selected_input == "0":
                print("👋 Bye!"); return
            try:
                idx = int(selected_input) - 1
                if 0 <= idx < len(models):
                    selected_model = models[idx]
                else:
                    print("❌ Number out of range. Try again.")
            except ValueError:
                print("❌ Invalid input. Please enter a number.")

        current_alias = alias_dict.get(selected_model, "")

        alias = ""
        while not alias:
            if current_alias:
                prompt_msg = f"Enter new alias to add or change, or leave blank to remove:\n(Current: '{current_alias}')\n> "
            else:
                prompt_msg = "Enter new alias to add or change, or leave blank to remove:\n(Current: [No alias])\n> "

            alias = input(prompt_msg).strip()
            if alias.lower() == "/exit":
                print("👋 Bye!"); return

            # Empty = remove (only if there's a current alias)
            if not alias:
                if current_alias:
                    confirm = input(f"Remove alias '{current_alias}' from '{selected_model}'? [(y)/n]: ").strip().lower()
                    if confirm not in ("", "y", "yes"):
                        print("❌ Operation cancelled. Returning to menu...\n")
                        break  # Return to main menu
                    alias_dict[selected_model] = ""
                    try:
                        with open(alias_file_path, "w", encoding="utf-8") as f:
                            json.dump(alias_dict, f, indent=2)
                        print(f"🧹 Removed alias '{current_alias}'\n")
                    except Exception as e:
                        print(f"❌ Failed to write alias file: {e}\n")
                    break  # Return to main menu
                else:
                    print("❌ No alias to remove. Returning to menu...\n")
                    break  # Return to main menu

        # If we broke out of the alias input loop, continue to main menu
        if not alias:
            continue

        # Check if new alias already exists (except for current model)
        conflict = False
        for model_key, existing_alias in alias_dict.items():
            if existing_alias == alias and model_key != selected_model:
                print(f"❌ Alias '{alias}' already exists for '{model_key}'. Returning to menu...\n")
                conflict = True
                break

        if conflict:
            continue  # Return to main menu

        # Add or edit
        action = "changed" if current_alias else "added"
        confirm = input(f"Assign alias '{alias}' to '{selected_model}'? [(y)/n]: ").strip().lower()
        if confirm not in ("", "y", "yes"):
            print("❌ Operation cancelled. Returning to menu...\n")
            continue  # Return to main menu

        alias_dict[selected_model] = alias
        try:
            with open(alias_file_path, "w", encoding="utf-8") as f:
                json.dump(alias_dict, f, indent=2)
            print(f"✅ Alias '{alias}' {action} successfully!\n")
        except Exception as e:
            print(f"❌ Failed to write alias file: {e}\n")

        # After successful operation, return to main menu
        continue

def alias_main(argv: list[str] | None = None) -> None:
    """Subcommand entrypoint: `mlxlm alias [add/remove/list]` or interactive when no args."""
    argv = argv or []
    _sync_alias_from_cache()
    if len(argv) == 0:
        alias_interactive()
        return

    cmd = argv[0].lower()
    alias_dict = load_alias_dict()

    if cmd == "list":
        if not alias_dict:
            print("(No aliases)"); return
        print("ALIAS".ljust(24), "→", "MODEL NAME")
        for full_name, al in alias_dict.items():
            print(al.ljust(24), "→", full_name)
        return

    if cmd == "add":
        if len(argv) < 3:
            print("❗ Usage: mlxlm alias add <MODEL_OR_ALIAS_OR_CACHEKEY> <ALIAS>")
            return
        target, new_alias = argv[1], argv[2]
        # Resolve to cache key (accept alias, repo_id, or models-- key)
        key = resolve_to_cache_key(target, alias_dict)
        if new_alias in alias_dict.values():
            print(f"❌ Alias '{new_alias}' already exists."); return
        alias_dict[key] = new_alias
        try:
            with open(alias_file_path, "w", encoding="utf-8") as f:
                json.dump(alias_dict, f, indent=2)
            print(f"✅ Added alias '{new_alias}' for '{key}'")
        except Exception as e:
            print(f"❌ Failed to write alias file: {e}")
        return

    if cmd == "edit":
        if len(argv) < 3:
            print("❗ Usage: mlxlm alias edit <OLD_ALIAS> <NEW_ALIAS>")
            return
        old_alias, new_alias = argv[1], argv[2]
        # Find the model with old_alias
        found_key = None
        for full_name, al in alias_dict.items():
            if al == old_alias:
                found_key = full_name
                break
        if not found_key:
            print(f"❓ Alias '{old_alias}' not found."); return
        if new_alias in alias_dict.values():
            print(f"❌ Alias '{new_alias}' already exists."); return
        alias_dict[found_key] = new_alias
        try:
            with open(alias_file_path, "w", encoding="utf-8") as f:
                json.dump(alias_dict, f, indent=2)
            print(f"✅ Changed alias '{old_alias}' → '{new_alias}' for '{found_key}'")
        except Exception as e:
            print(f"❌ Failed to update alias file: {e}")
        return

    if cmd == "remove":
        if len(argv) < 2:
            print("❗ Usage: mlxlm alias remove <ALIAS>")
            return
        target_alias = argv[1]
        removed_key = None
        for full_name, al in list(alias_dict.items()):
            if al == target_alias:
                removed_key = full_name
                alias_dict[full_name] = ""  # Set to empty instead of deleting
                break
        if not removed_key:
            print(f"❓ Alias '{target_alias}' not found."); return
        try:
            with open(alias_file_path, "w", encoding="utf-8") as f:
                json.dump(alias_dict, f, indent=2)
            print(f"🧹 Removed alias '{target_alias}' (was for '{removed_key}')")
        except Exception as e:
            print(f"❌ Failed to update alias file: {e}")
        return

    # Unknown subcommand → fall back to interactive
    alias_interactive()
