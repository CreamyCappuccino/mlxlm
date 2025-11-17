"""
/save command handler for MLX-LM.

Handles manual session saving.
"""

from core.session_utils import save_session, build_session_data
from .run_utils import _colored


def handle_save_command(
    history: list[tuple[str, str]],
    model_name: str,
    settings: dict,
    session_id: str,
    session_name: str,
    created_at: str
) -> None:
    """
    Handle /save command - save current session immediately.

    Args:
        history: Current conversation history
        model_name: Current model name
        settings: Current session settings
        session_id: Current session ID
        session_name: Current session name
        created_at: Session creation timestamp
    """
    # Build session data
    session_data = build_session_data(
        history, model_name, settings, session_id, session_name, created_at
    )

    # Only save if there are actual completed message pairs
    msg_count = session_data['message_count']

    if msg_count == 0:
        print(_colored("⚠️  No messages to save (empty session)", "warning"))
        return

    # Save to file
    save_session(session_data)

    # Display success message
    updated_time = session_data['updated_at'][:16].replace('T', ' ')

    print(_colored(f"💾 Session saved: {session_id}", "success"))
    print(_colored(
        f"   {msg_count} message{'s' if msg_count != 1 else ''}, "
        f"last updated: {updated_time}",
        "system"
    ))
