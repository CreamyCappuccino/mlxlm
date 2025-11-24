# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Interactive search interface."""

from __future__ import annotations

import re
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
        print(f"  1-{state.results_per_page}  Show details")
        print("  n/N   Next page (/next)")
        print("  f/F   Filters & Sort (/filter)")
        print("  s/S   New search (/s <query>)")
        print("  d/D   Display count (/d <num>)")
        print("  0     Exit")
        print("\n💡 Tip: Type /s <keyword>, /d 20, /next, or /filter at any time.\n")

        choice = input("Your choice: ").strip()

        # Check for slash commands first
        if choice.startswith("/"):
            result = parse_slash_command(choice, query, state, models)
            if result is not None:
                models, query = result
            continue

        choice_lower = choice.lower()

        # Handle exit
        if choice_lower in ("0", "exit", "q", "quit"):
            print("👋 Bye!")
            return

        # Handle next page
        if choice_lower in ("n", "next"):
            start_idx = state.page * state.results_per_page
            if start_idx + state.results_per_page >= len(models):
                print("\n❗ No more results.")
                continue
            state.page += 1
            continue

        # Handle filters
        if choice_lower in ("f", "filter"):
            handle_filters(state)
            print("\n🔍 Re-searching with new settings...")
            models = search_huggingface(query, state)
            state.page = 0
            continue

        # Handle new search
        if choice_lower in ("s", "search"):
            new_query = input("Enter search query: ").strip()
            if new_query:
                query = new_query
                state.page = 0
                models = search_huggingface(query, state)
            continue

        # Handle display count change
        if choice_lower in ("d", "display"):
            try:
                count_str = input("Enter display count (or 'reset' for default): ").strip().lower()
                if count_str == "reset":
                    state.results_per_page = 10
                    print("✅ Reset to default (10 models per page)")
                else:
                    count = int(count_str)
                    if count > 0:
                        state.results_per_page = count
                        state.page = 0
                        print(f"✅ Display count set to {count}")
                    else:
                        print("❌ Please enter a positive number.")
            except ValueError:
                print("❌ Invalid input.")
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
                print(f"❌ Invalid selection. Choose 1-{state.results_per_page}, or n/f/s/d/0.")
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


def parse_slash_command(cmd: str, query: str, state: SearchState, models: list) -> tuple | None:
    """Parse slash commands (/s, /d, /next, /filter).

    Returns:
        Tuple of (updated_models, updated_query) if search was performed, None otherwise.
    """
    # /exit and /next are already handled in main loop, but support them here too
    if cmd in ("/exit", "/quit"):
        print("👋 Bye!")
        sys.exit(0)

    if cmd in ("/next", "/n"):
        start_idx = state.page * state.results_per_page
        if start_idx + state.results_per_page >= len(models):
            print("\n❗ No more results.")
        else:
            state.page += 1
            print(f"📄 Page {state.page + 1}")
        return None

    if cmd in ("/filter", "/f"):
        handle_filters(state)
        print("\n🔍 Re-searching with new settings...")
        models = search_huggingface(query, state)
        state.page = 0
        return (models, query)

    # /s <query> - new search
    if cmd.startswith("/s "):
        new_query = cmd[3:].strip()
        if new_query:
            state.page = 0
            models = search_huggingface(new_query, state)
            print(f"\n🔍 Searching for '{new_query}'...")
            return (models, new_query)
        else:
            print("❌ Usage: /s <query>")
        return None

    # /d <num> or /d reset - change display count
    if cmd.startswith("/d"):
        parts = cmd.split()
        if len(parts) == 1:
            print("❌ Usage: /d <count> or /d reset")
            return None

        count_str = parts[1].lower()
        if count_str == "reset":
            state.results_per_page = 10
            state.page = 0
            print("✅ Reset to default (10 models per page)")
        else:
            try:
                count = int(count_str)
                if count > 0:
                    state.results_per_page = count
                    state.page = 0
                    print(f"✅ Display count set to {count}")
                else:
                    print("❌ Please enter a positive number.")
            except ValueError:
                print(f"❌ Invalid count: {count_str}")
        return None

    print(f"❌ Unknown command: {cmd}")
    return None
