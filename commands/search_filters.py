# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Filter and sort functions for search."""

from __future__ import annotations

import re
from typing import Optional

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
    initial_param_scale = state.param_scale
    initial_param_scale_mode = state.param_scale_mode
    initial_param_scale_min = state.param_scale_min
    initial_param_scale_max = state.param_scale_max

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
            state.param_scale = None
            state.param_scale_mode = "eq"
            state.param_scale_min = None
            state.param_scale_max = None
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
        print("  6  Parameter scale (7B, 13B, 30B, etc.)")
        print("  7  Last updated (within X days)")
        print("  8  Clear all filters")
        print("  9  Save current filters as preset")
        print("  10 Load preset")
        print("  11 Delete preset")
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
                state.updated_within_days != initial_updated_within_days or
                state.param_scale != initial_param_scale or
                state.param_scale_mode != initial_param_scale_mode or
                state.param_scale_min != initial_param_scale_min or
                state.param_scale_max != initial_param_scale_max
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

        # Parameter scale (v0.3.5)
        if choice == "6":
            handle_param_scale_filter(state)
            continue

        # Updated within
        if choice == "7":
            handle_updated_filter(state)
            continue

        # Clear all
        if choice == "8":
            confirm = input("\nClear all filters? [(y)/n]: ").strip().lower()
            if confirm in ("", "y", "yes"):
                state.max_size_gb = None
                state.min_downloads = None
                state.tags = []
                state.updated_within_days = None
                state.param_scale = None
                state.param_scale_mode = "eq"
                state.param_scale_min = None
                state.param_scale_max = None
                state.sort_by = "downloads"
                state.sort_direction = "desc"
                print("\n✅ All filters cleared.")
                # Changed, so return True to trigger API re-fetch
                return True
            continue

        # Save preset
        if choice == "9":
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
        if choice == "10":
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
        if choice == "11":
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

        print("❌ Invalid choice. Choose 1-11 or 0.")


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

    # 5. Param scale (v0.3.5: support range)
    if hasattr(state, 'param_scale_mode'):
        if state.param_scale_mode == "range" and (state.param_scale_min or state.param_scale_max):
            param_str = f"range_{state.param_scale_min or 0}b_{state.param_scale_max or 0}b"
            parts.append(param_str)
        elif state.param_scale:
            param_str = f"{state.param_scale}b"
            if state.param_scale_mode == "lt":
                param_str += "_under"
            elif state.param_scale_mode == "gt":
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
    if hasattr(state, 'param_scale_mode'):
        if state.param_scale_mode == "range" and (state.param_scale_min or state.param_scale_max):
            preset_data["param_scale_mode"] = "range"
            preset_data["param_scale_min"] = state.param_scale_min
            preset_data["param_scale_max"] = state.param_scale_max
        elif state.param_scale:
            preset_data["param_scale"] = state.param_scale
            preset_data["param_scale_mode"] = state.param_scale_mode

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
    if hasattr(state, 'param_scale_mode'):
        if preset_data.get("param_scale_mode") == "range":
            state.param_scale_mode = "range"
            state.param_scale_min = preset_data.get("param_scale_min")
            state.param_scale_max = preset_data.get("param_scale_max")
        else:
            state.param_scale = preset_data.get("param_scale")
            state.param_scale_mode = preset_data.get("param_scale_mode", "eq")

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


# ===== Parameter Scale Filter (v0.3.5) =====

def extract_param_scale(model_id: str, card_data: Optional[dict] = None) -> Optional[int]:
    """
    Extract parameter scale (in billions) from model ID and card data.

    Examples:
        "Llama-2-7B" → 7
        "Mistral-7B-v0.1" → 7
        "gemma-3-27b-instruct" → 27
        "7" → 7 (direct integer)

    Supports multiple formats:
        - "27b", "27B", "27-b", "27_b"
        - "27 billion", "27B billion"
        - Direct integers: 27

    Args:
        model_id: The model repository ID (e.g., "meta-llama/Llama-2-7B")
        card_data: Optional model card metadata (for fallback extraction)

    Returns:
        The parameter scale in billions, or None if not found
    """
    if not model_id:
        return None

    # Primary extraction: look for XB pattern in model_id
    # Patterns: 7B, 7b, 7-b, 7_b, 7 billion, 7B billion, etc.
    patterns = [
        r'(\d+)\s*[Bb](?:\s+billion)?',  # 7B, 7b, 7 B, 7 billion, 7B billion
        r'(\d+)[-_][Bb]',                  # 7-b, 7_B
    ]

    for pattern in patterns:
        match = re.search(pattern, model_id)
        if match:
            return int(match.group(1))

    # Fallback: check card_data for model_size, num_parameters, parameters fields
    if card_data and isinstance(card_data, dict):
        # Try model_size field (sometimes contains "7B")
        model_size = card_data.get('model_size')
        if model_size and isinstance(model_size, str):
            match = re.search(r'(\d+)\s*[Bb](?:\s+billion)?', model_size)
            if match:
                return int(match.group(1))

        # Try parameters field
        params = card_data.get('parameters')
        if params and isinstance(params, str):
            match = re.search(r'(\d+)\s*[Bb](?:\s+billion)?', params)
            if match:
                return int(match.group(1))

    return None


