# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Export conversation functionality for mlxlm run command."""

from .run_utils import _colored


def export_conversation(history: list[tuple[str, str]], filename: str, format: str = 'md', model_name: str = '') -> bool:
    """
    Export conversation history to a file.

    Args:
        history: List of (role, message) tuples
        filename: Output filename
        format: Export format ('md', 'txt', or 'json')
        model_name: Model name for metadata

    Returns:
        bool: True if successful, False otherwise
    """
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        if format == 'md':
            content = f"# MLX-LM Chat Export\n"
            content += f"**Model**: {model_name}\n"
            content += f"**Date**: {timestamp}\n"
            content += f"**Total Turns**: {len(history)}\n\n"
            content += "---\n\n"

            for role, message in history:
                if role == 'user':
                    content += f"### User:\n{message}\n\n"
                else:
                    content += f"### AI:\n{message}\n\n"
                content += "---\n\n"

        elif format == 'txt':
            content = f"MLX-LM Chat Export\n"
            content += f"Model: {model_name}\n"
            content += f"Date: {timestamp}\n"
            content += f"Total Turns: {len(history)}\n\n"
            content += "=" * 80 + "\n\n"

            for role, message in history:
                if role == 'user':
                    content += f"[User]\n{message}\n\n"
                else:
                    content += f"[AI]\n{message}\n\n"
                content += "=" * 80 + "\n\n"

        elif format == 'json':
            import json
            data = {
                "model": model_name,
                "export_date": timestamp,
                "total_turns": len(history),
                "conversation": [
                    {"role": role, "content": message}
                    for role, message in history
                ]
            }
            content = json.dumps(data, indent=2, ensure_ascii=False)

        else:
            print(_colored(f"⚠️  Unknown format: {format}. Use 'md', 'txt', or 'json'.", "error"))
            return False

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)

        print(_colored(f"✅ Exported to {filename}", "success"))
        return True

    except (PermissionError, OSError) as e:
        print(_colored(f"⚠️  Error: Could not export to {filename} ({e})", "error"))
        return False
