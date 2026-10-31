from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "VYNEX.py"
SPEC = importlib.util.spec_from_file_location("vynex_delete_test_module", SOURCE)
assert SPEC is not None and SPEC.loader is not None
vynex = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(vynex)


class _Status:
    def __init__(self):
        self.value = ""

    def set(self, value):
        self.value = value


class DeleteConversationTests(unittest.TestCase):
    def make_app(self):
        app = object.__new__(vynex.VYNEXApp)
        app.root = object()
        app.chats = {
            "chat-a": {"id": "chat-a", "title": "Conversation A", "turns": []},
            "chat-b": {"id": "chat-b", "title": "Conversation B", "turns": []},
        }
        app.current_chat_id = "chat-b"
        app.busy = False
        app.status_var = _Status()
        app.refresh_count = 0
        app._refresh_recent_list = lambda: setattr(app, "refresh_count", app.refresh_count + 1)
        return app

    def test_confirmed_delete_persists_only_selected_conversation(self):
        app = self.make_app()
        written = {}
        with patch.object(vynex.messagebox, "askyesno", return_value=True), patch.object(
            vynex, "write_json", side_effect=lambda _path, data: written.update(data)
        ):
            deleted = app._delete_chat_record(app.chats["chat-a"], parent=app.root)

        self.assertTrue(deleted)
        self.assertNotIn("chat-a", app.chats)
        self.assertIn("chat-b", app.chats)
        self.assertNotIn("chat-a", written)
        self.assertIn("chat-b", written)
        self.assertEqual(app.refresh_count, 1)
        self.assertIn("Conversation A", app.status_var.value)

    def test_cancelled_delete_does_not_change_history(self):
        app = self.make_app()
        original = dict(app.chats)
        with patch.object(vynex.messagebox, "askyesno", return_value=False), patch.object(
            vynex, "write_json"
        ) as write_json:
            deleted = app._delete_chat_record(app.chats["chat-a"], parent=app.root)

        self.assertFalse(deleted)
        self.assertEqual(app.chats, original)
        write_json.assert_not_called()

    def test_deleting_active_conversation_resets_open_session(self):
        app = self.make_app()
        app.current_chat_id = "chat-a"
        app.current_turns = [{"role": "Vous", "text": "question privée"}]
        app.api_messages = [{"role": "system", "content": "instructions"}]
        app.last_assistant_answer = "réponse privée"
        app.pending_images = []
        app.pending_files = []
        app.home_composer = {}
        app.chat_composer = {}
        app._effective_system_prompt = lambda: "instructions"
        app._clear_transcript = lambda: None
        app._refresh_attachment_previews = lambda: None
        app.show_home = lambda: None
        with patch.object(vynex.messagebox, "askyesno", return_value=True), patch.object(
            vynex, "write_json", return_value=None
        ):
            deleted = app._delete_chat_record(app.chats["chat-a"], parent=app.root)

        self.assertTrue(deleted)
        self.assertNotEqual(app.current_chat_id, "chat-a")
        self.assertEqual(app.current_turns, [])
        self.assertEqual(app.last_assistant_answer, "")
        self.assertEqual(app.api_messages, [{"role": "system", "content": "instructions"}])


if __name__ == "__main__":
    unittest.main()
