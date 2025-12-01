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
        self.param_scale: Optional[int] = None  # v0.3.5: parameter scale single value (7, 13, 30)
        self.param_scale_mode: str = "eq"  # eq, lt, gt, range (v0.3.5)
        self.param_scale_min: Optional[int] = None  # v0.3.5: min for range mode
        self.param_scale_max: Optional[int] = None  # v0.3.5: max for range mode
        self.precision_level: Optional[int] = None  # v0.3.6: model precision level (2, 3, 4, 5, 6, 8, 16, 32)
        self.precision_method: Optional[str] = None  # v0.3.6: quantization method (awq, gptq, gguf, mlx)
        self.page: int = 0
        self.results_per_page: int = 10
        self.search_cache: dict = {}  # Session-based cache for empty-query precision searches
        self.search_type: str = "or"  # "or" (default) or "and" (+ or , delimited)
        self.search_keywords: list[str] = []  # Parsed keywords for AND/OR filtering
        self.exclude_keywords: list[str] = []  # Keywords to exclude (! or - prefix)

    def has_filters(self) -> bool:
        """Check if any filters are active."""
        param_filter_active = (
            self.param_scale or
            (self.param_scale_mode == "range" and (self.param_scale_min or self.param_scale_max))
        )
        precision_filter_active = self.precision_level or self.precision_method
        return bool(
            self.max_size_gb or
            self.min_downloads or
            self.tags or
            self.updated_within_days or
            param_filter_active or
            precision_filter_active
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
        if self.param_scale_mode == "range" and (self.param_scale_min is not None or self.param_scale_max is not None):
            filters.append(f"Parameters: {self.param_scale_min}B - {self.param_scale_max}B")
        elif self.param_scale and self.param_scale_mode in ["eq", "lt", "gt"]:
            op_symbol = {"eq": "=", "lt": "<", "gt": ">"}[self.param_scale_mode]
            filters.append(f"Parameters: {op_symbol} {self.param_scale}B")
        if self.precision_level:
            precision_str = f"Precision: {self.precision_level}-bit"
            if self.precision_method:
                precision_str += f" ({self.precision_method.upper()})"
            filters.append(precision_str)
        elif self.precision_method:
            filters.append(f"Precision: Any level ({self.precision_method.upper()})")
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


# ===== Query Parsing =====
def parse_search_query(query: str, state: SearchState) -> None:
    """Parse search query for AND/OR/exclude operators.

    Sets state.search_type, state.search_keywords, and state.exclude_keywords based on query format:
    - "qwen kimi" (space) → OR search (default)
    - "qwen+kimi" or "qwen+llama" → AND search
    - "qwen,kimi" or "qwen,llama" → AND search
    - "!qwen" or "-qwen" → exclude qwen from results
    - Combined: "llama+mistral !qwen" → (llama AND mistral) excluding qwen
    - Mixed: "gpt,20B,!120B" → (gpt AND 20B) excluding 120B
    """
    if not query:
        state.search_type = "or"
        state.search_keywords = []
        state.exclude_keywords = []
        return

    # Strip backslash escapes added by zsh for ! (e.g., '\!qwen' → '!qwen')
    query = query.replace(r'\!', '!')

    # First, extract exclude keywords (! or - prefix) from the entire query
    # This handles both space-separated and comma-separated formats
    exclude_kws = []

    # Handle space-separated exclude keywords (e.g., "qwen !120B")
    parts = query.split()
    search_parts = []

    for part in parts:
        if part.startswith("!") or part.startswith("-"):
            # Exclude keyword with prefix
            exclude_kws.append(part[1:])
        else:
            search_parts.append(part)

    # Also handle exclude keywords in comma/plus separated lists
    # e.g., "gpt,!120B" or "llama+!qwen"
    cleaned_parts = []
    for part in search_parts:
        # Split by comma and plus to extract exclude keywords
        if "," in part or "+" in part:
            # Reconstruct the part, extracting exclude keywords
            tokens = []
            for token in part.replace("+", ",").split(","):
                token = token.strip()
                if token.startswith("!") or token.startswith("-"):
                    exclude_kws.append(token[1:])
                else:
                    tokens.append(token)
            cleaned_parts.append(",".join(tokens) if "," in part else "+".join(tokens))
        else:
            cleaned_parts.append(part)

    state.exclude_keywords = exclude_kws

    # Now parse the search keywords (AND/OR)
    search_query = " ".join(cleaned_parts).strip()

    if not search_query:
        state.search_type = "or"
        state.search_keywords = []
        return

    # Determine search type and extract keywords
    if "+" in search_query and "," not in search_query:
        # AND search with + delimiter (only +, no ,)
        state.search_type = "and"
        state.search_keywords = [kw.strip() for kw in search_query.split("+") if kw.strip()]
    elif "," in search_query:
        # AND search with , delimiter (comma takes precedence)
        state.search_type = "and"
        state.search_keywords = [kw.strip() for kw in search_query.split(",") if kw.strip()]
    else:
        # OR search (space delimiter, default)
        state.search_type = "or"
        state.search_keywords = [kw.strip() for kw in search_query.split() if kw.strip()]


# ===== API Functions =====
def do_precision_search(query: str, state: SearchState) -> list[dict]:
    """
    Perform search with precision filter supplementation and session caching.

    If precision filter is set and initial results are limited,
    search with precision keywords to ensure comprehensive coverage
    across all naming conventions (16bit, fp16, bf16, etc.).

    For empty queries with precision filters, results are cached in-memory
    to reduce API usage during the session.

    Args:
        query: Search query string
        state: SearchState object with filter settings

    Returns:
        List of model dictionaries matching the search and filters
    """
    # Check cache for empty-query precision searches
    if not query and state.precision_level:
        cache_key = (state.precision_level, state.precision_method)
        if cache_key in state.search_cache:
            print("💾 Using cached results from this session")
            return state.search_cache[cache_key]

    # Perform initial search
    models = search_huggingface(query, state)

    # Supplementary precision keyword search
    # If precision filter is set and initial results are limited, search with precision keywords
    # to ensure comprehensive coverage across all naming conventions (16bit, fp16, bf16, etc.)
    if state.precision_level:
        from .search_filters import PRECISION_KEYWORDS
        threshold = 20  # If fewer than 20 models, try augmenting with precision keywords

        if len(models) < threshold:
            keywords = PRECISION_KEYWORDS.get(state.precision_level, [])
            supplementary_models = {}

            print(f"💡 Augmenting results with precision keywords: {', '.join(keywords)}")

            for keyword in keywords:
                # Skip keyword if it matches the original query
                if query and keyword.lower() in query.lower():
                    continue

                try:
                    # Search with precision keyword
                    keyword_results = search_huggingface(keyword, state)

                    # Add new models (by ID) to supplementary set, avoiding duplicates
                    for model in keyword_results:
                        if model.id not in {m.id for m in models}:
                            supplementary_models[model.id] = model
                except Exception:
                    # If individual keyword search fails, continue with others
                    continue

            # Merge supplementary models with original results
            if supplementary_models:
                models.extend(list(supplementary_models.values()))
                print(f"✅ Added {len(supplementary_models)} supplementary models")

    # Cache results for empty-query precision searches
    if not query and state.precision_level:
        cache_key = (state.precision_level, state.precision_method)
        state.search_cache[cache_key] = models
        print("💾 Results cached for this session")

    return models


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
        # Otherwise, use a lower limit for filtered results
        # Default: 500 (no tags), 100 (with tags) - can be customized via state.hf_search_limit
        default_limit = getattr(state, 'hf_search_limit', None) or (500 if not state.tags else 100)
        limit = default_limit
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
        from .search_filters import extract_param_scale

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

            # Parameter scale filter (v0.3.5)
            if state.param_scale_mode == "range" and (state.param_scale_min or state.param_scale_max):
                model_params = extract_param_scale(model.id, getattr(model, 'cardData', None))
                if model_params is None:
                    continue  # Models with unknown parameter scale are excluded when param filter is active

                if state.param_scale_min and model_params < state.param_scale_min:
                    continue
                if state.param_scale_max and model_params > state.param_scale_max:
                    continue
            elif state.param_scale and state.param_scale_mode in ["eq", "lt", "gt"]:
                model_params = extract_param_scale(model.id, getattr(model, 'cardData', None))
                if model_params is None:
                    continue  # Models with unknown parameter scale are excluded when param filter is active

                if state.param_scale_mode == "eq" and model_params != state.param_scale:
                    continue
                elif state.param_scale_mode == "lt" and model_params >= state.param_scale:
                    continue
                elif state.param_scale_mode == "gt" and model_params <= state.param_scale:
                    continue

            # Model precision filter (v0.3.6)
            if state.precision_level or state.precision_method:
                from .search_filters import extract_precision_info
                precision_info = extract_precision_info(model.id, tags=model.tags)

                # If precision_level is set, model must match that level
                if state.precision_level:
                    if precision_info.get('precision_level') != state.precision_level:
                        continue

                # If precision_method is set (optionally), model must match that method
                if state.precision_method:
                    if precision_info.get('method') != state.precision_method:
                        continue

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

        # Apply AND filtering if search_type is "and"
        if state.search_type == "and" and state.search_keywords:
            filtered_models = [
                m for m in filtered_models
                if all(kw.lower() in m.id.lower() for kw in state.search_keywords)
            ]

        # Apply exclude filtering
        if state.exclude_keywords:
            filtered_models = [
                m for m in filtered_models
                if not any(kw.lower() in m.id.lower() for kw in state.exclude_keywords)
            ]

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
    param_scale: Optional[int] = None,
    param_scale_mode: str = "eq",
    param_scale_min: Optional[int] = None,
    param_scale_max: Optional[int] = None,
    precision_level: Optional[int] = None,
    precision_method: Optional[str] = None,
    sort: str = "downloads",
    limit: int = 7,
    hf_limit: Optional[int] = None,
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

ADVANCED SEARCH SYNTAX:
  AND search:     llama+mistral       Find models with both llama and mistral
  OR search:      llama mistral       Find models with llama OR mistral (default with spaces)
  Exclude:        llama !qwen         Find llama models but exclude qwen
                  (use ! or - prefix)
  Combined:       llama+mistral !qwen (llama AND mistral) excluding qwen

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

  # Advanced search examples
  mlxlm search "llama+mistral"        Find models with both llama and mistral
  mlxlm search "llama !qwen"          Find llama models excluding qwen
  mlxlm search "qwen mistral !gpt"    Find qwen OR mistral, excluding gpt

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

  IMPORTANT: When using special characters (!, +, etc.) in CLI, use quotes to prevent shell expansion:
    ✓ Correct:   mlxlm search "llama !qwen"
                 mlxlm search "gpt+mistral"
    ✗ Incorrect: mlxlm search llama !qwen     (shell expands !)
                 mlxlm search gpt+mistral     (may cause issues in some shells)
        """)
        return

    if not query:
        query = ""  # Empty query shows top models

    # Load user config for search settings
    from core import load_user_config
    user_config = load_user_config()
    search_config = user_config.get('search', {})

    # Apply saved default_display_count if limit is at default (10)
    if limit == 10:  # Default value indicates no explicit --limit flag
        limit = search_config.get('default_display_count', 10)

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
    if param_scale:
        state.param_scale = param_scale
        state.param_scale_mode = param_scale_mode
    if param_scale_min:
        state.param_scale_min = param_scale_min
        state.param_scale_mode = "range"
    if param_scale_max:
        state.param_scale_max = param_scale_max
        if state.param_scale_mode != "range":
            state.param_scale_mode = "range"
    if precision_level:
        state.precision_level = precision_level
    if precision_method:
        state.precision_method = precision_method
    if hf_limit:
        state.hf_search_limit = hf_limit

    # Parse query for AND/OR operators
    parse_search_query(query, state)

    # Handle exclude-only queries (e.g., "!qwen")
    if not state.search_keywords and state.exclude_keywords:
        # Search with empty query to get all models, then apply exclude filter
        api_query = ""
        models = do_precision_search(api_query, state)
        print(f"🔍 Searching all models, excluding: {', '.join(state.exclude_keywords)}")
    # Handle OR search with multiple keywords (search each keyword and merge results)
    elif state.search_type == "or" and len(state.search_keywords) > 1:
        models_dict = {}
        print(f"🔍 OR search: Searching for {', '.join(state.search_keywords)}...")

        for keyword in state.search_keywords:
            try:
                keyword_models = do_precision_search(keyword, state)
                for model in keyword_models:
                    if model.id not in models_dict:
                        models_dict[model.id] = model
            except Exception:
                continue

        models = list(models_dict.values())
        print(f"✅ Merged {len(models)} unique models from OR search")
    else:
        # For AND search, use only the first keyword for HuggingFace API
        # (API will perform OR search, then we filter with AND logic client-side)
        api_query = state.search_keywords[0] if (state.search_type == "and" and state.search_keywords) else query

        # Perform search (with precision filter supplementation if applicable)
        models = do_precision_search(api_query, state)

    # JSON output mode (highest priority)
    if json_output:
        import json as json_module
        filters_dict = {
            "sort_by": state.sort_by,
            "max_size_gb": state.max_size_gb,
            "min_downloads": state.min_downloads,
            "tags": state.tags,
            "updated_within_days": state.updated_within_days,
        }
        if state.param_scale_mode == "range":
            filters_dict["param_scale_mode"] = "range"
            filters_dict["param_scale_min"] = state.param_scale_min
            filters_dict["param_scale_max"] = state.param_scale_max
        else:
            filters_dict["param_scale"] = state.param_scale
            filters_dict["param_scale_mode"] = state.param_scale_mode
        if state.precision_level:
            filters_dict["precision_level"] = state.precision_level
        if state.precision_method:
            filters_dict["precision_method"] = state.precision_method

        output = {
            "query": query,
            "total": len(models),
            "filters": filters_dict,
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
