# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Alias management commands."""

from __future__ import annotations

import os
import json

from core import HF_CACHE_PATH, load_alias_dict, resolve_to_cache_key, alias_file_path


def _list_cached_models_all() -> list[str]:
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


def _sync_alias_from_cache() -> None:
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


def alias_interactive() -> None:
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
