"""Exercise the model/tool round trip through a real local MCP stdio connection.

Run with the dependencies from scripts/requirements.txt installed:
    python -m unittest discover -s tools/mcp-builder/tests -v
"""

import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

from anthropic.types import TextBlock, ToolUseBlock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from connections import MCPConnectionStdio
from evaluation import agent_loop


# A JSON-RPC fixture avoids needing a separate MCP server framework. The client
# and its typed CallToolResult/content parsing are the real installed MCP SDK.
SERVER = r'''
import json
import sys

for line in sys.stdin:
    request = json.loads(line)
    if "id" not in request:
        continue
    method = request["method"]
    if method == "initialize":
        result = {
            "protocolVersion": request["params"]["protocolVersion"],
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "evaluation-fixture", "version": "1"},
        }
    elif method == "tools/list":
        result = {"tools": [{
            "name": "echo",
            "description": "Return the supplied text",
            "inputSchema": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        }]}
    elif method == "tools/call" and request["params"]["name"] == "echo":
        result = {"content": [{
            "type": "text", "text": request["params"]["arguments"]["text"],
        }]}
    else:
        print(json.dumps({
            "jsonrpc": "2.0", "id": request["id"],
            "error": {"code": -32602, "message": "Unknown fixture tool"},
        }), flush=True)
        continue
    print(json.dumps({
        "jsonrpc": "2.0", "id": request["id"], "result": result,
    }), flush=True)
'''


class ScriptedMessages:
    def __init__(self, test, calls):
        self.test = test
        self.calls = calls
        self.requests = 0

    def create(self, *, messages, **kwargs):
        self.requests += 1
        if self.requests == 1:
            return SimpleNamespace(stop_reason="tool_use", content=self.calls)

        self.test.assertEqual(self.requests, 2)
        self.test.assertEqual([m["role"] for m in messages], ["user", "assistant", "user"])
        results = messages[-1]["content"]
        self.test.assertEqual(
            [result["tool_use_id"] for result in results],
            [call.id for call in self.calls],
        )
        for call, result in zip(self.calls, results):
            self.test.assertEqual(result["type"], "tool_result")
            if call.name == "missing":
                self.test.assertIn("Unknown fixture tool", result["content"])
            else:
                self.test.assertEqual(
                    json.loads(result["content"]),
                    [{"type": "text", "text": call.input["text"]}],
                )
        return SimpleNamespace(
            stop_reason="end_turn",
            content=[TextBlock(type="text", text="<response>done</response>")],
        )


class ToolRoundTripTests(unittest.IsolatedAsyncioTestCase):
    async def check_calls(self, names):
        calls = [
            ToolUseBlock(type="tool_use", id=f"call_{i}", name=name, input={"text": f"résultat {i}"})
            for i, name in enumerate(names)
        ]
        messages = ScriptedMessages(self, calls)
        client = SimpleNamespace(messages=messages)
        async with MCPConnectionStdio(sys.executable, ["-c", SERVER]) as connection:
            tools = await connection.list_tools()
            self.assertEqual([tool["name"] for tool in tools], ["echo"])
            response, metrics = await agent_loop(client, "fixture-model", "Echo", tools, connection)

        self.assertEqual(response, "<response>done</response>")
        self.assertEqual(messages.requests, 2)
        for name in set(names):
            self.assertEqual(metrics[name]["count"], names.count(name))
            self.assertEqual(len(metrics[name]["durations"]), names.count(name))
            self.assertTrue(all(duration >= 0 for duration in metrics[name]["durations"]))

    async def test_single_typed_mcp_result_reaches_model(self):
        await self.check_calls(["echo"])

    async def test_all_parallel_calls_receive_results_in_one_message(self):
        await self.check_calls(["echo", "echo"])

    async def test_failed_call_does_not_drop_later_results(self):
        await self.check_calls(["missing", "echo"])


if __name__ == "__main__":
    unittest.main()
