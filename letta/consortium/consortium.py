#!/usr/bin/env python3
"""
Consortium — ACP-native multi-agent group chat.

Agents participate in living conversations via raw ACP (Agent Client Protocol).
Each agent is spawned as an ACP-compatible subprocess, communicating via
JSON-RPC 2.0 over stdio. Agent-agnostic — works with ANY ACP-compatible agent
(letta-acp, Claude Code, Copilot CLI, or any tool implementing the ACP spec).

Usage:
    # With a config file (recommended):
    python3 consortium.py \
        --topic "How should we organize the build system?" \
        --config agents.yaml

    # With explicit agent flags:
    python3 consortium.py \
        --topic "..." \
        --agent "alice:copilot.exe" \
        --agent "bob:letta-acp --yolo" \
        --max-messages 5

    # Interactive mode (human participates):
    python3 consortium.py --topic "..." --config agents.yaml --interactive
"""

import argparse
import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


# ─── Agent Config ─────────────────────────────────────────────────────────────

def load_config(config_path: str | None = None) -> dict:
    """Load agent configuration from YAML or JSON file.

    Config format (YAML):
        agents:
          - id: alice
            name: Alice
            command: copilot.exe
            args: ["--yolo"]
            env:
              API_KEY: xxx
            cwd: /home/user

          - id: bob
            name: Bob
            command: letta-acp
            args: ["--yolo"]
            env:
              LETTA_ACP_BACKEND: remote
              LETTA_AGENT_ID: agent-xxx
              LETTA_APP_SERVER_URL: ws://127.0.0.1:14601

    Config format (JSON): same structure as above.

    If no config file, returns empty dict (agents must be provided via --agent flags).
    """
    if not config_path:
        return {"agents": []}

    path = Path(config_path).expanduser()
    if not path.exists():
        print(f"Error: config file not found: {path}", file=sys.stderr)
        sys.exit(1)

    text = path.read_text()

    if path.suffix in ('.yaml', '.yml'):
        if not HAS_YAML:
            print("Error: PyYAML not installed. Install with: pip install pyyaml", file=sys.stderr)
            sys.exit(1)
        return yaml.safe_load(text)
    else:
        return json.loads(text)


def parse_agent_flag(flag: str) -> dict:
    """Parse --agent flag: 'name:command arg1 arg2' → {id, name, command, args}."""
    parts = flag.split(':', 1)
    if len(parts) != 2:
        print(f"Error: --agent must be 'name:command'. Got: {flag}", file=sys.stderr)
        sys.exit(1)

    name = parts[0].strip()
    cmd_parts = parts[1].strip().split()

    return {
        "id": name.lower(),
        "name": name,
        "command": cmd_parts[0],
        "args": cmd_parts[1:] if len(cmd_parts) > 1 else [],
        "env": {},
        "cwd": os.path.expanduser("~"),
    }


# ─── ACP Client (JSON-RPC 2.0 over stdio) ─────────────────────────────────────

class ACPError(Exception):
    pass


