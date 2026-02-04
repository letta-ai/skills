"""
Client-side tool execution - run tools locally while agent runs on Letta API.

This is how Letta Code executes Bash, Read, Write tools on your machine.

Run: python 13_client_side_tools.py
"""

import json
import os
import subprocess

from letta_client import Letta

client = Letta(api_key=os.getenv("LETTA_API_KEY"))


def main():
    # =========================================================================
    # Create a client-side tool
    # =========================================================================

    def run_local_command(command: str) -> str:
        """
        Run a shell command on the local machine.

        Args:
            command: The shell command to execute

        Returns:
            Command output as a string
        """
        # This code never runs - tool executes client-side
        raise Exception("This tool executes client-side only")

    tool = client.tools.upsert_from_function(
        func=run_local_command,
        default_requires_approval=True,  # Key: requires approval = client-side
    )

    print(f"Created client-side tool: {tool.name}")

    # =========================================================================
    # Create agent with the tool
    # =========================================================================

    agent = client.agents.create(
        name="local-executor",
        model="anthropic/claude-sonnet-4-5-20250929",
        embedding="openai/text-embedding-3-small",
        tools=[tool.name],
        memory_blocks=[
            {
                "label": "persona",
                "value": "I help users run commands on their local machine.",
            },
            {"label": "human", "value": "User wants to execute local commands."},
        ],
    )

    print(f"Created agent: {agent.id}")

    # =========================================================================
    # Send message - agent will request tool approval
    # =========================================================================

    print("\n--- Sending message to agent ---")

    response = client.agents.messages.create(
        agent_id=agent.id,
        messages=[{"role": "user", "content": "List files in current directory"}],
    )

    # =========================================================================
    # Handle approval request - execute tool locally
    # =========================================================================

    for msg in response.messages:
        if msg.message_type == "reasoning_message":
            print(f"[Reasoning] {msg.reasoning[:80]}...")

        elif msg.message_type == "approval_request_message":
            tool_call = msg.tool_call
            print(f"\n[Approval Request] Tool: {tool_call.name}")
            print(f"  Arguments: {tool_call.arguments}")

            # Parse arguments
            args = json.loads(tool_call.arguments)
            command = args["command"]

            print(f"\n--- Executing locally: {command} ---")

            # Execute tool on local machine
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                tool_return = result.stdout or result.stderr
                status = "success" if result.returncode == 0 else "error"
                stdout_lines = result.stdout.splitlines() if result.stdout else []
                stderr_lines = result.stderr.splitlines() if result.stderr else []
            except Exception as e:
                tool_return = f"Error: {str(e)}"
                status = "error"
                stdout_lines = []
                stderr_lines = [str(e)]

            print(f"[Local Result] Status: {status}")
            print(f"  Output: {tool_return[:200]}...")

            # =========================================================================
            # Send result back to agent
            # =========================================================================

            print("\n--- Sending result back to agent ---")

            response = client.agents.messages.create(
                agent_id=agent.id,
                messages=[
                    {
                        "type": "approval",
                        "approvals": [
                            {
                                "type": "tool",  # "tool" not "approval" - key difference!
                                "tool_call_id": tool_call.tool_call_id,
                                "tool_return": tool_return,
                                "status": status,
                                "stdout": stdout_lines,
                                "stderr": stderr_lines,
                            }
                        ],
                    }
                ],
            )

            # Agent continues with the result
            for msg in response.messages:
                if msg.message_type == "assistant_message":
                    print(f"\n[Agent Response] {msg.content}")

        elif msg.message_type == "assistant_message":
            print(f"[Agent] {msg.content}")


if __name__ == "__main__":
    main()
