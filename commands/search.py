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
        self.sort_direction: str = "desc"  # desc, asc
        self.max_size_gb: Optional[int] = None
        self.min_downloads: Optional[int] = None
        self.tags: list[str] = []
        self.updated_within_days: Optional[int] = None
        self.page: int = 0
        self.results_per_page: int = 10

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


# ===== API Functions =====
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

        # Map internal sort values to HF API sort values
        sort_mapping = {
            "downloads": "downloads",
            "updated": "lastModified",
            "size": "downloads",  # Size sorting done client-side
        }
        hf_sort = sort_mapping.get(state.sort_by, "downloads")

        # Build search parameters
        hf_direction = -1 if state.sort_direction == "desc" else 1  # -1=desc, 1=asc
        # When no tag filter is applied, increase limit to get better representation of all models
        # Otherwise, 100 is sufficient for filtered results
        limit = 500 if not state.tags else 100
        search_params = {
            "search": query,
            "task": "text-generation",
            "sort": hf_sort,
            "direction": hf_direction,
            "limit": limit,
            "expand": ["lastModified", "safetensors", "tags"],  # Request expandable fields
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
            if state.max_size_gb:
                if not model.safetensors:
                    continue  # Models without size data are excluded when size filter is active
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

                    # Use UTC for consistent timezone handling
                    from datetime import timezone
                    if updated.tzinfo is None:
                        updated = updated.replace(tzinfo=timezone.utc)
                        cutoff = datetime.now(timezone.utc) - timedelta(days=state.updated_within_days)
                    else:
                        cutoff = datetime.now(updated.tzinfo) - timedelta(days=state.updated_within_days)

                    if updated < cutoff:
                        continue
                except Exception:
                    pass

            filtered_models.append(model)

        # Client-side sorting for "size" (HF API doesn't support it)
        if state.sort_by == "size":
            # Sort by actual size, pushing models with unknown size to the end
            # In DESC order (large first), N/A should be last → use -inf
            # In ASC order (small first), N/A should be last → use +inf
            def size_sort_key(m):
                if m.safetensors and m.safetensors.get("total"):
                    return m.safetensors.get("total", 0)
                # Unknown size goes to the end in both directions
                return float('-inf') if state.sort_direction == "desc" else float('inf')

            filtered_models.sort(
                key=size_sort_key,
                reverse=(state.sort_direction == "desc")
            )

        return filtered_models

    except Exception as e:
        print(f"❌ Failed to search HuggingFace: {e}")
        print("\n💡 Try:")
        print("  - Check internet connection")
        print("  - Try again later")
        print("  - Visit https://status.huggingface.co/")
        sys.exit(1)


def display_non_interactive(models: list, state: SearchState) -> None:
    """Display search results in non-interactive mode."""
    if not models:
        print("\n❌ No models found matching your search.")
        return

    print(f"\n🔍 Search results for '{state.query}':\n")

    # Show first page only
    page_models = models[:state.results_per_page]

    for i, model in enumerate(page_models, start=1):
        repo_id = model.id
        size = format_size(model.safetensors.get("total") if model.safetensors else None)
        downloads = format_downloads(model.downloads)
        updated = format_updated(str(model.lastModified) if model.lastModified else None)

        print(f"{i}. {repo_id}")
        print(f"   Size: {size} | Downloads: {downloads} | Updated: {updated}")
        print(f"   https://huggingface.co/{repo_id}\n")

    if len(models) > state.results_per_page:
        print(f"(Showing {state.results_per_page} of {len(models)} results)\n")

    print("💡 To pull a model: mlxlm pull <repo-id>")


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
    help_detail: bool = False,
) -> None:
    """Main entry point for search command."""
    # Show detailed help if requested
    if help_detail:
        print("""
mlxlm search - Search HuggingFace for text-generation models

USAGE:
  mlxlm search <query> [options]

ARGUMENTS:
  query                 Search term (e.g., 'llama', 'mistral', 'phi-3', 'qwen')

COMMON OPTIONS:
  --filter-tag TAG      Filter by tag (can be repeated for multiple tags)
                        Common tags: mlx, gguf, quantized, 4-bit, 8-bit, f16, f32
  --max-size GB         Maximum model size in gigabytes (e.g., 10)
  --sort TYPE           Sort results by: downloads, updated, size
                        Default: downloads
  --json                Output as JSON format (for AI agents and scripts)
                        Takes priority over --no-interactive

ADVANCED OPTIONS:
  --min-downloads N     Minimum download count (e.g., 1000, 5000)
  --updated-within DAYS Filter models updated within X days
                        Examples: 7 (last week), 30 (last month), 365 (last year)
  --limit N             Results per page in interactive mode (default: 7)
  --no-interactive      Non-interactive mode: display all results as plain text
                        without pagination menu

EXAMPLES:
  # Basic interactive search
  mlxlm search llama

  # Filter by MLX compatibility
  mlxlm search mistral --filter-tag mlx

  # Multiple filters: small MLX models
  mlxlm search phi --filter-tag mlx --max-size 5

  # Find recently updated quantized models
  mlxlm search qwen --filter-tag quantized --updated-within 30

  # Sort by size, limit results
  mlxlm search gemma --sort size --max-size 10

  # JSON output for AI/scripts (non-interactive)
  mlxlm search llama --json

  # Text output without interactive menu
  mlxlm search mistral --no-interactive

OUTPUT MODES:
  1. Interactive (default)   - Menu-driven with pagination (1-7: select, 8: next, 9: filters, 0: exit)
  2. JSON (--json)            - Structured JSON output for AI agents and scripts
  3. Non-interactive (--no-interactive) - Plain text list without menu

COLOR CODING (interactive mode):
  Green  = MLX-compatible models (mlx, mlx-community tags)
  Yellow = Quantized models (gguf, quantized, 4-bit, 8-bit tags)
  Blue   = Official models (meta-llama, mistralai, google, microsoft, Qwen tags)
  White  = Other models

NOTES:
  - All searches are limited to text-generation task models
  - Size filter requires safetensors metadata (some models may not have this)
  - Sort by 'size' is done client-side (may be slower for large result sets)
  - Tags are case-insensitive and matched partially
        """)
        return

    if not query:
        query = ""  # Empty query shows top models

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

    # Perform search
    models = search_huggingface(query, state)

    # JSON output mode (highest priority)
    if json_output:
        import json as json_module
        output = {
            "query": query,
            "total": len(models),
            "filters": {
                "sort_by": state.sort_by,
                "max_size_gb": state.max_size_gb,
                "min_downloads": state.min_downloads,
                "tags": state.tags,
                "updated_within_days": state.updated_within_days,
            },
            "results": [
                {
                    "repo_id": model.id,
                    "size_bytes": model.safetensors.get("total") if model.safetensors else None,
                    "downloads": model.downloads,
                    "last_modified": str(model.lastModified) if model.lastModified else None,
                    "tags": model.tags or [],
                }
                for model in models[:state.results_per_page * 5]  # Limit to first 5 pages
            ]
        }
        print(json_module.dumps(output, indent=2))
        return

    # Non-interactive mode
    if no_interactive:
        display_non_interactive(models, state)
        return

    # Interactive mode (default)
    from .search_interactive import search_interactive
    search_interactive(query, state, models)
