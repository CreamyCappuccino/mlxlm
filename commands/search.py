# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Search HuggingFace for models."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from typing import Optional

try:
    from huggingface_hub import HfApi
except ImportError:
    HfApi = None


# ===== ANSI Color Codes =====
class Colors:
    GREEN = '\033[92m'    # MLX models
    YELLOW = '\033[93m'   # Quantized models
    BLUE = '\033[94m'     # Official models
    CYAN = '\033[96m'     # Highlights
    RESET = '\033[0m'     # Reset
    BOLD = '\033[1m'      # Bold


# ===== Common Tags =====
COMMON_TAGS = {
    "mlx": "MLX-optimized models",
    "quantized": "Compressed models",
    "4bit": "4-bit quantization",
    "8bit": "8-bit quantization",
    "instruct": "Instruction-tuned",
    "chat": "Chat models",
    "gguf": "GGUF format",
    "awq": "AWQ quantization",
    "gptq": "GPTQ quantization",
    "text-generation": "Text generation",
    "conversational": "Conversational AI",
    "code": "Code generation",
}

OFFICIAL_ORGS = [
    "meta-llama", "google", "microsoft", "facebook", "openai",
    "mistralai", "anthropic", "EleutherAI", "bigscience"
]


# ===== Filter State =====
class SearchState:
    """Manages search filters and sort settings."""

    def __init__(self):
        self.query: str = ""
        self.sort_by: str = "downloads"  # downloads, updated, size
        self.max_size_gb: Optional[int] = None
        self.min_downloads: Optional[int] = None
        self.tags: list[str] = []
        self.updated_within_days: Optional[int] = None
        self.page: int = 0
        self.results_per_page: int = 7

    def has_filters(self) -> bool:
        """Check if any filters are active."""
        return bool(
            self.max_size_gb or
            self.min_downloads or
            self.tags or
            self.updated_within_days
        )

    def get_filter_summary(self) -> list[str]:
        """Get a list of active filters for display."""
        filters = []
        if self.max_size_gb:
            filters.append(f"Max size: {self.max_size_gb} GB")
        if self.min_downloads:
            filters.append(f"Min downloads: {self.min_downloads:,}")
        if self.tags:
            filters.append(f"Tags: {', '.join(self.tags)}")
        if self.updated_within_days:
            filters.append(f"Updated within: {self.updated_within_days} days")
        return filters


# ===== Helper Functions =====
def get_model_color(tags: list[str], repo_id: str) -> str:
    """Determine color for model based on tags and repo."""
    tags_lower = [t.lower() for t in tags]

    # Priority: MLX > Quantized > Official > Default
    if "mlx" in tags_lower:
        return Colors.GREEN

    if any(tag in tags_lower for tag in ["quantized", "4bit", "8bit", "awq", "gptq", "gguf"]):
        return Colors.YELLOW

    org = repo_id.split("/")[0] if "/" in repo_id else ""
    if org in OFFICIAL_ORGS:
        return Colors.BLUE

    return Colors.RESET


def format_size(size_bytes: Optional[int]) -> str:
    """Format size in bytes to human-readable format."""
    if size_bytes is None:
        return "N/A"

    gb = size_bytes / (1024 ** 3)
    if gb >= 1:
        return f"{gb:.1f} GB"

    mb = size_bytes / (1024 ** 2)
    if mb >= 1:
        return f"{mb:.1f} MB"

    kb = size_bytes / 1024
    return f"{kb:.1f} KB"


def format_downloads(downloads: Optional[int]) -> str:
    """Format download count to human-readable format."""
    if downloads is None:
        return "N/A"

    if downloads >= 1000:
        return f"{downloads / 1000:.1f}k"

    return str(downloads)


def format_updated(updated_at: Optional[str]) -> str:
    """Format last updated timestamp to relative time."""
    if not updated_at:
        return "N/A"

    try:
        updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        now = datetime.now(updated.tzinfo)
        delta = now - updated

        if delta.days == 0:
            return "Today"
        elif delta.days == 1:
            return "Yesterday"
        elif delta.days < 7:
            return f"{delta.days} days ago"
        elif delta.days < 30:
            weeks = delta.days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        elif delta.days < 365:
            months = delta.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        else:
            years = delta.days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"
    except Exception:
        return "N/A"


