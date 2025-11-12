# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Command-line argument parser and flag definitions for mlxlm."""

from __future__ import annotations

import argparse

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="mlxlm: Local model management tool for MLX")
    subparsers = parser.add_subparsers(dest="command")

    list_parser = subparsers.add_parser("list", help="Show list of installed models")
    list_parser.add_argument("scope", nargs="?", choices=["all"], help="Show all orgs (use: mlxlm list all)")

    show_parser = subparsers.add_parser("show", help="Show info for specified model")
    show_parser.add_argument("model_name", nargs='?', help="Name of the model to inspect")
    show_parser.add_argument("--full", action="store_true", help="Show full config.json instead of summary")

    pull_parser = subparsers.add_parser("pull", help="Download a model to the cache")
    pull_parser.add_argument("model_name", help="Repo ID or alias of the model to download")

    remove_parser = subparsers.add_parser("remove", help="Delete cached model(s) by alias, repo_id, or cache key")
    remove_parser.add_argument("targets", nargs="+", help="One or more model identifiers to remove")
    remove_parser.add_argument("--yes", action="store_true", help="Do not prompt for confirmation")
    remove_parser.add_argument("--dry-run", action="store_true", help="Show what would be removed without deleting")

    run_parser = subparsers.add_parser("run", help="Run specified model")
    run_parser.add_argument("model_name")
    run_parser.add_argument("--chat", choices=["auto","harmony","hf","plain"], default="auto",
                            help="Chat rendering: official Harmony, HF chat_template, or plain. 'auto' tries harmony→hf→plain.")
    run_parser.add_argument("--system", default="You are a helpful assistant. Answer concisely and helpfully.",
                            help="System prompt text")
    run_parser.add_argument("--reasoning", choices=["low","medium","high"], default=None,
                            help="Hint to reduce or increase reasoning verbosity")
    run_parser.add_argument("--max-tokens", type=int, default=2048,
                            help="Max new tokens to generate per turn (default 2048)")
    run_parser.add_argument("--stream-mode", choices=["all","final","off"], default="all",
                            help="Streaming display: 'all' prints raw stream, 'final' prints only the <|channel|>final in real time, 'off' disables streaming")
    run_parser.add_argument("--stop", action="append", default=None,
                            help="Add a stop sequence (can be repeated). For Harmony, defaults to <|end|> and <|start|> when not provided.")
    run_parser.add_argument("--time-limit", type=int, default=0,
                            help="Hard time limit per turn in seconds (0=off)")
    run_parser.add_argument("--history", choices=["on","off"], default="on",
                            help="Enable conversation history (on=remember assistant responses, off=Q&A mode only)")

    alias_parser = subparsers.add_parser("alias", help="Manage model aliases")
    alias_subparsers = alias_parser.add_subparsers(dest="alias_cmd")

    add_parser = alias_subparsers.add_parser("add", help="Add alias for a model")
    add_parser.add_argument("model", help="Model name, alias, or cache key")
    add_parser.add_argument("alias", help="New alias name")

    edit_parser = alias_subparsers.add_parser("edit", help="Edit existing alias")
    edit_parser.add_argument("old_alias", help="Current alias name to change")
    edit_parser.add_argument("new_alias", help="New alias name")

    remove_parser = alias_subparsers.add_parser("remove", help="Remove alias (set to empty)")
    remove_parser.add_argument("alias", help="Alias name to remove")

    subparsers.add_parser("doctor", help="Diagnose environment (MLX/Harmony/HF cache)")
    subparsers.add_parser("help", help="Show this help message and exit")
    return parser
