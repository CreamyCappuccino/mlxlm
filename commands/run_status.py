# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Status command handler for mlxlm run."""

from .run_utils import _colored


def handle_status_command(
    history: list[tuple[str, str]],
    model_name: str,
    chat_mode: str,
    history_mode: str,
    stream_mode: str,
    max_tokens: int,
    time_limit: int,
    tokenizer,
    sys_prompt: str,
    _render_prompt,
    _count_tokens
) -> None:
    """
    Display current session status.

    Args:
        history: Conversation history
        model_name: Name of the loaded model
        chat_mode: Current chat mode
        history_mode: History mode setting
        stream_mode: Stream mode setting
        max_tokens: Max tokens setting
        time_limit: Time limit setting
        tokenizer: Model tokenizer
        sys_prompt: System prompt
        _render_prompt: Function to render prompts
        _count_tokens: Function to count tokens
    """
    # Calculate statistics
    user_count = sum(1 for r, _ in history if r == "user")
    assistant_count = sum(1 for r, _ in history if r == "assistant")

    # Calculate current token usage
    try:
        full_prompt = _render_prompt(chat_mode, tokenizer, sys_prompt, history)
        current_tokens = _count_tokens(tokenizer, full_prompt)
    except Exception:
        current_tokens = 0

    # Estimate model's context limit (rough estimate)
    estimated_limit = 8192  # Default rough estimate

    status_text = f"""
📊 Current Status:

Model: {model_name}
Chat Mode: {chat_mode}
History Mode: {history_mode}

💬 Conversation:
  User messages: {user_count}
  Assistant messages: {assistant_count}
  Total turns: {len(history)}

🧮 Token Usage:
  Current context: ~{current_tokens} tokens
  Max tokens per response: {max_tokens}
  Estimated limit: ~{estimated_limit} tokens (model dependent)
  Usage: {(current_tokens / estimated_limit * 100):.1f}%

⚙️  Settings:
  Stream mode: {stream_mode}
  Time limit: {time_limit or 'none'} sec
"""
    print(_colored(status_text, "system"))
