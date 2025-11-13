# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""List installed MLX models command."""

from __future__ import annotations

import os
import subprocess
from datetime import datetime

from core import HF_CACHE_PATH, load_alias_dict


def list_models(show_all: bool = False) -> None:
    """
    Display list of installed MLX models with aliases, sizes, and modification times.

    Args:
        show_all: If True, show all models (currently unused, reserved for future filtering)
    """
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
