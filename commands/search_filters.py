# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Filter and sort functions for search."""

from __future__ import annotations

from .search import SearchState, COMMON_TAGS


def handle_filters(state: SearchState) -> bool:
    """Handle filter and sort menu.

    Returns:
        True if any filters/sort settings changed (API re-fetch needed), False otherwise.
    """
    # Save initial state to detect changes
    initial_sort_by = state.sort_by
    initial_sort_direction = state.sort_direction
    initial_tags = state.tags.copy()
    initial_max_size_gb = state.max_size_gb
    initial_min_downloads = state.min_downloads
    initial_updated_within_days = state.updated_within_days

    # Show current filters and ask if user wants to keep them
    if state.has_filters() or state.sort_by != "downloads":
        print("\n" + "━" * 70)
        print("🔍 Current Filters & Sort")
        print("━" * 70 + "\n")

        settings = []
        settings.append(f"Sort by: {state.sort_by.capitalize()}")
        settings.extend(state.get_filter_summary())

        for setting in settings:
            print(f"  • {setting}")

        keep = input("\nKeep these settings? [(y)/n]: ").strip().lower()
        if keep in ("n", "no"):
            # Clear all filters
            state.max_size_gb = None
            state.min_downloads = None
            state.tags = []
            state.updated_within_days = None
            state.sort_by = "downloads"
            print("\n✅ All settings cleared.")

    # Show filter menu
    while True:
        print("\n" + "━" * 70)
        print("🔍 Filters & Sort")
        print("━" * 70 + "\n")

        if state.has_filters() or state.sort_by != "downloads":
            print("Current settings:")
            print(f"  • Sort by: {state.sort_by.capitalize()}")
            for filter_text in state.get_filter_summary():
                print(f"  • {filter_text}")
            print()
        else:
            print("(No filters applied)\n")

        print("Available options:")
        print("  1  Sort order (downloads/updated/size)")
        print("  2  Sort direction (ascending/descending)")
        print("  3  Model size (max GB)")
        print("  4  Minimum downloads")
        print("  5  Tags (e.g., mlx, quantized, instruct)")
        print("  6  Last updated (within X days)")
        print("  7  Clear all filters")
        print("  8  Save current filters as preset")
        print("  9  Load preset")
        print("  10 Delete preset")
        print("  0  Back to results")
        print("\n💡 Tip: You can type /exit at any time to cancel.\n")

        choice = input("Select option: ").strip().lower()

        # Exit
        if choice in ("0", "/exit", "exit"):
            # Check if any settings changed
            changed = (
                state.sort_by != initial_sort_by or
                state.sort_direction != initial_sort_direction or
                state.tags != initial_tags or
                state.max_size_gb != initial_max_size_gb or
                state.min_downloads != initial_min_downloads or
                state.updated_within_days != initial_updated_within_days
            )
            return changed

        # Sort order
        if choice == "1":
            handle_sort_menu(state)
            continue

        # Sort direction
        if choice == "2":
            handle_sort_direction_menu(state)
            continue

        # Max size
        if choice == "3":
            handle_size_filter(state)
            continue

        # Min downloads
        if choice == "4":
            handle_downloads_filter(state)
            continue

        # Tags
        if choice == "5":
            handle_tags_filter(state)
            continue

        # Updated within
        if choice == "6":
            handle_updated_filter(state)
            continue

        # Clear all
        if choice == "7":
            confirm = input("\nClear all filters? [(y)/n]: ").strip().lower()
            if confirm in ("", "y", "yes"):
                state.max_size_gb = None
                state.min_downloads = None
                state.tags = []
                state.updated_within_days = None
                state.sort_by = "downloads"
                state.sort_direction = "desc"
                print("\n✅ All filters cleared.")
                # Changed, so return True to trigger API re-fetch
                return True
            continue

        # Save preset
        if choice == "8":
            print("\n" + "━" * 70)
            print("💾 Save as Preset")
            print("━" * 70 + "\n")
            auto_name = auto_generate_preset_name(state)
            user_name = input(f"Confirm or enter custom name [{auto_name}]: ").strip()
            preset_name = user_name if user_name else auto_name

            if save_preset(preset_name, state):
                print(f"✅ Preset '{preset_name}' saved!")
            else:
                print(f"❌ Failed to save preset '{preset_name}'")
            continue

        # Load preset
        if choice == "9":
            presets = list_presets()
            if not presets:
                print("\n❌ No presets available. Save one first!")
                continue

            print("\n" + "━" * 70)
            print("📚 Load Preset")
            print("━" * 70 + "\n")

            preset_list = list(presets.keys())
            for i, preset_name in enumerate(preset_list, 1):
                preset_data = presets[preset_name]
                # Display preset summary
                summary_parts = []
                if preset_data.get("sort_by"):
                    summary_parts.append(f"Sort: {preset_data['sort_by']}")
                if preset_data.get("max_size_gb"):
                    summary_parts.append(f"Size: max {preset_data['max_size_gb']} GB")
                if preset_data.get("tags"):
                    summary_parts.append(f"Tags: {', '.join(preset_data['tags'])}")
                summary = ", ".join(summary_parts) if summary_parts else "(no filters)"
                print(f"  {i}  {preset_name} ({summary})")

            print("  0  Cancel\n")

            try:
                choice_str = input("Select preset: ").strip()
                if choice_str == "0":
                    continue
                idx = int(choice_str) - 1
                if 0 <= idx < len(preset_list):
                    preset_name = preset_list[idx]
                    if load_preset(preset_name, state):
                        print(f"✅ Preset '{preset_name}' loaded!")
                        # Return True to trigger API re-fetch with new filters
                        return True
                    else:
                        print(f"❌ Failed to load preset '{preset_name}'")
                else:
                    print("❌ Invalid preset number")
            except ValueError:
                print("❌ Invalid input")
            continue

        # Delete preset
        if choice == "10":
            presets = list_presets()
            if not presets:
                print("\n❌ No presets available.")
                continue

            print("\n" + "━" * 70)
            print("🗑️  Delete Preset")
            print("━" * 70 + "\n")

            preset_list = list(presets.keys())
            for i, preset_name in enumerate(preset_list, 1):
                print(f"  {i}  {preset_name}")

            print("  0  Cancel\n")

            try:
                choice_str = input("Select preset to delete: ").strip()
                if choice_str == "0":
                    continue
                idx = int(choice_str) - 1
                if 0 <= idx < len(preset_list):
                    preset_name = preset_list[idx]
                    confirm = input(f"\nDelete '{preset_name}'? [y/N]: ").strip().lower()
                    if confirm in ("y", "yes"):
                        if delete_preset(preset_name):
                            print(f"✅ Preset '{preset_name}' deleted.")
                        else:
                            print(f"❌ Failed to delete preset '{preset_name}'")
                else:
                    print("❌ Invalid preset number")
            except ValueError:
                print("❌ Invalid input")
            continue

        print("❌ Invalid choice. Choose 1-10 or 0.")