class ACPAgent:
    """A single ACP agent subprocess with JSON-RPC communication."""

    def __init__(self, config: dict):
        self.agent_id = config["id"]
        self.name = config.get("name", config["id"])
        self.command = config["command"]
        self.args = config.get("args", [])
        self.env_vars = config.get("env", {})
        self.cwd = config.get("cwd", os.path.expanduser("~"))

        self.process: asyncio.subprocess.Process | None = None
        self.session_id: str | None = None
        self._next_id = 1
        self._pending: dict[int, asyncio.Future] = {}
        self._reader_task: asyncio.Task | None = None

    async def start(self):
        """Spawn the ACP subprocess and initialize."""
        env = {
            **os.environ,
            **self.env_vars,
        }

        # Build the command (binary + args)
        full_cmd = [self.command] + self.args

        self.process = await asyncio.create_subprocess_exec(
            *full_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=sys.stderr,  # Passthrough for debugging
            env=env,
            cwd=self.cwd,
        )

        self._reader_task = asyncio.create_task(self._read_loop())

        # Initialize ACP protocol
        result = await self._call("initialize", {
            "protocolVersion": 1,
            "clientCapabilities": {},
        }, timeout=30)

        # Create session
        result = await self._call("session/new", {
            "mcpServers": [],
            "cwd": self.cwd,
            "permissionMode": "unrestricted",
        }, timeout=60)

        self.session_id = result.get("sessionId")
        if not self.session_id:
            raise ACPError("No sessionId in session/new response")

    async def _read_loop(self):
        """Continuously read JSON-RPC messages from the agent's stdout."""
        try:
            while True:
                line = await self.process.stdout.readline()
                if not line:
                    break
                line = line.decode().strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue

                msg_id = msg.get("id")

                # Check if this is a response to a pending request
                if msg_id is not None and msg_id in self._pending:
                    fut = self._pending.pop(msg_id)
                    if not fut.done():
                        if "error" in msg:
                            fut.set_exception(ACPError(json.dumps(msg["error"])))
                        else:
                            fut.set_result(msg.get("result", {}))
                elif msg_id is not None and "method" in msg:
                    # Request from agent (e.g., session/request_permission)
                    await self._handle_request(msg)
                elif "method" in msg:
                    # Notification (e.g., session/update) — store for the current prompt
                    await self._handle_notification(msg)
        except (asyncio.CancelledError, ConnectionResetError):
            pass

    async def _handle_request(self, msg: dict):
        """Handle a request from the agent (permissions, etc.)."""
        method = msg.get("method", "")
        params = msg.get("params", {})
        msg_id = msg["id"]

        if method == "session/request_permission":
            # Auto-approve: find allow option
            options = params.get("options", [])
            for opt in options:
                if opt.get("kind") in ("allow_always", "allow_once"):
                    self._send({"jsonrpc": "2.0", "id": msg_id,
                               "result": {"outcome": {"outcome": "selected", "optionId": opt["optionId"]}}})
                    return
            # Fallback: allow first option
            if options:
                self._send({"jsonrpc": "2.0", "id": msg_id,
                           "result": {"outcome": {"outcome": "selected", "optionId": options[0]["optionId"]}}})
                return
        # Default: empty response
        self._send({"jsonrpc": "2.0", "id": msg_id, "result": {}})

    async def _handle_notification(self, msg: dict):
        """Store notifications for the active prompt to consume."""
        if not hasattr(self, '_notif_queue'):
            self._notif_queue = asyncio.Queue()
        await self._notif_queue.put(msg)

    def _send(self, msg: dict):
        """Send a JSON-RPC message to the agent."""
        data = (json.dumps(msg) + "\n").encode()
        self.process.stdin.write(data)

    async def _call(self, method: str, params: dict, timeout: float = 120) -> dict:
        """Send a JSON-RPC request and wait for the result."""
        req_id = self._next_id
        self._next_id += 1
        fut: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending[req_id] = fut

        self._send({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params})

        try:
            return await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending.pop(req_id, None)
            raise ACPError(f"Timeout waiting for {method}")

    async def prompt(self, text: str, on_event=None) -> str:
        """
        Send a prompt and collect the response.
        Returns the full response text.
        on_event(event_dict) is called for each session/update.
        """
        if not self.session_id:
            raise ACPError("No session")

        # Ensure notification queue exists
        if not hasattr(self, '_notif_queue'):
            self._notif_queue = asyncio.Queue()

        # Send session/prompt
        req_id = self._next_id
        self._next_id += 1
        prompt_fut: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending[req_id] = prompt_fut

        self._send({
            "jsonrpc": "2.0", "id": req_id,
            "method": "session/prompt",
            "params": {
                "sessionId": self.session_id,
                "prompt": [{"type": "text", "text": text}],
            },
        })

        full_text = ""
        thinking_text = ""

        # Read notifications until the prompt result arrives
        while not prompt_fut.done():
            try:
                # Wait for next notification with short timeout
                msg = await asyncio.wait_for(self._notif_queue.get(), timeout=2.0)
            except asyncio.TimeoutError:
                continue

            if msg.get("method") != "session/update":
                continue

            update = msg.get("params", {}).get("update", {})
            kind = update.get("sessionUpdate", "")

            if kind == "agent_message_chunk":
                chunk = update.get("content", {}).get("text", "")
                full_text += chunk
            elif kind == "agent_thought_chunk":
                chunk = update.get("content", {}).get("text", "")
                thinking_text += chunk

            if on_event:
                await on_event({"kind": kind, "thinking": thinking_text, "text": full_text, "raw": update})

        # Get the result
        try:
            result = await asyncio.wait_for(prompt_fut, timeout=5.0)
        except (asyncio.TimeoutError, ACPError):
            pass

        return full_text

    async def stop(self):
        """Terminate the agent process."""
        if self._reader_task:
            self._reader_task.cancel()
        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except (asyncio.TimeoutError, ProcessLookupError):
                try:
                    self.process.kill()
                except ProcessLookupError:
                    pass


