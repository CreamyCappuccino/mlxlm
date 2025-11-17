# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""/new command handler for MLX-LM.

Handles creating a new session (saves current, starts fresh).
"""

from datetime import datetime

from core.session_utils import save_session, build_session_data, create_session_id
from .run_utils import _colored


def handle_new_command(
    history: list[tuple[str, str]],
    model_name: str,
    settings: dict,
    session_id: str,
    session_name: str,
    created_at: str
) -> dict:
    """
    Handle /new command - save current session and start a new one.

    Args:
        history: Current conversation history
        model_name: Current model name
        settings: Current session settings
        session_id: Current session ID
        session_name: Current session name
        created_at: Session creation timestamp

    Returns:
        New session data dictionary with:
        - session_id: New session ID
        - session_name: Empty string
        - created_at: New timestamp
        - history: Empty list
        - settings: Same settings as current session
    """
    # Save current session if it has messages
    if history:
        session_data = build_session_data(
            history, model_name, settings, session_id, session_name, created_at
        )
        save_session(session_data)
        print(_colored("💾 Current session saved", "success"))

    # Create new session
    new_session_id = create_session_id()
    new_created_at = datetime.now().isoformat()

    print(_colored("✨ New session started", "success"))

    return {
        'session_id': new_session_id,
        'session_name': '',
        'created_at': new_created_at,
        'history': [],
        'settings': settings
    }