def handle_sort_menu(state: SearchState) -> None:
    """Handle sort order selection."""
    print("\n" + "━" * 70)
    print("🔄 Sort Order")
    print("━" * 70 + "\n")

    print(f"Current: {state.sort_by.capitalize()}\n")

    print("Sort by:")
    print("  1  Downloads    (popularity)")
    print("  2  Updated      (recency)")
    print("  3  Size         (file size)")
    print("  0  Cancel\n")

    choice = input("Your choice: ").strip()

    if choice == "1":
        state.sort_by = "downloads"
        print("\n✅ Sort order changed to: Downloads")
    elif choice == "2":
        state.sort_by = "updated"
        print("\n✅ Sort order changed to: Updated")
    elif choice == "3":
        state.sort_by = "size"
        print("\n✅ Sort order changed to: Size")
    elif choice == "0":
        return
    else:
        print("❌ Invalid choice.")


def handle_sort_direction_menu(state: SearchState) -> None:
    """Handle sort direction selection (ascending/descending)."""
    print("\n" + "━" * 70)
    print("📊 Sort Direction")
    print("━" * 70 + "\n")

    current_dir = "Descending (↓)" if state.sort_direction == "desc" else "Ascending (↑)"
    print(f"Current: {current_dir}\n")

    print("Sort direction:")
    print("  1  Descending   (↓ largest/most popular/newest first)")
    print("  2  Ascending    (↑ smallest/least popular/oldest first)")
    print("  0  Cancel\n")

    choice = input("Your choice: ").strip()

    if choice == "1":
        state.sort_direction = "desc"
        print("\n✅ Sort direction changed to: Descending (↓)")
    elif choice == "2":
        state.sort_direction = "asc"
        print("\n✅ Sort direction changed to: Ascending (↑)")
    elif choice == "0":
        return
    else:
        print("❌ Invalid choice.")


