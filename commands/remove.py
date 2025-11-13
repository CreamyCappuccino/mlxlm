# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Remove models from local cache command."""

from __future__ import annotations

import os
import json

from core import HF_CACHE_PATH, load_alias_dict, resolve_to_cache_key, alias_file_path


def remove_models(targets: list[str], assume_yes: bool = False, dry_run: bool = False) -> None:
    """
    Remove one or more models from local cache.

    Args:
        targets: List of model identifiers (aliases, repo IDs, or cache keys)
        assume_yes: Skip confirmation prompt if True
        dry_run: Show removal plan without actually deleting if True
    """
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
