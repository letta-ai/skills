"""Offline SDK tests: python -m unittest discover -s letta/conversations/scripts."""

from contextlib import redirect_stdout
import io
import unittest

import httpx
from letta_client import Letta

from conversations_cli import AppState, cmd_agent, cmd_list, cmd_new


class ConversationNameTests(unittest.TestCase):
    def setUp(self):
        self.rows = []
        self.new_conversation = self.conversation("conv-created")
        self.requests = []

        def handle(request):
            self.requests.append((request.method, request.url.path))
            if request.url.path == "/v1/conversations/":
                return httpx.Response(200, json=self.new_conversation if request.method == "POST" else self.rows)
            if request.url.path == "/v1/agents/agent-other":
                return httpx.Response(200, json={"id": "agent-other", "name": "Other agent"})
            raise AssertionError(f"Unexpected request: {request.method} {request.url}")

        self.client = Letta(
            api_key="offline-test-key", base_url="https://letta.test",
            http_client=httpx.Client(transport=httpx.MockTransport(handle)),
        )
        self.addCleanup(self.client.close)
        self.state = AppState(client=self.client, agent_id="agent-test", agent_name="Test agent")

    @staticmethod
    def conversation(id, messages=None, agent_id="agent-test"):
        return {"id": id, "agent_id": agent_id, "created_at": "2026-01-02T03:04:00Z",
                "in_context_message_ids": messages or []}

    def test_new_name_survives_list_and_server_reordering(self):
        with redirect_stdout(io.StringIO()):
            cmd_new(self.state, ["Project", "日本語"])
        original = self.state.current_conversation
        self.rows = [self.conversation("conv-other"), self.conversation("conv-created", ["m1", "m2", "m3"])]
        output = io.StringIO()
        with redirect_stdout(output):
            cmd_list(self.state)
        self.assertIn("Project 日本語", output.getvalue())
        self.assertEqual(self.state.current_conversation.name, "Project 日本語")
        self.assertEqual(self.state.current_conversation.message_count, 3)
        self.assertIs(self.state.current_conversation, self.state.conversations[1])
        self.assertIsNot(self.state.current_conversation, original)
        self.assertEqual(self.requests, [("POST", "/v1/conversations/"), ("GET", "/v1/conversations/")])

    def test_new_server_conversation_gets_generated_name(self):
        self.rows = [self.conversation("conv-server", ["m1"])]
        with redirect_stdout(io.StringIO()):
            cmd_list(self.state)
        info = self.state.conversations[0]
        self.assertEqual(info.name, "Conversation 1 (01/02 03:04)")
        self.assertEqual(info.message_count, 1)

    def test_agent_switch_clears_session_names(self):
        with redirect_stdout(io.StringIO()):
            cmd_new(self.state, ["Private", "label"])
            self.rows = [self.conversation("conv-other-agent", agent_id="agent-other")]
            cmd_agent(self.state, ["agent-other"])
        self.assertEqual(self.state.agent_id, "agent-other")
        self.assertIsNone(self.state.current_conversation)
        self.assertEqual([row.name for row in self.state.conversations], ["Conversation 1 (01/02 03:04)"])


if __name__ == "__main__":
    unittest.main()