def handle_param_scale_filter(state: SearchState) -> None:
    """
    Handle parameter scale filter input from user.

    Prompts for:
    1. Mode selection: eq/lt/gt (single value) or range (min-max)
    2. Value input based on mode selected

    Updates state.param_scale, param_scale_min, param_scale_max, and param_scale_mode.
    """
    print("\n" + "━" * 70)
    print("📊 Parameter Scale Filter")
    print("━" * 70 + "\n")

    # Show current filter
    if state.param_scale_mode == "range" and (state.param_scale_min or state.param_scale_max):
        print(f"Current: Parameters {state.param_scale_min or '?'}B - {state.param_scale_max or '?'}B\n")
    elif state.param_scale:
        op_symbol = {"eq": "=", "lt": "<", "gt": ">"}[state.param_scale_mode]
        print(f"Current: Parameters {op_symbol} {state.param_scale}B\n")
    else:
        print("Current: No parameter scale filter\n")

    print("Common model sizes:")
    print("  7   - Small models (Llama-2-7B, Mistral-7B)")
    print("  13  - Medium models (Llama-2-13B, Mistral-8x7B)")
    print("  27  - Large models (Gemma-27B, Qwen-27B)")
    print("  30  - Very large models (Llama-2-70B, Falcon-180B)")
    print("  70  - Massive models (Falcon-180B)\n")

    # Mode selection
    print("Choose filter mode:")
    print("  1  = (eq)     - Exactly this size")
    print("  2  < (lt)     - Less than this size")
    print("  3  > (gt)     - Greater than or equal to")
    print("  4  range      - Between min and max (inclusive)")
    print("  0  Remove filter\n")

    mode_input = input("Select mode (1/2/3/4) [1]: ").strip().lower()

    if mode_input == "0":
        state.param_scale = None
        state.param_scale_mode = "eq"
        state.param_scale_min = None
        state.param_scale_max = None
        print("\n✅ Parameter scale filter removed.")
        return

    # Range mode
    if mode_input == "4":
        try:
            min_input = input("\nEnter minimum parameter size (e.g., 7): ").strip()
            max_input = input("Enter maximum parameter size (e.g., 13): ").strip()

            if not min_input or not max_input:
                print("❌ Both min and max values are required for range mode.")
                return

            min_val = int(min_input)
            max_val = int(max_input)

            if min_val <= 0 or max_val <= 0:
                print("❌ Values must be greater than 0.")
                return

            if min_val > max_val:
                min_val, max_val = max_val, min_val
                print(f"⚠️  Swapped: now {min_val}B - {max_val}B")

            state.param_scale_mode = "range"
            state.param_scale_min = min_val
            state.param_scale_max = max_val
            state.param_scale = None
            print(f"\n✅ Parameter scale filter set: {min_val}B - {max_val}B (inclusive)")

        except ValueError:
            print("❌ Invalid number. Please enter valid integers.")
        return

    # Single value modes (eq, lt, gt)
    try:
        scale_input = input("\nEnter parameter scale in billions (e.g., 7, 13, 30): ").strip()

        if not scale_input:
            return

        scale = int(scale_input)
        if scale <= 0:
            print("❌ Value must be greater than 0.")
            return

        # Map mode input to compare string
        if mode_input == "2":
            compare = "lt"
        elif mode_input == "3":
            compare = "gt"
        else:
            compare = "eq"

        state.param_scale = scale
        state.param_scale_mode = compare
        state.param_scale_min = None
        state.param_scale_max = None

        op_symbol = {"eq": "=", "lt": "<", "gt": ">"}[compare]
        print(f"\n✅ Parameter scale filter set: {op_symbol} {scale}B")

    except ValueError:
        print("❌ Invalid number. Please enter a valid integer.")
