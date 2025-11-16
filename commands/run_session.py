"""
/session command handler for MLX-LM.

Handles session management menu and operations.
"""

from typing import Optional

from core import load_user_config, save_user_config
from core.session_utils import (
    get_session_storage_info, update_session_name,
    delete_session, list_sessions
)
from .run_utils import _colored
from .run_resume import handle_resume_command, format_session_preview


def rename_current_session(session_id: str, current_name: str) -> str:
    """
    Rename current session with interactive prompt.

    Args:
        session_id: Session identifier
        current_name: Current session name (empty string if unnamed)

    Returns:
        New session name
    """
    display_name = current_name if current_name else "[No name]"
    print(f"\nCurrent session name: {display_name}")

    try:
        new_name = input(_colored("Enter new name (or leave blank): ", "user_prompt")).strip()

        # Check if session is saved on disk
        from core.session_utils import get_sessions_dir
        from pathlib import Path
        session_file = get_sessions_dir() / f"{session_id}.json"

        if session_file.exists():
            # Session is saved, update the file
            update_session_name(session_id, new_name)
        else:
            # Session not saved yet, just update in memory (will be saved on exit)
            print(_colored("ℹ️  Session will be saved with this name on exit", "system"))

        if new_name:
            print(_colored(f'✅ Session renamed to "{new_name}"', "success"))
        else:
            print(_colored("✅ Session name cleared", "success"))

        return new_name
    except (KeyboardInterrupt, EOFError):
        print()
        print(_colored("Cancelled", "system"))
        return current_name


def delete_sessions_ui() -> None:
    """
    Display session deletion UI with checkbox-style selection.

    Simple implementation: display sessions and allow single deletion.
    """
    sessions = list_sessions()

    if not sessions:
        print(_colored("📂 No sessions to delete", "warning"))
        return

    # Display header
    print("\n" + "="*60)
    print(_colored("🗑️  Delete Sessions", "system"))
    print("="*60)

    # Display sessions
    for i, session in enumerate(sessions, 1):
        print(format_session_preview(session, i))
        if i < len(sessions):
            print()

    # Display footer
    print("="*60)
    print(" 0. Cancel")
    print()

    # Get user choice
    while True:
        try:
            choice = input(_colored(f"Select session to delete (0-{len(sessions)}): ", "user_prompt")).strip()

            if not choice:
                continue

            choice_num = int(choice)

            if choice_num == 0:
                print(_colored("Cancelled", "system"))
                return
            elif 1 <= choice_num <= len(sessions):
                selected_session = sessions[choice_num - 1]

                # Confirm deletion
                name_display = selected_session['session_name'] or '[No name]'
                confirm = input(_colored(f"Delete session \"{name_display}\"? (y/n): ", "warning")).strip().lower()

                if confirm == 'y':
                    delete_session(selected_session['session_id'])
                    print(_colored("🗑️  Session deleted", "success"))
                else:
                    print(_colored("Cancelled", "system"))
                return
            else:
                print(_colored(f"⚠️  Please enter a number between 0 and {len(sessions)}", "warning"))
        except ValueError:
            print(_colored("⚠️  Please enter a valid number", "warning"))
        except (KeyboardInterrupt, EOFError):
            print()
            print(_colored("Cancelled", "system"))
            return


def edit_autosave_settings() -> None:
    """
    Edit auto-save settings (interval).
    """
    # Load current config
    config = load_user_config()
    current_interval = config.get('sessions', {}).get('auto_save_interval', 300)

    # Display current setting
    if current_interval == 0:
        status = "Disabled"
    else:
        minutes = current_interval // 60
        status = f"Enabled (every {minutes} minutes)"

    print("\n" + "="*60)
    print(_colored("⚙️  Auto-save Settings", "system"))
    print("="*60)
    print(f"Current: {status}\n")
    print(" 1. Enable (5 minutes interval)")
    print(" 2. Enable (10 minutes interval)")
    print(" 3. Disable")
    print("="*60)
    print(" 0. Back")
    print()

    try:
        choice = input(_colored("Select option (0-3): ", "user_prompt")).strip()

        if choice == "1":
            config.setdefault('sessions', {})['auto_save_interval'] = 300
            save_user_config(config)
            print(_colored("✅ Auto-save enabled (5 minutes)", "success"))
        elif choice == "2":
            config.setdefault('sessions', {})['auto_save_interval'] = 600
            save_user_config(config)
            print(_colored("✅ Auto-save enabled (10 minutes)", "success"))
        elif choice == "3":
            config.setdefault('sessions', {})['auto_save_interval'] = 0
            save_user_config(config)
            print(_colored("✅ Auto-save disabled", "success"))
        elif choice == "0":
            return
        else:
            print(_colored("⚠️  Invalid option", "warning"))
    except (KeyboardInterrupt, EOFError):
        print()
        print(_colored("Cancelled", "system"))


def show_session_menu(
    current_history: list[tuple[str, str]],
    current_model: str,
    current_settings: dict,
    current_session_id: str,
    current_session_name: str,
    created_at: str
) -> Optional[dict]:
    """
    Display session management menu.

    Args:
        current_history: Current conversation history
        current_model: Current model name
        current_settings: Current session settings
        current_session_id: Current session ID
        current_session_name: Current session name
        created_at: Current session creation timestamp

    Returns:
        Restored session data if Resume was selected, otherwise None
    """
    while True:
        # Get storage info
        info = get_session_storage_info()

        # Display menu
        print("\n" + "="*60)
        print(_colored("📊 Session Management", "system"))
        print("="*60)
        print(f"Total Sessions:     {info['total_sessions']} session{'s' if info['total_sessions'] != 1 else ''}")
        print(f"Storage Used:       {info['storage_mb']} MB")
        print(f"Oldest Session:     {info['oldest_date']}")
        print()
        print("="*60)
        print(" 1. Resume Session")
        print(" 2. Rename Current Session")
        print(" 3. Delete Sessions")
        print(" 4. Auto-save Settings")
        print("="*60)
        print(" 0. Back")
        print()

        try:
            choice = input(_colored("Select option (0-4): ", "user_prompt")).strip()

            if choice == "1":
                # Resume Session
                restored = handle_resume_command(
                    current_history, current_model, current_settings,
                    current_session_id, current_session_name, created_at
                )
                if restored:
                    return restored  # Session switch

            elif choice == "2":
                # Rename Current Session
                new_name = rename_current_session(current_session_id, current_session_name)
                # Update local variable (caller should handle this)
                current_session_name = new_name

            elif choice == "3":
                # Delete Sessions
                delete_sessions_ui()

            elif choice == "4":
                # Auto-save Settings
                edit_autosave_settings()

            elif choice == "0":
                return None

            else:
                print(_colored("⚠️  Invalid option", "warning"))

        except (KeyboardInterrupt, EOFError):
            print()
            return None

    return None
