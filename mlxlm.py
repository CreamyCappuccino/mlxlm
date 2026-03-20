#!/usr/bin/env python3
# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""mlxlm - Local model management CLI for MLX."""

from __future__ import annotations

__version__ = "0.3.8"

import sys
from cli_flags import build_parser
from core import load_alias_dict, resolve_model_name, _preflight_and_maybe_adjust_chat
from commands import list_models, show_info, pull_model, remove_models, cmd_doctor, run_model, search_main

def main() -> None:
    parser = build_parser()
    try:
        args = parser.parse_args()
    except SystemExit as e:
        # Allow help output (exit code 0) to pass through
        if e.code != 0:
            print("❗ Invalid command or usage.")
            print("💡 Use `mlxlm --help` to view the correct usage.\n")
        sys.exit(e.code)

    if args.command == "help" or not args.command:
        parser.print_help(); sys.exit(0)

    if args.command == "list":
        list_models(show_all=(getattr(args, "scope", None) == "all"))
        return
    if args.command == "show":
        if not getattr(args, "model_name", None):
            print("❗ You must specify a model name or alias for the 'show' command.")
            print("💡 Example: mlxlm show mlx-community--meta-llama--Llama-3-8B-Instruct")
            sys.exit(1)
        alias_dict = load_alias_dict()
        model_name = resolve_model_name(args.model_name, alias_dict)
        show_info(model_name, full=getattr(args,"full",False))
        return
    if args.command == "pull":
        alias_dict = load_alias_dict()
        model_name = resolve_model_name(args.model_name, alias_dict)
        pull_model(model_name); return
    if args.command == "remove":
        remove_models(args.targets, assume_yes=getattr(args,"yes",False), dry_run=getattr(args,"dry_run",False))
        return
    if args.command == "doctor":
        cmd_doctor(); return
    if args.command == "alias":
        from commands import alias_main
        alias_cmd = getattr(args, 'alias_cmd', None)
        if alias_cmd == "add":
            alias_main(["add", args.model, args.alias])
        elif alias_cmd == "edit":
            alias_main(["edit", args.old_alias, args.new_alias])
        elif alias_cmd == "remove":
            alias_main(["remove", args.alias])
        else:
            # No subcommand = interactive mode
            alias_main([])
        return
    if args.command == "search":
        search_main(
            args.query,
            tags=getattr(args, "tags", None),
            max_size=getattr(args, "max_size", None),
            min_downloads=getattr(args, "min_downloads", None),
            updated_within=getattr(args, "updated_within", None),
            param_scale=getattr(args, "param_scale", None),
            param_scale_mode=getattr(args, "param_scale_mode", "eq"),
            param_scale_min=getattr(args, "param_scale_min", None),
            param_scale_max=getattr(args, "param_scale_max", None),
            precision_level=getattr(args, "precision", None),
            precision_method=getattr(args, "method", None),
            sort=getattr(args, "sort", "downloads"),
            limit=getattr(args, "limit", 7),
            hf_limit=getattr(args, "hf_limit", None),
            no_interactive=getattr(args, "no_interactive", False),
            json_output=getattr(args, "json", False),
            help_detail=getattr(args, "help_detail", False),
        )
        return
    if args.command == "run":
        alias_dict = load_alias_dict()
        model_name = resolve_model_name(args.model_name, alias_dict)
        print(f"[DEBUG] Resolved model name: {model_name}")
        desired_chat = getattr(args, "chat", "auto")
        adjusted_chat = _preflight_and_maybe_adjust_chat(desired_chat, model_name, alias_dict)
        run_model(
            model_name,
            chat_mode=adjusted_chat,
            system_prompt=getattr(args, "system", "You are a helpful assistant. Answer concisely and helpfully."),
            reasoning=getattr(args, "reasoning", None),
            max_tokens=getattr(args, "max_tokens", 2048),
            stream_mode=getattr(args, "stream_mode", "all"),
            stop=getattr(args, "stop", None),
            time_limit=getattr(args, "time_limit", 0),
            history_mode=getattr(args, "history", "on"),
        )
        return

if __name__ == "__main__":
    main()
