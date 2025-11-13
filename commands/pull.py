# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Pull (download) models from HuggingFace Hub command."""

from __future__ import annotations

import os

from huggingface_hub import snapshot_download


def pull_model(model_name: str) -> None:
    """
    Download a model from HuggingFace Hub to local cache.

    Args:
        model_name: Repository ID (e.g., 'google/gemma-3-27b-it')
    """
    print(f"🔽 Downloading model '{model_name}' to local cache...")
    try:
        local_dir = snapshot_download(repo_id=model_name)
        print(f"✅ Model downloaded to: {local_dir}")
    except (ConnectionError, TimeoutError, ValueError) as e:
        print(f"❌ Failed to download model: {e}")
        if os.getenv("MLXLM_DEBUG") == "1":
            import traceback
            traceback.print_exc()
