"""
/resume command handler for MLX-LM.

Handles session restoration with interactive selection UI.
"""

from typing import Optional

from core.session_utils import (
    list_sessions, save_session, build_session_data, format_relative_time
)
from .run_utils import _colored


def format_session_preview(session: dict, index: int) -> str:
    """
    Format a session for display in the selection list.

    Displays in 2 lines:
    Line 1: Number, relative time, message count, session name (if present)
    Line 2: Preview of first user message (60 chars max)

    Args:
        session: Session data dictionary
        index: Display index (1-based)

    Returns:
        Formatted string (2 lines)
    """
    # Line 1: metadata
    time_str = format_relative_time(session['updated_at'])
    msg_count = session['message_count']
    name = f' | "{session["session_name"]}"' if session['session_name'] else ''
    line1 = f" {index}. {time_str} | {msg_count} message{'s' if msg_count != 1 else ''}{name}"

    # Line 2: message preview
    if session['history']:
        first_message = session['history'][0][0]
        name_prefix = '[No name] ' if not session['session_name'] else ''
        preview = first_message[:60] + "..." if len(first_message) > 60 else first_message
        line2 = f'    {name_prefix}"{preview}"'
    else:
        line2 = '    (Empty session)'

    return f"{line1}\n{line2}"


def select_session_ui(sessions: list[dict]) -> Optional[dict]:
    """
    Display session selection UI and get user choice.

    Args:
        sessions: List of session data dictionaries

    Returns:
        Selected session data or None if cancelled
    """
    # Display header
    print("\n" + "="*60)
    print(_colored(f"📂 Saved Sessions ({len(sessions)} session{'s' if len(sessions) != 1 else ''} found)", "system"))
    print("="*60)

    # Display sessions
    for i, session in enumerate(sessions, 1):
        print(format_session_preview(session, i))
        if i < len(sessions):
            print()  # Blank line between sessions

    # Display footer
    print("="*60)
    print(" 0. Cancel")
    print()

    # Get user choice
    while True:
        try:
            choice = input(_colored(f"Select session (0-{len(sessions)}) or use ↑↓ + Enter: ", "user_prompt")).strip()

            if not choice:
                continue

            choice_num = int(choice)

            if choice_num == 0:
                return None  # Cancelled
            elif 1 <= choice_num <= len(sessions):
                return sessions[choice_num - 1]
            else:
                print(_colored(f"⚠️  Please enter a number between 0 and {len(sessions)}", "warning"))
        except ValueError:
            print(_colored("⚠️  Please enter a valid number", "warning"))
        except (KeyboardInterrupt, EOFError):
            print()
            return None


def handle_resume_command(
    current_history: list[tuple[str, str]],
    current_model: str,
    current_settings: dict,
    current_session_id: str,
    current_session_name: str,
    created_at: str
) -> Optional[dict]:
    """
    Handle /resume command - restore a previous session.

    Saves current session before switching.

    Args:
        current_history: Current conversation history
        current_model: Current model name
        current_settings: Current session settings
        current_session_id: Current session ID
        current_session_name: Current session name
        created_at: Current session creation timestamp

    Returns:
        Selected session data or None if cancelled
    """
    # Get list of saved sessions
    sessions = list_sessions()

    if not sessions:
        print(_colored("📂 No saved sessions found", "warning"))
        return None

    # Display selection UI
    selected_session = select_session_ui(sessions)

    if not selected_session:
        print(_colored("Cancelled", "system"))
        return None

    # Save current session before switching (only if it has messages)
    current_session_data = build_session_data(
        current_history,
        current_model,
        current_settings,
        current_session_id,
        current_session_name,
        created_at
    )

    if current_session_data['message_count'] > 0:
        print(_colored("💾 Saving current session...", "system"))
        save_session(current_session_data)
        print(_colored("✅ Current session saved", "success"))

    # Display success message for loaded session
    print(_colored("📂 Loading session...", "system"))
    msg_count = selected_session['message_count']
    name_display = selected_session['session_name'] or '[No name]'
    print(_colored(
        f"✅ Session restored: {name_display} ({msg_count} message{'s' if msg_count != 1 else ''})",
        "success"
    ))

    return selected_session
