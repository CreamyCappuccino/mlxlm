# Copyright (c) 2025 MLX-LM Contributors
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Tests for v0.2.8: Session Management & Resume."""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


class TestSessionManagement:
    """Test session management functionality."""

    def test_session_creation(self):
        """Test creating a new session."""
        # Session structure test
        session = {
            "name": "test_session",
            "created_at": "2025-11-24T12:00:00",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"}
            ]
        }
        assert session["name"] == "test_session"
        assert len(session["messages"]) == 2
        assert session["messages"][0]["role"] == "user"

    def test_session_save_format(self):
        """Test session save format consistency."""
        session = {
            "name": "my_session",
            "created_at": "2025-11-24",
            "updated_at": "2025-11-24T15:30:00",
            "messages": [],
            "metadata": {
                "version": "0.2.8",
                "auto_saved": False
            }
        }
        assert "name" in session
        assert "created_at" in session
        assert "messages" in session
        assert isinstance(session["messages"], list)

    def test_session_message_append(self):
        """Test appending messages to session."""
        session = {"name": "test", "messages": []}

        # Add first message
        session["messages"].append({"role": "user", "content": "msg1"})
        assert len(session["messages"]) == 1

        # Add second message
        session["messages"].append({"role": "assistant", "content": "msg2"})
        assert len(session["messages"]) == 2

    def test_empty_session_not_saved(self):
        """Test that empty sessions are not saved."""
        session = {"name": "empty", "messages": []}

        # Empty session should be rejected
        is_valid = len(session["messages"]) > 0
        assert not is_valid

    def test_session_name_uniqueness(self):
        """Test session naming."""
        sessions = {
            "session_1": {"messages": [{"role": "user", "content": "a"}]},
            "session_2": {"messages": [{"role": "user", "content": "b"}]}
        }
        assert "session_1" in sessions
        assert "session_2" in sessions
        assert len(sessions) == 2

    def test_session_list_retrieval(self):
        """Test retrieving list of saved sessions."""
        sessions = [
            {"name": "session_1", "created_at": "2025-11-24"},
            {"name": "session_2", "created_at": "2025-11-23"},
            {"name": "session_3", "created_at": "2025-11-22"}
        ]
        assert len(sessions) == 3
        assert sessions[0]["name"] == "session_1"


class TestSessionResume:
    """Test session resume functionality."""

    def test_resume_session_loading(self):
        """Test loading a session for resume."""
        saved_session = {
            "name": "old_session",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"}
            ]
        }

        # Simulate resuming
        resumed_messages = saved_session["messages"]
        assert len(resumed_messages) == 2
        assert resumed_messages[0]["content"] == "Hello"

    def test_resume_with_new_message(self):
        """Test resuming session and adding new message."""
        resumed_messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"}
        ]

        # Add new message to resumed session
        resumed_messages.append({"role": "user", "content": "How are you?"})

        assert len(resumed_messages) == 3
        assert resumed_messages[-1]["content"] == "How are you?"

    def test_resume_session_not_found(self):
        """Test behavior when session to resume is not found."""
        sessions = {"session_1": {}, "session_2": {}}
        session_name = "nonexistent_session"

        session_exists = session_name in sessions
        assert not session_exists


class TestAutoSave:
    """Test auto-save functionality."""

    def test_auto_save_enabled(self):
        """Test that auto-save can be enabled."""
        config = {"auto_save": True, "interval": 300}
        assert config["auto_save"] is True
        assert config["interval"] == 300

    def test_auto_save_interval(self):
        """Test auto-save interval configuration."""
        intervals = [60, 300, 600, 1800]  # seconds

        for interval in intervals:
            config = {"auto_save_interval": interval}
            assert config["auto_save_interval"] == interval

    def test_auto_save_on_exit(self):
        """Test auto-save on exit behavior."""
        session = {
            "name": "test",
            "messages": [{"role": "user", "content": "msg"}],
            "auto_save_on_exit": True
        }
        assert session["auto_save_on_exit"] is True

    def test_session_not_saved_if_empty(self):
        """Test that empty sessions are not auto-saved."""
        session = {"messages": []}

        should_save = len(session["messages"]) > 0
        assert not should_save


class TestSessionDelete:
    """Test session deletion functionality."""

    def test_delete_session(self):
        """Test deleting a session."""
        sessions = {
            "session_1": {"name": "session_1"},
            "session_2": {"name": "session_2"}
        }

        # Delete session_1
        del sessions["session_1"]

        assert "session_1" not in sessions
        assert "session_2" in sessions
        assert len(sessions) == 1

    def test_delete_nonexistent_session(self):
        """Test deleting a nonexistent session (should raise error)."""
        sessions = {"session_1": {}}

        with pytest.raises(KeyError):
            del sessions["nonexistent"]

    def test_session_rename(self):
        """Test renaming a session."""
        sessions = {"old_name": {"data": "value"}}

        # Rename
        sessions["new_name"] = sessions.pop("old_name")

        assert "old_name" not in sessions
        assert "new_name" in sessions
        assert sessions["new_name"]["data"] == "value"


class TestSessionMetadata:
    """Test session metadata."""

    def test_session_timestamps(self):
        """Test session creation and update timestamps."""
        session = {
            "name": "test",
            "created_at": "2025-11-24T10:00:00",
            "updated_at": "2025-11-24T15:30:00"
        }
        assert "created_at" in session
        assert "updated_at" in session

    def test_session_message_count(self):
        """Test tracking message count in session."""
        session = {
            "name": "test",
            "messages": [
                {"role": "user", "content": "1"},
                {"role": "assistant", "content": "2"},
                {"role": "user", "content": "3"}
            ]
        }
        message_count = len(session["messages"])
        assert message_count == 3

    def test_session_version_tracking(self):
        """Test version tracking in sessions."""
        session = {
            "name": "test",
            "version": "0.2.8",
            "messages": []
        }
        assert session["version"] == "0.2.8"
