# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Display and formatting functions for search results."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from .search import Colors, SearchState, OFFICIAL_ORGS


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
        # Parse timestamp with timezone info
        updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))

        # Use UTC for consistent timezone handling
        if updated.tzinfo is None:
            # If no timezone info, assume UTC
            from datetime import timezone
            updated = updated.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
        else:
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

        # If model name is too long, use 2-line display
        MAX_NAME_WIDTH = 50
        if len(repo_id) > MAX_NAME_WIDTH:
            # Line 1: Number + Model name only
            print(f" {i}  {model_display}")
            # Line 2: Metadata aligned to column positions
            # Indent = " " + "i" + "  " = 4 chars, then MODEL NAME column (50 chars)
            indent = " " * (4 + MAX_NAME_WIDTH)
            print(f"{indent} {size:<10} {downloads:<12} {updated}")
        else:
            # Normal single-line display
            # Account for ANSI color codes in padding
            padding = MAX_NAME_WIDTH - len(repo_id)
            print(f" {i}  {model_display}{' ' * padding} {size:<10} {downloads:<12} {updated}")

    # Footer
    filter_summary = "Filters: " + (", ".join(state.get_filter_summary()) if state.has_filters() else "none")
    direction = "↓" if state.sort_direction == "desc" else "↑"
    print(f"\n (Showing {showing_start}-{showing_end} of {total_models} | Sorted by: {state.sort_by.capitalize()} {direction} | {filter_summary})")

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
