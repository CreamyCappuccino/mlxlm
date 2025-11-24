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
        print("  N     Next page")
        print("  P     Previous page")
        print("  F     Filters & Sort")
        print("  S     New search")
        print("  D     Display count")
        print("  0     Exit")
        print("\n💡 Tip: Use slash commands for quick actions:")
        print("   /search qwen    /display 20    /search reset    /exit\n")

        choice = input("Your choice: ").strip()

        # Check for slash commands first
        if choice.startswith("/"):
            result = parse_slash_command(choice, query, state, models)
            if result is not None:
                models, query = result
            continue

        # Parse menu choice
        action, param = parse_menu_choice(choice, state.results_per_page)

        if action == "exit":
            print("👋 Bye!")
            return

        if action == "next_page":
            start_idx = state.page * state.results_per_page
            if start_idx + state.results_per_page >= len(models):
                print("\n❗ No more results.")
                continue
            state.page += 1
            continue

        if action == "prev_page":
            if state.page == 0:
                print("\n❗ Already on first page.")
                continue
            state.page -= 1
            continue

        if action == "filters":
            needs_refetch = handle_filters(state)
            if needs_refetch:
                print("\n🔍 Re-searching with new settings...")
                models = search_huggingface(query, state)
            state.page = 0
            continue

        if action == "new_search":
            new_query = input("Enter search query: ").strip()
            if new_query:
                query = new_query
                state.page = 0
                models = search_huggingface(query, state)
            continue

        if action == "set_display_count":
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

        if action == "show_detail":
            start_idx = state.page * state.results_per_page
            actual_idx = start_idx + param
            if actual_idx < len(models):
                model = models[actual_idx]
                handle_detail_view(model, state)
            else:
                print("❌ Number out of range. Try again.")
            continue

        if action == "invalid":
            print(f"❌ Invalid selection. Choose 1-{state.results_per_page}, or n/f/s/d/0, or use slash commands (/search, /display).")


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


def parse_menu_choice(choice: str, max_display: int) -> tuple[str, any]:
    """Parse menu choice and return action type and parameter.

    Returns:
        Tuple of (action, param):
        - ("exit", None) for exit commands
        - ("next_page", None) for next page
        - ("prev_page", None) for previous page
        - ("filters", None) for filters menu
        - ("new_search", None) for new search
        - ("set_display_count", None) for display count change
        - ("show_detail", index) for model selection
        - ("invalid", None) for invalid input
    """
    choice_lower = choice.lower()

    # Exit commands
    if choice_lower in ("0", "exit", "q", "quit"):
        return ("exit", None)

    # Next page
    if choice_lower == "n":
        return ("next_page", None)

    # Previous page
    if choice_lower == "p":
        return ("prev_page", None)

    # Filters menu (uppercase F only)
    if choice_lower == "f":
        return ("filters", None)

    # New search (uppercase S only)
    if choice_lower == "s":
        return ("new_search", None)

    # Display count (uppercase D only)
    if choice_lower == "d":
        return ("set_display_count", None)

    # Model selection (numeric)
    try:
        idx = int(choice) - 1
        if 0 <= idx < max_display:
            return ("show_detail", idx)
        else:
            return ("invalid", None)
    except ValueError:
        return ("invalid", None)


def parse_slash_command(cmd: str, query: str, state: SearchState, models: list) -> tuple | None:
    """Parse slash commands (/search, /display, /exit).

    Returns:
        Tuple of (updated_models, updated_query) if search was performed, None otherwise.
    """
    # /exit and /quit
    if cmd in ("/exit", "/quit"):
        print("👋 Bye!")
        sys.exit(0)

    # /search reset - reset query only
    if cmd == "/search reset":
        state.page = 0
        state.query = ""
        models = search_huggingface("", state)
        print("✅ Query reset. Showing all models...")
        return (models, "")

    # /search or /s <query> - new search
    if cmd.startswith("/search ") or cmd.startswith("/s "):
        # Handle both /search and /s
        prefix_len = 8 if cmd.startswith("/search ") else 3
        new_query = cmd[prefix_len:].strip()
        if new_query:
            state.page = 0
            models = search_huggingface(new_query, state)
            print(f"\n🔍 Searching for '{new_query}'...")
            return (models, new_query)
        else:
            print("❌ Usage: /search <query>")
        return None

    # /display or /d <count> or /display reset - change display count
    if cmd.startswith("/display") or cmd.startswith("/d"):
        parts = cmd.split()
        if len(parts) == 1:
            print("❌ Usage: /display <count> or /display reset")
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
