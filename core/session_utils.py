"""
Session management utilities for MLX-LM.

Handles session data persistence, restoration, and management.
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


def get_sessions_dir() -> Path:
    """
    Get the sessions directory path, creating it if it doesn't exist.

    Returns:
        Path to the sessions directory
    """
    from core import get_mlxlm_data_dir

    session_dir = get_mlxlm_data_dir() / "sessions"
    session_dir.mkdir(exist_ok=True)
    return session_dir


def create_session_id() -> str:
    """
    Generate a unique session ID using UUID v4.

    Returns:
        UUID string (e.g., "550e8400-e29b-41d4-a716-446655440000")
    """
    return str(uuid.uuid4())


def build_session_data(
    history: list[tuple[str, str]],
    model_name: str,
    settings: dict,
    session_id: str,
    session_name: str,
    created_at: Optional[str] = None
) -> dict:
    """
    Build session data dictionary.

    Args:
        history: List of (role, message) tuples in Harmony format
                 e.g., [("user", "hi"), ("assistant", "hello"), ...]
        model_name: Name of the model used
        settings: Session settings dictionary
        session_id: Unique session identifier
        session_name: Session name (empty string if unnamed)
        created_at: ISO 8601 timestamp of creation (or None for new session)

    Returns:
        Session data dictionary
    """
    now = datetime.now().isoformat()

    # Convert Harmony format [("user", msg), ("assistant", resp), ...]
    # to pair format [(msg, resp), ...]
    paired_history = []
    i = 0
    while i < len(history):
        if i + 1 < len(history):
            role1, msg1 = history[i]
            role2, msg2 = history[i + 1]
            if role1 == "user" and role2 == "assistant":
                paired_history.append((msg1, msg2))
                i += 2
            else:
                # Skip malformed entries
                i += 1
        else:
            i += 1

    return {
        "session_id": session_id,
        "created_at": created_at or now,
        "updated_at": now,
        "session_name": session_name,
        "model_name": model_name,
        "settings": settings,
        "history": paired_history,
        "message_count": len(paired_history),
        "archived": False
    }


def save_session(session_data: dict) -> None:
    """
    Save session data to JSON file.

    Args:
        session_data: Session data dictionary
    """
    session_dir = get_sessions_dir()
    session_id = session_data['session_id']
    filepath = session_dir / f"{session_id}.json"

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)


def load_session(session_id: str) -> dict:
    """
    Load session data from JSON file.

    Args:
        session_id: Session identifier

    Returns:
        Session data dictionary

    Raises:
        FileNotFoundError: If session file doesn't exist
    """
    session_dir = get_sessions_dir()
    filepath = session_dir / f"{session_id}.json"

    if not filepath.exists():
        raise FileNotFoundError(f"Session not found: {session_id}")

    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def list_sessions(include_archived: bool = False) -> list[dict]:
    """
    List all saved sessions, sorted by updated_at (newest first).

    Args:
        include_archived: Include archived sessions (default: False)

    Returns:
        List of session data dictionaries
    """
    session_dir = get_sessions_dir()

    sessions = []
    for filepath in session_dir.glob("*.json"):
        # Skip active_session.json
        if filepath.name == "active_session.json":
            continue

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                session = json.load(f)

            # Filter archived sessions
            if not include_archived and session.get('archived', False):
                continue

            sessions.append(session)
        except (json.JSONDecodeError, KeyError):
            # Skip corrupted files
            continue

    # Sort by updated_at (newest first)
    sessions.sort(key=lambda s: s.get('updated_at', ''), reverse=True)

    return sessions


def delete_session(session_id: str) -> None:
    """
    Delete a session file.

    Args:
        session_id: Session identifier
    """
    session_dir = get_sessions_dir()
    filepath = session_dir / f"{session_id}.json"

    if filepath.exists():
        filepath.unlink()


def update_session_name(session_id: str, name: str) -> None:
    """
    Update session name.

    Args:
        session_id: Session identifier
        name: New session name (empty string to clear)
    """
    session = load_session(session_id)
    session['session_name'] = name
    session['updated_at'] = datetime.now().isoformat()
    save_session(session)


def get_session_storage_info() -> dict:
    """
    Get information about session storage.

    Returns:
        Dictionary with:
        - total_sessions: Number of saved sessions
        - storage_mb: Total storage used in MB
        - oldest_date: Relative time of oldest session
    """
    session_dir = get_sessions_dir()

    if not session_dir.exists():
        return {
            'total_sessions': 0,
            'storage_mb': 0.0,
            'oldest_date': 'N/A'
        }

    # Get session files (exclude active_session.json)
    session_files = [
        f for f in session_dir.glob("*.json")
        if f.name != "active_session.json"
    ]

    # Calculate total size
    total_bytes = sum(f.stat().st_size for f in session_files)
    storage_mb = total_bytes / (1024 * 1024)

    # Get oldest session date
    oldest_date = "N/A"
    if session_files:
        try:
            oldest_session = min(
                session_files,
                key=lambda f: json.loads(f.read_text()).get('created_at', '')
            )
            data = json.loads(oldest_session.read_text())
            oldest_date = format_relative_time(data['created_at'])
        except (json.JSONDecodeError, KeyError):
            pass

    return {
        'total_sessions': len(session_files),
        'storage_mb': round(storage_mb, 1),
        'oldest_date': oldest_date
    }


def format_relative_time(timestamp_str: str) -> str:
    """
    Convert ISO 8601 timestamp to relative time string.

    Args:
        timestamp_str: ISO 8601 timestamp (e.g., "2025-01-15T14:30:00")

    Returns:
        Relative time string (e.g., "2 hours ago", "Yesterday 14:30")
    """
    try:
        timestamp = datetime.fromisoformat(timestamp_str)
    except (ValueError, TypeError):
        return timestamp_str

    now = datetime.now()
    delta = now - timestamp

    if delta < timedelta(minutes=1):
        return "just now"
    elif delta < timedelta(hours=1):
        minutes = int(delta.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif delta < timedelta(days=1):
        hours = int(delta.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif delta.days == 1:
        return f"Yesterday {timestamp.strftime('%H:%M')}"
    elif delta < timedelta(days=7):
        days = delta.days
        return f"{days} day{'s' if days > 1 else ''} ago"
    else:
        # 1 week or older: show date
        return timestamp.strftime("%Y-%m-%d %H:%M")
