# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Interactive search interface."""

from __future__ import annotations

import sys

from .search import SearchState, search_huggingface
from .search_display import show_detail
from .search_filters import handle_filters


def search_interactive(query: str, state: SearchState, models: list) -> None:
    """Interactive search interface."""
    state.query = query

    while True:
        # Import here to avoid circular imports
        from .search_display import display_results

        # Display results
        display_results(models, state)

        # Show menu
        print("\nOptions:")
        print("  1-7  Show details")
        print("  8    Next page (/next)")
        print("  9    Filters & Sort (/filter)")
        print("  0    Exit")
        print("\n💡 Tip: You can type /exit, /next, or /filter at any time.\n")

        choice = input("Your choice: ").strip().lower()

        # Handle exit
        if choice in ("0", "/exit", "exit", "q", "quit"):
            print("👋 Bye!")
            return

        # Handle next page
        if choice in ("8", "/next", "next"):
            start_idx = state.page * state.results_per_page
            end_idx = start_idx + state.results_per_page

            # Check if we're already at the last page
            if start_idx + state.results_per_page >= len(models):
                print("\n❗ No more results.")
                continue

            state.page += 1
            continue

        # Handle filters
        if choice in ("9", "/filter", "filter"):
            handle_filters(state)
            # Re-search with new filters/sort
            print("\n🔍 Re-searching with new settings...")
            models = search_huggingface(query, state)
            state.page = 0  # Reset to first page
            continue

        # Handle model selection
        try:
            idx = int(choice) - 1
            start_idx = state.page * state.results_per_page

            if 0 <= idx < state.results_per_page:
                actual_idx = start_idx + idx
                if actual_idx < len(models):
                    model = models[actual_idx]
                    handle_detail_view(model, state)
                else:
                    print("❌ Number out of range. Try again.")
            else:
                print("❌ Invalid selection. Choose 1-7, 8, 9, or 0.")
        except ValueError:
            print("❌ Invalid input. Please enter a number or command.")


def handle_detail_view(model, state: SearchState) -> None:
    """Handle detail view and actions."""
    while True:
        show_detail(model, state)

        choice = input("Choose action: ").strip().lower()

        # Exit
        if choice in ("0", "/exit", "exit"):
            print("👋 Bye!")
            sys.exit(0)

        # Back to results
        if choice == "2":
            return

        # Pull model
        if choice == "1":
            repo_id = model.id
            print(f"\n📥 Pulling {repo_id}...")

            # Import pull_model from commands
            from .pull import pull_model
            pull_model(repo_id)

            # Ask about alias
            alias_choice = input("\nWould you like to set an alias for this model? [(y)/n]: ").strip().lower()
            if alias_choice in ("", "y", "yes"):
                alias_name = input("Enter alias name: ").strip()
                if alias_name:
                    # Import alias functionality
                    from .alias import alias_main
                    from ..core import repo_to_cache_name

                    cache_key = repo_to_cache_name(repo_id)
                    alias_main(["add", cache_key, alias_name])

            print(f"\n✅ You can now run: mlxlm run {repo_id}")
            print("👋 Exiting search...")
            sys.exit(0)

        print("❌ Invalid choice. Choose 1, 2, or 0.")