def handle_size_filter(state: SearchState) -> None:
    """Handle model size filter."""
    print("\n" + "━" * 70)
    print("💾 Model Size Filter")
    print("━" * 70 + "\n")

    if state.max_size_gb:
        print(f"Current: Max {state.max_size_gb} GB\n")
    else:
        print("Current: No size limit\n")

    print("Enter maximum model size in GB (or 0 to remove filter):\n")
    print("Examples:")
    print("  5   - Small models (quantized, mobile-friendly)")
    print("  10  - Medium models (8B models, 4-bit)")
    print("  20  - Large models (13B models, quantized)")
    print("  50  - Very large models (30B+, 4-bit)")
    print("  100 - Extra large models (70B+)\n")

    size_input = input("Max size (GB): ").strip()

    if not size_input:
        return

    try:
        max_size = int(size_input)
        if max_size <= 0:
            state.max_size_gb = None
            print("\n✅ Size filter removed.")
        else:
            state.max_size_gb = max_size
            print(f"\n✅ Max size set to {max_size} GB")
    except ValueError:
        print("❌ Invalid number.")


def handle_downloads_filter(state: SearchState) -> None:
    """Handle minimum downloads filter."""
    print("\n" + "━" * 70)
    print("📊 Downloads Filter")
    print("━" * 70 + "\n")

    if state.min_downloads:
        print(f"Current: Min {state.min_downloads:,} downloads\n")
    else:
        print("Current: No download minimum\n")

    print("Enter minimum downloads (or 0 to remove filter):\n")
    print("Examples:")
    print("  100    - Any popular model")
    print("  1000   - Well-tested models")
    print("  5000   - Popular models")
    print("  10000  - Very popular models\n")

    downloads_input = input("Min downloads: ").strip()

    if not downloads_input:
        return

    try:
        min_downloads = int(downloads_input)
        if min_downloads <= 0:
            state.min_downloads = None
            print("\n✅ Downloads filter removed.")
        else:
            state.min_downloads = min_downloads
            print(f"\n✅ Min downloads set to {min_downloads:,}")
    except ValueError:
        print("❌ Invalid number.")


def handle_tags_filter(state: SearchState) -> None:
    """Handle tags filter with selection menu."""
    print("\n" + "━" * 70)
    print("📌 Tag Filter")
    print("━" * 70 + "\n")

    if state.tags:
        print(f"Current tags: {', '.join(state.tags)}\n")
    else:
        print("Current tags: None\n")

    print("Available tags:")
    tag_list = list(COMMON_TAGS.keys())
    for i, tag in enumerate(tag_list, start=1):
        description = COMMON_TAGS[tag]
        print(f"  {i:2d}  {tag:<15}  ({description})")
    print("   0  Back\n")

    print("Select tags (comma-separated, e.g., 1,2,3) or 0 to cancel:\n")

    choice = input("Your choice: ").strip()

    if choice == "0" or not choice:
        return

    # Parse comma-separated numbers
    try:
        indices = [int(x.strip()) - 1 for x in choice.split(",") if x.strip()]
        selected_tags = []
        for idx in indices:
            if 0 <= idx < len(tag_list):
                selected_tags.append(tag_list[idx])

        if selected_tags:
            state.tags = selected_tags
            print(f"\n✅ Tags updated: {', '.join(selected_tags)}")
        else:
            print("❌ No valid tags selected.")
    except ValueError:
        print("❌ Invalid input. Use comma-separated numbers (e.g., 1,2,3)")


def handle_updated_filter(state: SearchState) -> None:
    """Handle last updated filter."""
    print("\n" + "━" * 70)
    print("📅 Last Updated Filter")
    print("━" * 70 + "\n")

    if state.updated_within_days:
        print(f"Current: Within {state.updated_within_days} days\n")
    else:
        print("Current: Any time\n")

    print("Updated within:")
    print("  1  7 days       (this week)")
    print("  2  30 days      (this month)")
    print("  3  90 days      (last 3 months)")
    print("  4  180 days     (last 6 months)")
    print("  5  365 days     (this year)")
    print("  6  Any time     (remove filter)")
    print("  0  Cancel\n")

    choice = input("Your choice: ").strip()

    if choice == "1":
        state.updated_within_days = 7
        print("\n✅ Filter set to: Updated within 7 days")
    elif choice == "2":
        state.updated_within_days = 30
        print("\n✅ Filter set to: Updated within 30 days")
    elif choice == "3":
        state.updated_within_days = 90
        print("\n✅ Filter set to: Updated within 90 days")
    elif choice == "4":
        state.updated_within_days = 180
        print("\n✅ Filter set to: Updated within 180 days")
    elif choice == "5":
        state.updated_within_days = 365
        print("\n✅ Filter set to: Updated within 365 days")
    elif choice == "6":
        state.updated_within_days = None
        print("\n✅ Filter removed (showing all models)")
    elif choice == "0":
        return
    else:
        print("❌ Invalid choice.")