# ─── Consortium ───────────────────────────────────────────────────────────────

class ConsortiumMessage:
    def __init__(self, sender: str, text: str, msg_type: str = "message"):
        self.sender = sender
        self.text = text
        self.type = msg_type
        self.timestamp = time.time()

    def format(self) -> str:
        return f"[{self.sender}]: {self.text}"


class Consortium:
    def __init__(self, topic: str, agent_configs: list[dict],
                 max_messages: int = 5, initiator: str = "Human",
                 interactive: bool = False, prompt_timeout: int = 180):
        self.topic = topic
        self.agent_configs = agent_configs
        self.max_messages = max_messages
        self.initiator = initiator
        self.interactive = interactive
        self.prompt_timeout = prompt_timeout

        # Build agent registry
        self.agents = [(c["id"], c.get("name", c["id"])) for c in agent_configs]

        self.acp_agents: dict[str, ACPAgent] = {}
        self.queues: dict[str, asyncio.Queue] = {aid: asyncio.Queue() for aid, _ in self.agents}
        self.quotas: dict[str, int] = {aid: max_messages for aid, _ in self.agents}
        self.passed: set[str] = set()
        self.active: set[str] = set()
        self.last_said: dict[str, str | None] = {aid: None for aid, _ in self.agents}

        self.transcript: list[ConsortiumMessage] = []
        self.lock = asyncio.Lock()
        self.ending = False

    def name(self, aid: str) -> str:
        for agent_id, name in self.agents:
            if agent_id == aid:
                return name
        return aid[:12]

    def all_names(self, exclude: str | None = None) -> str:
        return ", ".join(self.name(aid) for aid, _ in self.agents if aid != exclude)

    def ts(self) -> str:
        return datetime.now().strftime("%H:%M:%S")

    def log(self, msg: str):
        print(f"[{self.ts()}] {msg}", flush=True)

    async def setup(self):
        """Spawn ACP subprocesses for all agents."""
        for config in self.agent_configs:
            aid = config["id"]
            name = config.get("name", aid)
            self.active.add(aid)
            self.log(f"Starting {name}...")
            try:
                agent = ACPAgent(config)
                await asyncio.wait_for(agent.start(), timeout=90)
                self.acp_agents[aid] = agent
                self.log(f"  {name} ready (session: {agent.session_id[:12]}...)")
            except Exception as e:
                self.log(f"  {name} failed: {e}")
                self.active.discard(aid)

    async def broadcast(self, sender_id: str, text: str, msg_type: str = "message"):
        msg = ConsortiumMessage(self.name(sender_id), text, msg_type)
        self.transcript.append(msg)
        # Only queue for other agents if it's a real message (not a pass)
        if msg_type == "message":
            for aid in self.queues:
                if aid != sender_id:
                    await self.queues[aid].put(msg)
        display = text if msg_type == "message" else f"({text})"
        sender_name = self.name(sender_id) if sender_id else "System"
        self.log(f"**[{sender_name}]** {display}")

    def first_prompt(self, aid: str) -> str:
        name = self.name(aid)
        return (
            f"You are {name} participating in a group discussion (consortium) with: {self.all_names(aid)}.\n\n"
            f"Topic: {self.topic}\n\n"
            f"This is your first opportunity to speak in this consortium. The discussion is just beginning.\n"
            f"You have {self.max_messages} messages maximum. Use them wisely.\n\n"
            f"Rules:\n"
            f"- When others speak, you'll see their messages as '[Name]: their message'\n"
            f"- If you have something to add, write your response\n"
            f"- If you don't have anything to add, respond with exactly: PASS\n"
            f"- Passing is fine — you stay in the conversation and can speak later\n"
            f"- Your response will be shared with all other agents\n\n"
            f"Opening topic from {self.initiator}:\n{self.topic}"
        )

    def update_prompt(self, aid: str, msgs: list[ConsortiumMessage]) -> str:
        lines = "\n".join(m.format() for m in msgs)
        remaining = self.quotas[aid]

        # Build context about what the agent did last
        if self.last_said.get(aid):
            last_context = f"Your last message was delivered to the group: \"{self.last_said[aid]}\"\n\n"
        elif aid in self.passed:
            last_context = "You passed in the previous round.\n\n"
        else:
            last_context = ""

        return (
            f"{last_context}"
            f"New messages from the group:\n{lines}\n\n"
            f"Do you want to respond to any of the above?\n"
            f"Write your response, or PASS if you have nothing to add.\n"
            f"You have {remaining}/{self.max_messages} remaining."
        )

    def reprompt(self, aid: str, draft: str, msgs: list[ConsortiumMessage]) -> str:
        new = "\n".join(m.format() for m in msgs)
        return (
            f"IMPORTANT: Your previous response was NOT delivered to the group yet.\n"
            f"While you were composing your response, other agents sent new messages.\n\n"
            f"Messages you missed:\n{new}\n\n"
            f'Your undelivered response was: "{draft}"\n\n'
            f"You must resend your response for it to be shared with the group.\n"
            f"You can resend it as-is, revise it to incorporate the new messages above, or PASS.\n"
            f"Consider further based on the new messages, or send your updated response, or PASS. {self.quotas[aid]}/{self.max_messages} remaining."
        )

    async def agent_loop(self, aid: str):
        """Process one message cycle for an agent. Called once per cycle by the main loop."""
        name = self.name(aid)
        agent = self.acp_agents.get(aid)
        if not agent or aid not in self.active or self.ending:
            return

        first = not hasattr(agent, '_consortium_started')

        # Collect new messages from queue
        new_msgs = []
        try:
            first_msg = await asyncio.wait_for(self.queues[aid].get(), timeout=2.0)
            new_msgs.append(first_msg)
            while not self.queues[aid].empty():
                new_msgs.append(self.queues[aid].get_nowait())
        except asyncio.TimeoutError:
            return  # No new messages this cycle

        # Build prompt
        prompt = self.first_prompt(aid) if first else self.update_prompt(aid, new_msgs)
        if first:
            agent._consortium_started = True

        self.log(f"*{name} is thinking...*")

        # Stream thinking to console
        async def on_event(event):
            kind = event.get("kind", "")
            if kind == "agent_thought_chunk":
                thinking = event.get("thinking", "")
                sys.stdout.write(f"\r  {name} (thinking): {thinking[-80:]}")
                sys.stdout.flush()
            elif kind == "agent_message_chunk":
                sys.stdout.write("\r" + " " * 100 + "\r")
                sys.stdout.flush()

        # Call agent
        try:
            response = await asyncio.wait_for(
                agent.prompt(prompt, on_event=on_event),
                timeout=self.prompt_timeout
            )
            sys.stdout.write("\r" + " " * 100 + "\r")
            sys.stdout.flush()
        except asyncio.TimeoutError:
            self.log(f"  {name} timed out — PASS")
            self.passed.add(aid)
            await self.broadcast(aid, "(timed out)", "pass")
            return
        except ACPError as e:
            self.log(f"  {name} error: {e}")
            self.passed.add(aid)
            return

        response = response.strip()

        if not response or response.strip().upper() == "PASS":
            self.passed.add(aid)
            self.log(f"  {name}: PASS")
            await self.broadcast(aid, "explicitly passed", "pass")
            return

        # Check if response ends with PASS (agent said something then passed)
        if response.rstrip().endswith("PASS.") or response.rstrip().endswith("PASS"):
            pass_idx = response.upper().rfind("PASS")
            actual_message = response[:pass_idx].strip().rstrip(".")
            if actual_message:
                self.quotas[aid] -= 1
                self.passed.discard(aid)
                await self.broadcast(aid, actual_message)
                self.passed.add(aid)
                self.log(f"  {name}: (spoke then PASS)")
                await self.broadcast(aid, "said their piece, then passed", "pass")
                if self.quotas[aid] <= 0:
                    self.active.discard(aid)
                return
            else:
                self.passed.add(aid)
                self.log(f"  {name}: PASS")
                await self.broadcast(aid, "explicitly passed", "pass")
                return

        # Submit with lock — check for context changes
        async with self.lock:
            missed = []
            while not self.queues[aid].empty():
                missed.append(self.queues[aid].get_nowait())

            if missed:
                self.log(f"  {name}: context changed, re-prompting...")
                try:
                    revised = await asyncio.wait_for(
                        agent.prompt(self.reprompt(aid, response, missed)),
                        timeout=self.prompt_timeout
                    )
                    if revised.strip() and revised.strip().upper() != "PASS":
                        response = revised.strip()
                except (asyncio.TimeoutError, ACPError):
                    pass  # Keep original

            if not response or response.strip().upper() == "PASS" or response.strip().endswith("PASS."):
                self.passed.add(aid)
                return

            self.quotas[aid] -= 1
            self.passed.discard(aid)
            await self.broadcast(aid, response)

            if self.quotas[aid] <= 0:
                self.log(f"  {name} is out of messages")
                self.active.discard(aid)

    async def human_loop(self):
        if not self.interactive:
            return
        loop = asyncio.get_event_loop()
        while not self.ending:
            try:
                line = await loop.run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                line = line.strip()
                if line == "/end":
                    self.ending = True
                    break
                if line:
                    msg = ConsortiumMessage("Human", line)
                    self.transcript.append(msg)
                    for aid in self.queues:
                        await self.queues[aid].put(msg)
                    self.log(f"**[Human]** {line}")
            except Exception:
                break

    def should_end(self) -> bool:
        if not self.active:
            return True
        return self.active.issubset(self.passed)

    async def run(self):
        await self.setup()

        if not self.active:
            self.log("No agents available. Exiting.")
            return

        self.log(f"\nStarting consortium: {self.topic}")
        self.log(f"Agents: {', '.join(self.name(aid) for aid, _ in self.agents if aid in self.active)}")
        self.log(f"Max messages per agent: {self.max_messages}\n")

        # Broadcast topic
        for aid in list(self.active):
            await self.queues[aid].put(ConsortiumMessage(self.initiator, self.topic))

        human_task = asyncio.create_task(self.human_loop())

        for cycle in range(100):
            if self.ending:
                break

            self.log(f"--- Cycle {cycle + 1} ---")
            self.transcript.append(ConsortiumMessage("System", f"--- Cycle {cycle + 1} ---", "system"))

            tasks = [asyncio.create_task(self.agent_loop(aid)) for aid in list(self.active)]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            self.passed.clear()

            if self.should_end():
                break

            if not any(not self.queues[aid].empty() for aid in self.active):
                if not any(self.quotas[aid] > 0 for aid in self.active):
                    break
                break

        self.ending = True
        human_task.cancel()

        # Reflection phase
        await self.reflection_phase()

        for agent in self.acp_agents.values():
            await agent.stop()

        self.save_transcript()
        msg_count = sum(1 for m in self.transcript if m.type == "message")
        self.log(f"\nConsortium ended. {msg_count} messages.")
        self.log(f"Transcript: {self.transcript_path}")

    async def reflection_phase(self):
        """Give each agent the full transcript to reflect on."""
        self.log("\n--- Reflection Phase ---")

        transcript_lines = []
        for msg in self.transcript:
            if msg.type == "system":
                continue
            elif msg.type == "pass":
                transcript_lines.append(f"[{msg.sender}]: (PASS)")
            else:
                transcript_lines.append(f"[{msg.sender}]: {msg.text}")
        full_transcript = "\n".join(transcript_lines)

        participants = ", ".join(self.name(aid) for aid, _ in self.agents)

        reflection_prompt = (
            f"The consortium has ended. Here is the full conversation:\n\n"
            f"{full_transcript}\n\n"
            f"Participants: {participants}\n"
            f"Total messages: {sum(1 for m in self.transcript if m.type == 'message')}\n\n"
            f"Take a moment to reflect on this discussion. You can:\n"
            f"- Update your memory with anything important that was discussed\n"
            f"- Note any decisions, action items, or follow-ups for yourself\n"
            f"- Run any tools or commands you need to\n\n"
            f"There is no need to respond to the group. This is your personal reflection time.\n"
            f"Simply acknowledge when you're done (one sentence)."
        )

        tasks = []
        for aid, agent in self.acp_agents.items():
            name = self.name(aid)
            tasks.append(self._reflect(aid, agent, name, reflection_prompt))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        self.log("--- Reflection complete ---")

    async def _reflect(self, aid: str, agent, name: str, prompt: str):
        """Run reflection for a single agent."""
        self.log(f"*{name} is reflecting...*")
        try:
            response = await asyncio.wait_for(
                agent.prompt(prompt),
                timeout=120.0
            )
            self.log(f"  {name} done reflecting")
        except asyncio.TimeoutError:
            self.log(f"  {name} reflection timed out")
        except Exception as e:
            self.log(f"  {name} reflection error: {e}")

    def save_transcript(self):
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        slug = re.sub(r'[^a-z0-9]+', '-', self.topic.lower())[:50].strip('-')
        d = Path.home() / "consortium-transcripts"
        d.mkdir(exist_ok=True)
        self.transcript_path = d / f"{ts}-{slug}.md"

        lines = [
            f"# Consortium: {self.topic}",
            f"**Participants:** {', '.join(name for _, name in self.agents)}",
            f"**Transport:** ACP (raw JSON-RPC over stdio)",
            f"**Started:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Max messages per agent:** {self.max_messages}",
            "", "---", "",
        ]
        for msg in self.transcript:
            if msg.type == "system":
                lines.append(f"*{msg.text}*")
            elif msg.type == "pass":
                lines.append(f"**[{msg.sender}]** *(PASS — {msg.text})*")
            else:
                lines.append(f"**[{msg.sender}]** {msg.text}")
            lines.append("")
        lines += ["---", f"**Ended:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
        self.transcript_path.write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(
        description="ACP-native multi-agent group chat — works with any ACP-compatible agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # With config file:
  consortium.py --topic "Design the API" --config agents.yaml

  # With explicit agents (name:command):
  consortium.py --topic "..." --agent "alice:copilot.exe" --agent "bob:claude"

  # Interactive (human participates):
  consortium.py --topic "..." --config agents.yaml --interactive
        """
    )
    parser.add_argument("--topic", required=True, help="Discussion topic")
    parser.add_argument("--config", help="Agent config file (YAML or JSON)")
    parser.add_argument("--agent", action="append", default=[],
                        help="Agent in 'name:command' format (can repeat)")
    parser.add_argument("--max-messages", type=int, default=5,
                        help="Max messages per agent (default: 5)")
    parser.add_argument("--initiator", default="Human",
                        help="Who initiated the discussion (default: Human)")
    parser.add_argument("--interactive", action="store_true",
                        help="Enable interactive mode (human can type messages)")
    parser.add_argument("--timeout", type=int, default=180,
                        help="Per-agent prompt timeout in seconds (default: 180)")
    args = parser.parse_args()

    # Build agent configs
    agent_configs = []

    if args.config:
        config = load_config(args.config)
        agent_configs.extend(config.get("agents", []))

    for flag in args.agent:
        agent_configs.append(parse_agent_flag(flag))

    if len(agent_configs) < 2:
        print("Error: need at least 2 agents. Use --config or --agent flags.", file=sys.stderr)
        sys.exit(1)

    # Deduplicate by agent ID
    seen = set()
    unique_configs = []
    for c in agent_configs:
        if c["id"] not in seen:
            seen.add(c["id"])
            unique_configs.append(c)
    agent_configs = unique_configs

    c = Consortium(args.topic, agent_configs, args.max_messages,
                   args.initiator, args.interactive, args.timeout)
    asyncio.run(c.run())


if __name__ == "__main__":
    main()