def search_huggingface(query: str, state: SearchState) -> list[dict]:
    """Search HuggingFace for models."""
    if HfApi is None:
        print("❌ huggingface_hub is not installed.")
        print("💡 Install: pip install huggingface_hub")
        sys.exit(1)

    if os.getenv("MLXLM_OFFLINE") == "1":
        print("❌ Search requires internet connection.")
        print("   (MLXLM_OFFLINE=1 is set)")
        print("\n💡 Try: mlxlm list (to see installed models)")
        sys.exit(1)

    try:
        api = HfApi()

        # Build search parameters
        search_params = {
            "search": query,
            "task": "text-generation",
            "sort": state.sort_by,
            "direction": -1,  # Descending
            "limit": 100,  # Get more for filtering
        }

        # Add tag filters
        if state.tags:
            search_params["filter"] = state.tags

        print(f"🔍 Searching HuggingFace for '{query}'...")

        models = list(api.list_models(**search_params))

        # Apply additional filters
        filtered_models = []
        for model in models:
            # Size filter
            if state.max_size_gb and model.safetensors:
                total_size = model.safetensors.get("total", 0)
                if total_size > state.max_size_gb * (1024 ** 3):
                    continue

            # Downloads filter
            if state.min_downloads and (model.downloads or 0) < state.min_downloads:
                continue

            # Updated filter
            if state.updated_within_days and model.lastModified:
                try:
                    updated = datetime.fromisoformat(str(model.lastModified).replace("Z", "+00:00"))
                    cutoff = datetime.now(updated.tzinfo) - timedelta(days=state.updated_within_days)
                    if updated < cutoff:
                        continue
                except Exception:
                    pass

            filtered_models.append(model)

        return filtered_models

    except Exception as e:
        print(f"❌ Failed to search HuggingFace: {e}")
        print("\n💡 Try:")
        print("  - Check internet connection")
        print("  - Try again later")
        print("  - Visit https://status.huggingface.co/")
        sys.exit(1)


def display_results(models: list, state: SearchState) -> None:
    """Display search results with pagination."""
    if not models:
        print("\n❌ No models found matching your search.")
        print("\n💡 Tips:")
        print("  - Check spelling")
        print("  - Try broader terms (e.g., 'llama' instead of 'llama-3.1')")
        print("  - Adjust or remove filters")
        return

    # Pagination
    start_idx = state.page * state.results_per_page
    end_idx = start_idx + state.results_per_page
    page_models = models[start_idx:end_idx]

    total_models = len(models)
    showing_start = start_idx + 1
    showing_end = min(end_idx, total_models)

    # Header
    print(f"\n🔍 Found {total_models} model{'s' if total_models != 1 else ''} matching '{state.query}':\n")

    # Column headers
    print(f" #  {'MODEL NAME':<50} {'SIZE':<10} {'DOWNLOADS':<12} UPDATED")

    # Results
    for i, model in enumerate(page_models, start=1):
        repo_id = model.id
        tags = model.tags or []
        color = get_model_color(tags, repo_id)

        size = format_size(model.safetensors.get("total") if model.safetensors else None)
        downloads = format_downloads(model.downloads)
        updated = format_updated(str(model.lastModified) if model.lastModified else None)

        # Format with color
        model_display = f"{color}{repo_id}{Colors.RESET}"
        # Account for ANSI color codes in padding
        padding = 50 - len(repo_id)
        print(f" {i}  {model_display}{' ' * padding} {size:<10} {downloads:<12} {updated}")

    # Footer
    filter_summary = "Filters: " + (", ".join(state.get_filter_summary()) if state.has_filters() else "none")
    print(f"\n (Showing {showing_start}-{showing_end} of {total_models} | Sorted by: {state.sort_by.capitalize()} | {filter_summary})")

    # Legend
    print(f"\nLegend: [{Colors.GREEN}Green=MLX{Colors.RESET}] [{Colors.YELLOW}Yellow=Quantized{Colors.RESET}] [{Colors.BLUE}Blue=Official{Colors.RESET}]")