# ===== Preset Management (v0.3.4) =====

def auto_generate_preset_name(state: SearchState) -> str:
    """
    Auto-generate a meaningful preset name from filter state (v0.3.5 compatible).
    Includes all active filter information for clarity.

    Order: tags → size → min_downloads → updated_days → param_scale → sort_by → sort_direction
    Fallback: timestamp-based name if no filters
    """
    from datetime import datetime

    parts = []

    # 1. All tags (joined with underscore)
    if state.tags:
        parts.append("_".join(tag.lower() for tag in state.tags))

    # 2. Size
    if state.max_size_gb:
        parts.append(f"{int(state.max_size_gb)}gb")

    # 3. Min downloads
    if state.min_downloads:
        parts.append(f"{int(state.min_downloads)}downloads")

    # 4. Updated within days
    if state.updated_within_days:
        parts.append(f"updated{int(state.updated_within_days)}d")

    # 5. Param scale (v0.3.5 compatibility)
    if hasattr(state, 'param_scale') and state.param_scale:
        param_str = f"{state.param_scale}b"
        if hasattr(state, 'param_compare'):
            if state.param_compare == "lt":
                param_str += "_under"
            elif state.param_compare == "gt":
                param_str += "_over"
        parts.append(param_str)

    # 6. Sort order (if not default downloads)
    if state.sort_by != "downloads":
        parts.append(f"by_{state.sort_by}")

    # 7. Sort direction (if not default desc)
    if state.sort_direction != "desc":
        parts.append(state.sort_direction)

    # Fallback: timestamp
    if not parts:
        return f"preset_{datetime.now().strftime('%m%d_%H%M')}"

    return "_".join(parts)


def save_preset(preset_name: str, state: SearchState) -> bool:
    """Save current filter state as a preset."""
    from core import load_user_config, save_user_config

    user_config = load_user_config()
    if 'search' not in user_config:
        user_config['search'] = {}
    if 'presets' not in user_config['search']:
        user_config['search']['presets'] = {}

    # Save filter state
    preset_data = {
        "sort_by": state.sort_by,
        "sort_direction": state.sort_direction,
    }

    # Optional fields (only save if set)
    if state.max_size_gb:
        preset_data["max_size_gb"] = state.max_size_gb
    if state.min_downloads:
        preset_data["min_downloads"] = state.min_downloads
    if state.tags:
        preset_data["tags"] = state.tags
    if state.updated_within_days:
        preset_data["updated_within_days"] = state.updated_within_days

    # v0.3.5 compatibility
    if hasattr(state, 'param_scale') and state.param_scale:
        preset_data["param_scale"] = state.param_scale
    if hasattr(state, 'param_compare') and state.param_compare:
        preset_data["param_compare"] = state.param_compare

    user_config['search']['presets'][preset_name] = preset_data
    return save_user_config(user_config)


def load_preset(preset_name: str, state: SearchState) -> bool:
    """Load a preset into current filter state."""
    from core import load_user_config

    user_config = load_user_config()
    if 'search' not in user_config or 'presets' not in user_config['search']:
        return False

    preset_data = user_config['search']['presets'].get(preset_name)
    if not preset_data:
        return False

    # Restore filter state
    state.sort_by = preset_data.get("sort_by", "downloads")
    state.sort_direction = preset_data.get("sort_direction", "desc")
    state.max_size_gb = preset_data.get("max_size_gb")
    state.min_downloads = preset_data.get("min_downloads")
    state.tags = preset_data.get("tags", [])
    state.updated_within_days = preset_data.get("updated_within_days")

    # v0.3.5 compatibility
    if hasattr(state, 'param_scale'):
        state.param_scale = preset_data.get("param_scale")
    if hasattr(state, 'param_compare'):
        state.param_compare = preset_data.get("param_compare")

    state.page = 0
    return True


def list_presets() -> dict:
    """Get all saved presets."""
    from core import load_user_config

    user_config = load_user_config()
    return user_config.get('search', {}).get('presets', {})


def delete_preset(preset_name: str) -> bool:
    """Delete a preset."""
    from core import load_user_config, save_user_config

    user_config = load_user_config()
    if 'search' not in user_config or 'presets' not in user_config['search']:
        return False

    if preset_name in user_config['search']['presets']:
        del user_config['search']['presets'][preset_name]
        return save_user_config(user_config)

    return False
