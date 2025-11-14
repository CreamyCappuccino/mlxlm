# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Run model in interactive chat mode command."""

from __future__ import annotations

import os
import time

from mlx_lm import load, generate, stream_generate

# prompt-toolkit imports
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import InMemoryHistory, FileHistory
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.formatted_text import ANSI
    from prompt_toolkit.completion import WordCompleter
    from pathlib import Path
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False

from core import (
    load_alias_dict,
    resolve_to_cache_key,
    load_config_for_model,
    _apply_reasoning_to_system,
    _render_prompt,
    _human_bytes,
    _count_tokens,
    _estimate_kv_bytes,
    _stream_final_from_harmony,
)

# ANSI color codes for terminal output
COLORS = {
    'user_prompt': '\033[1;37m',      # Bold white (浅めの灰色に見える)
    'model_output': '\033[97m',       # Bright white
    'error': '\033[91m',              # Bright red
    'success': '\033[92m',            # Bright green
    'warning': '\033[93m',            # Bright yellow
    'reset': '\033[0m',               # Reset
}

def _colored(text: str, color_key: str) -> str:
    """Apply ANSI color to text."""
    return f"{COLORS.get(color_key, '')}{text}{COLORS['reset']}"


def run_model(
    model_name: str,
    chat_mode: str = "auto",
    system_prompt: str = "You are a helpful assistant. Answer concisely and helpfully.",
    reasoning: str | None = None,
    max_tokens: int = 2048,
    stream_mode: str = "all",
    stop: list[str] | None = None,
    time_limit: int = 0,
    history_mode: str = "on",
) -> None:
    """
    Run a model in interactive chat mode.

    Args:
        model_name: Model name, alias, or cache key
        chat_mode: Chat rendering mode ('auto', 'harmony', 'hf', 'plain')
        system_prompt: System prompt text
        reasoning: Reasoning verbosity hint ('low', 'medium', 'high')
        max_tokens: Maximum tokens to generate per turn
        stream_mode: Streaming output mode ('all', 'final', 'off')
        stop: List of stop sequences
        time_limit: Hard time limit per turn in seconds (0=off)
        history_mode: Conversation history mode ('on'=full context, 'off'=Q&A only)
    """
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

    # Initialize prompt session (with fallback to plain input)
    if PROMPT_TOOLKIT_AVAILABLE:
        # Set up history file path (mlxlm_data/input_history)
        project_root = Path(__file__).parent.parent
        data_dir = project_root / "mlxlm_data"
        data_dir.mkdir(exist_ok=True)
        history_file = data_dir / "input_history"

        # Create custom key bindings
        kb = KeyBindings()

        # Option+Enter (Mac) / Alt+Enter (Linux): Insert newline (for multiline input)
        # Note: Shift+Enter is not directly supported in prompt-toolkit
        @kb.add('escape', 'enter')
        def _(event):
            event.current_buffer.insert_text('\n')

        # Also support Ctrl+J for newline (common in terminals)
        @kb.add('c-j')
        def _(event):
            event.current_buffer.insert_text('\n')

        # Option+Up (Mac) / Alt+Up (Linux): Previous history (works in multiline)
        # Note: Command key is not directly supported in prompt-toolkit
        @kb.add('escape', 'up')
        def _(event):
            event.current_buffer.history_backward(count=1)

        # Option+Down (Mac) / Alt+Down (Linux): Next history (works in multiline)
        @kb.add('escape', 'down')
        def _(event):
            event.current_buffer.history_forward(count=1)

        # Create command completer for /exit, /bye
        completer = WordCompleter(['/exit', '/bye'], ignore_case=True)

        session = PromptSession(
            history=FileHistory(str(history_file)),  # Persistent history
            key_bindings=kb,
            completer=completer,
            multiline=False,  # Single-line by default, but Shift+Enter adds newlines
        )
    else:
        session = None

    while True:
        try:
            if session:
                # Use prompt-toolkit for enhanced input experience with colored prompt
                prompt_text = ANSI(_colored("📝 Prompt: ", "user_prompt"))
                user_input = session.prompt(prompt_text).strip()
            else:
                # Fallback to plain input if prompt-toolkit not available
                user_input = input(_colored("📝 Prompt: ", "user_prompt")).strip()
        except KeyboardInterrupt:
            # Ctrl+C: Cancel current input, don't exit
            print(_colored("\n⚠️  Cancelled. Type '/exit' or '/bye' to quit.", "warning"))
            continue
        except EOFError:
            # Ctrl+D: Exit
            print(_colored("\n👋 Bye!", "success"))
            break
        if user_input.lower() in ["/exit","/bye"]:
            print(_colored("👋 Bye!", "success")); break
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