def show_detail(model, state: SearchState) -> None:
    """Show detailed information for a model."""
    repo_id = model.id
    tags = model.tags or []

    print("\n" + "━" * 70)
    print(f"📦 {repo_id}")
    print("━" * 70 + "\n")

    # Basic info
    print(f"Description    : {model.cardData.get('description', 'N/A') if model.cardData else 'N/A'}")

    size = format_size(model.safetensors.get("total") if model.safetensors else None)
    print(f"Size           : {size}")

    # Try to get architecture from config
    arch = "N/A"
    if model.cardData and isinstance(model.cardData, dict):
        arch_list = model.cardData.get("architectures", [])
        if arch_list:
            arch = arch_list[0]
    print(f"Architecture   : {arch}")

    print(f"License        : {model.cardData.get('license', 'N/A') if model.cardData else 'N/A'}")
    print(f"Downloads      : {model.downloads:,}" if model.downloads else "Downloads      : N/A")
    print(f"Last updated   : {format_updated(str(model.lastModified)) if model.lastModified else 'N/A'}")

    if tags:
        print(f"Tags           : {', '.join(tags[:10])}")  # Limit to 10 tags

    print(f"\n🔗 https://huggingface.co/{repo_id}")

    print("\nActions:")
    print("  1  Pull this model")
    print("  2  Back to results")
    print("  0  Exit")
    print("\n💡 Tip: You can type /exit at any time to cancel.\n")


def search_interactive(query: str, state: SearchState) -> None:
    """Interactive search interface."""
    state.query = query

    # Perform search
    models = search_huggingface(query, state)

    while True:
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

            if end_idx >= len(models):
                print("\n❗ No more results.")
                continue

            state.page += 1
            continue

        # Handle filters
        if choice in ("9", "/filter", "filter"):
            handle_filters(state)
            # Re-search with new filters
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
            from commands.pull import pull_model
            pull_model(repo_id)

            # Ask about alias
            alias_choice = input("\nWould you like to set an alias for this model? [(y)/n]: ").strip().lower()
            if alias_choice in ("", "y", "yes"):
                alias_name = input("Enter alias name: ").strip()
                if alias_name:
                    # Import alias functionality
                    from commands.alias import alias_main
                    from core import repo_to_cache_name

                    cache_key = repo_to_cache_name(repo_id)
                    alias_main(["add", cache_key, alias_name])

            print(f"\n✅ You can now run: mlxlm run {repo_id}")
            print("👋 Exiting search...")
            sys.exit(0)

        print("❌ Invalid choice. Choose 1, 2, or 0.")


def handle_filters(state: SearchState) -> None:
    """Handle filter and sort menu."""
    # TODO: Implement filter menu (Phase 3)
    print("\n🚧 Filter & Sort menu coming in Phase 3...")
    input("\nPress Enter to continue...")


def search_main(
    query: str,
    tags: Optional[list[str]] = None,
    max_size: Optional[int] = None,
    min_downloads: Optional[int] = None,
    updated_within: Optional[int] = None,
    sort: str = "downloads",
    limit: int = 7,
    no_interactive: bool = False,
    json_output: bool = False,
) -> None:
    """Main entry point for search command."""
    if not query:
        print("❌ Search query required.")
        print("\nUsage:")
        print("  mlxlm search <query> [options]")
        print("\nExample:")
        print("  mlxlm search llama")
        print("  mlxlm search mistral --max-size 10")
        sys.exit(1)

    # Initialize state
    state = SearchState()
    state.results_per_page = limit
    state.sort_by = sort

    # Apply CLI flags
    if tags:
        state.tags = tags
    if max_size:
        state.max_size_gb = max_size
    if min_downloads:
        state.min_downloads = min_downloads
    if updated_within:
        state.updated_within_days = updated_within

    # TODO: Implement non-interactive and JSON modes (Phase 6)
    if no_interactive or json_output:
        print("\n🚧 Non-interactive and JSON modes coming in Phase 6...")
        return

    search_interactive(query, state)
