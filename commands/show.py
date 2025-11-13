# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Show detailed model information command."""

from __future__ import annotations

import os
import subprocess

from core import HF_CACHE_PATH, load_alias_dict, load_config_for_model


def show_info(model_name: str, full: bool = False) -> None:
    """
    Display detailed information about a specific model.

    Args:
        model_name: Model name, alias, or cache key
        full: If True, display full config.json instead of summary
    """
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
