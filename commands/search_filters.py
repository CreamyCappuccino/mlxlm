# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Filter and sort functions for search."""

from __future__ import annotations

from .search import SearchState, COMMON_TAGS


def handle_filters(state: SearchState) -> None:
    """Handle filter and sort menu."""
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
        print("  2  Model size (max GB)")
        print("  3  Minimum downloads")
        print("  4  Tags (e.g., mlx, quantized, instruct)")
        print("  5  Last updated (within X days)")
        print("  6  Clear all filters")
        print("  0  Back to results")
        print("\n💡 Tip: You can type /exit at any time to cancel.\n")

        choice = input("Select option: ").strip().lower()

        # Exit
        if choice in ("0", "/exit", "exit"):
            return

        # Sort order
        if choice == "1":
            handle_sort_menu(state)
            continue

        # Max size
        if choice == "2":
            handle_size_filter(state)
            continue

        # Min downloads
        if choice == "3":
            handle_downloads_filter(state)
            continue

        # Tags
        if choice == "4":
            handle_tags_filter(state)
            continue

        # Updated within
        if choice == "5":
            handle_updated_filter(state)
            continue

        # Clear all
        if choice == "6":
            confirm = input("\nClear all filters? [(y)/n]: ").strip().lower()
            if confirm in ("", "y", "yes"):
                state.max_size_gb = None
                state.min_downloads = None
                state.tags = []
                state.updated_within_days = None
                state.sort_by = "downloads"
                print("\n✅ All filters cleared.")
                return  # Back to results
            continue

        print("❌ Invalid choice. Choose 1-6 or 0.")


def handle_sort_menu(state: SearchState) -> None:
    """Handle sort order selection."""
    print("\n" + "━" * 70)
    print("🔄 Sort Order")
    print("━" * 70 + "\n")

    print(f"Current: {state.sort_by.capitalize()}\n")

    print("Sort by:")
    print("  1  Downloads    (most popular first)")
    print("  2  Updated      (most recent first)")
    print("  3  Size         (smallest first)")
    print("  0  Cancel\n")

    choice = input("Your choice: ").strip()

    if choice == "1":
        state.sort_by = "downloads"
        print("\n✅ Sort order changed to: Downloads (most popular first)")
    elif choice == "2":
        state.sort_by = "updated"
        print("\n✅ Sort order changed to: Updated (most recent first)")
    elif choice == "3":
        state.sort_by = "size"
        print("\n✅ Sort order changed to: Size (smallest first)")
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
