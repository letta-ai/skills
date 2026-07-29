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

    # Unsafe mode (unrestricted agent permissions):
    python3 consortium.py --topic "..." --config agents.yaml --unsafe
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


# Maximum line size for JSON-RPC messages (DoS protection, L3)
_MAX_LINE_SIZE = 10 * 1024 * 1024  # 10 MB

# Env vars blocked from both model_env AND env config (security, C2/C4 from R1)
_BLOCKED_ENV_VARS = frozenset({
    "LD_PRELOAD", "LD_LIBRARY_PATH", "DYLD_INSERT_LIBRARIES",
    "PATH", "PYTHONPATH", "PYTHONSTARTUP",
    "SHELL", "BASH_ENV", "ENV",
    "SYSTEMROOT", "WINDIR",
})

_VERSION = "1.0.0"
_CLIENT_INFO = {"name": "consortium", "version": _VERSION}


def _filter_env(env_dict: dict) -> dict:
    """Filter out blocked env vars from a config dict (C2)."""
    return {k: v for k, v in env_dict.items() if k.upper() not in _BLOCKED_ENV_VARS}


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
            model: glm
            model_env: LETTA_ACP_MODEL
            env:
              LETTA_ACP_BACKEND: remote
              LETTA_AGENT_ID: agent-xxx

    Config format (JSON): same structure as above.

    The optional `model` field names the model to use. `model_env` specifies
    which environment variable to set with that value. For security, certain
    dangerous env var names are blocked (PATH, LD_PRELOAD, etc.) in both
    `model_env` and the general `env` dict.

    If no config file, returns empty dict (agents must be provided via --agent flags).
    """
    if not config_path:
        return {"agents": []}

    path = Path(config_path).expanduser()
    if not path.exists():
        print(f"Error: config file not found: {path}", file=sys.stderr)
        sys.exit(1)

    text = path.read_text(encoding="utf-8")  # L2

    if path.suffix in ('.yaml', '.yml'):
        if not HAS_YAML:
            print("Error: PyYAML not installed. Install with: pip install pyyaml", file=sys.stderr)
            sys.exit(1)
        data = yaml.safe_load(text)
        if data is None:  # Empty file
            data = {}
        if not isinstance(data, dict):  # H11: validate structure for YAML
            print(f"Error: config root must be a mapping, got {type(data).__name__}", file=sys.stderr)
            sys.exit(1)
        return data
    else:
        data = json.loads(text)
        if not isinstance(data, dict):  # H11: validate structure for JSON
            print(f"Error: config root must be a mapping, got {type(data).__name__}", file=sys.stderr)
            sys.exit(1)
        return data


def parse_agent_flag(flag: str) -> dict:
    """Parse --agent flag: 'name:command arg1 arg2'.

    Example:
        'alice:copilot.exe'           -> {id: alice, command: copilot.exe}
        'bob:letta-acp --yolo'        -> {id: bob, command: letta-acp, args: [--yolo]}

    Handles Windows drive letters in commands (e.g. C:\\tools\\agent.exe).
    For model overrides, use a config file with the `model` and `model_env` fields.
    """
    # Handle Windows drive letters: split on first ':' only if followed by a non-drive pattern
    # A drive letter is a single char followed by ':\' or ':/'
    m = re.match(r'^([a-zA-Z]):[/\\]', flag)
    if m:
        # Windows path — no name: prefix, use the basename as name
        cmd_parts = flag.split()
        name = Path(cmd_parts[0]).stem
        if not name:  # M6
            print(f"Error: could not derive agent name from command. Got: {flag}", file=sys.stderr)
            sys.exit(1)
        return {
            "id": name.lower(),
            "name": name,
            "command": cmd_parts[0],
            "args": cmd_parts[1:] if len(cmd_parts) > 1 else [],
            "env": {},
            "cwd": os.path.expanduser("~"),
        }

    parts = flag.split(':', 1)
    if len(parts) != 2:
        print(f"Error: --agent must be 'name:command'. Got: {flag}", file=sys.stderr)
        sys.exit(1)

    name = parts[0].strip()
    cmd_parts = parts[1].strip().split()

    if not name or not cmd_parts:  # M6
        print(f"Error: --agent name and command must be non-empty. Got: {flag}", file=sys.stderr)
        sys.exit(1)

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

    # Separate ID spaces to avoid collisions (R1 #3)
    _CLIENT_ID_BASE = 1000

    def __init__(self, config: dict, unsafe: bool = False):
        self.agent_id = config["id"]
        self.name = config.get("name", config["id"])
        self.command = config["command"]
        self.args = config.get("args", [])
        self.env_vars = _filter_env(config.get("env", {}))  # C2: filter env
        self.cwd = config.get("cwd", os.path.expanduser("~"))
        self.model = config.get("model")
        self.model_env = config.get("model_env")
        self.unsafe = unsafe  # C3

        self.process: asyncio.subprocess.Process | None = None
        self.session_id: str | None = None

        # ID tracking
        self._next_client_id = self._CLIENT_ID_BASE
        self._pending: dict[int, asyncio.Future] = {}

        # Init in __init__ (L7)
        self._notif_queue: asyncio.Queue = asyncio.Queue(maxsize=10000)  # L6
        self._reader_task: asyncio.Task | None = None

    def _validate_model_env(self) -> str | None:
        """Validate model_env is not a dangerous env var."""
        if not self.model_env:
            return None
        upper = self.model_env.upper()
        if upper in _BLOCKED_ENV_VARS:
            print(f"Warning: model_env '{self.model_env}' is blocked (security). "
                  f"Model override will not be applied.", file=sys.stderr)
            return None
        return self.model_env

    async def start(self):
        """Spawn the ACP subprocess and initialize."""
        env = {
            **os.environ,
            **self.env_vars,
        }

        safe_env = self._validate_model_env()
        if self.model and safe_env:
            env[safe_env] = self.model

        full_cmd = [self.command] + self.args

        self.process = await asyncio.create_subprocess_exec(
            *full_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=sys.stderr,
            env=env,
            cwd=self.cwd,
        )

        self._reader_task = asyncio.create_task(self._read_loop())

        # Initialize ACP protocol with capability negotiation
        result = await self._call("initialize", {
            "protocolVersion": 1,
            "clientCapabilities": {  # M5: we don't implement fs/terminal handlers
                "fs": {"readTextFile": False, "writeTextFile": False},
                "terminal": False,
            },
            "clientInfo": _CLIENT_INFO,  # M10
        }, timeout=30)

        # H2: Check returned protocol version
        agent_version = result.get("protocolVersion")
        if agent_version and agent_version != 1:
            print(f"[{self.name}] Warning: agent returned protocol version {agent_version}, "
                  f"expected 1", file=sys.stderr)

        # Create session — C3: default to acceptEdits, unrestricted only with --unsafe
        # L4: permissionMode is a letta-acp extension, not in ACP v1 spec.
        # Spec-compliant agents may ignore it. Session will work regardless.
        permission_mode = "unrestricted" if self.unsafe else "acceptEdits"
        result = await self._call("session/new", {
            "mcpServers": [],
            "cwd": self.cwd,
            "permissionMode": permission_mode,
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
                # L3: DoS protection
                if len(line) > _MAX_LINE_SIZE:
                    print(f"[{self.name}] Warning: skipping oversized line ({len(line)} bytes)", file=sys.stderr)
                    continue
                line = line.decode(errors="replace").strip()  # M7: survive bad bytes
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue

                msg_id = msg.get("id")
                has_method = "method" in msg
                has_result = "result" in msg or "error" in msg

                if msg_id is not None and msg_id in self._pending and not has_method:
                    fut = self._pending.pop(msg_id)
                    if not fut.done():
                        if "error" in msg:
                            fut.set_exception(ACPError(json.dumps(msg["error"])))
                        else:
                            fut.set_result(msg.get("result", {}))
                elif msg_id is not None and has_method:
                    await self._handle_request(msg)
                elif has_method:
                    await self._handle_notification(msg)
                # H6: removed _agent_pending set — not needed, was a memory leak
        except (asyncio.CancelledError, ConnectionResetError, BrokenPipeError):
            pass
        except Exception as e:
            print(f"[{self.name}] reader error: {e}", file=sys.stderr)
        finally:
            # C4: Resolve all pending futures with exceptions so callers don't hang
            for fut in list(self._pending.values()):
                if not fut.done():
                    fut.set_exception(ACPError("Connection lost"))

    async def _handle_request(self, msg: dict):
        """Handle a request from the agent (permissions, etc.)."""
        method = msg.get("method", "")
        params = msg.get("params", {})
        msg_id = msg["id"]

        if method == "session/request_permission":
            options = params.get("options", [])
            for opt in options:
                if opt.get("kind") in ("allow_always", "allow_once"):
                    opt_id = opt.get("optionId")  # M6: use .get() to avoid KeyError
                    if opt_id:
                        await self._send({"jsonrpc": "2.0", "id": msg_id,
                                   "result": {"outcome": {"outcome": "selected", "optionId": opt_id}}})
                        return
            if options:
                opt_id = options[0].get("optionId")  # M6
                if opt_id:
                    await self._send({"jsonrpc": "2.0", "id": msg_id,
                               "result": {"outcome": {"outcome": "selected", "optionId": opt_id}}})
                    return
            # H9: Empty options for permission request — deny, don't return method-not-found
            await self._send({"jsonrpc": "2.0", "id": msg_id,
                       "result": {"outcome": {"outcome": "denied"}}})
            return

        # Unknown method — return method not found error
        await self._send({"jsonrpc": "2.0", "id": msg_id,
                   "error": {"code": -32601, "message": f"Method not found: {method}"}})

    async def _handle_notification(self, msg: dict):
        """Store notifications for the active prompt to consume."""
        method = msg.get("method", "")
        if method == "session/update":
            params = msg.get("params", {})
            notif_sid = params.get("sessionId")
            if notif_sid and self.session_id and notif_sid != self.session_id:
                return
        try:
            self._notif_queue.put_nowait(msg)
        except asyncio.QueueFull:
            print(f"[{self.name}] Warning: notification queue full, dropping message", file=sys.stderr)

    async def _send(self, msg: dict):
        """Send a JSON-RPC message to the agent. (H10: handle pipe errors)"""
        data = (json.dumps(msg) + "\n").encode()
        try:
            self.process.stdin.write(data)
            await self.process.stdin.drain()
        except (BrokenPipeError, ConnectionResetError, RuntimeError):
            pass  # Process already dead

    async def _call(self, method: str, params: dict, timeout: float = 120) -> dict:
        """Send a JSON-RPC request and wait for the result."""
        req_id = self._next_client_id
        self._next_client_id += 1
        loop = asyncio.get_running_loop()
        fut: asyncio.Future = loop.create_future()
        self._pending[req_id] = fut

        await self._send({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params})

        try:
            return await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending.pop(req_id, None)
            raise ACPError(f"Timeout waiting for {method}")

    def _extract_text(self, update: dict) -> str:
        """Extract text from a session/update content field.

        Handles str, dict, array, and nested content structures (L4).
        """
        content = update.get("content", "")
        return self._extract_text_recursive(content)

    def _extract_text_recursive(self, content) -> str:
        """Recursively extract text from content of any type (L4)."""
        if isinstance(content, str):
            return content
        if isinstance(content, dict):
            # Could be {"text": "..."} or a nested structure with "content"
            if "text" in content:
                return content["text"]
            if "content" in content:
                return self._extract_text_recursive(content["content"])
            return ""
        if isinstance(content, list):
            parts = []
            for block in content:
                parts.append(self._extract_text_recursive(block))
            return "".join(parts)
        return ""

    async def cancel_session(self):
        """Send session/cancel to stop a running prompt. (H3/H4)"""
        if not self.session_id or not self.process or self.process.returncode is not None:
            return

        # M3: Removed invalid loop — _pending contains client request futures,
        # not agent permission request IDs. session/cancel is the correct mechanism.

        try:
            await self._send({
                "jsonrpc": "2.0",
                "method": "session/cancel",
                "params": {"sessionId": self.session_id},
            })
        except (BrokenPipeError, ConnectionResetError, RuntimeError):
            pass

        # H4: Wait briefly for idle state_update
        try:
            await asyncio.wait_for(self._notif_queue.get(), timeout=3.0)
        except asyncio.TimeoutError:  # L5: removed dead QueueEmpty catch
            pass

    async def prompt(self, text: str, on_event=None) -> str:
        """Send a prompt and collect the response. Returns the full response text.

        Per ACP spec: the session/prompt response may arrive immediately (before
        content) or after. Content arrives via session/update notifications.
        We collect updates until we see a stop reason or the prompt resolves.
        """
        if not self.session_id:
            raise ACPError("No session")

        # Clear stale notifications
        while not self._notif_queue.empty():
            self._notif_queue.get_nowait()

        req_id = self._next_client_id
        self._next_client_id += 1
        loop = asyncio.get_running_loop()  # M4: fixed from get_event_loop
        prompt_fut: asyncio.Future = loop.create_future()
        self._pending[req_id] = prompt_fut

        try:  # C5: try/finally to clean up prompt_fut
            await self._send({
                "jsonrpc": "2.0", "id": req_id,
                "method": "session/prompt",
                "params": {
                    "sessionId": self.session_id,
                    "prompt": [{"type": "text", "text": text}],
                },
            })

            full_text = ""
            thinking_text = ""
            done = False

            # M4: use loop.time() instead of get_event_loop().time()
            deadline = loop.time() + 300  # 5 min hard cap
            while not done:
                remaining = deadline - loop.time()
                if remaining <= 0:
                    break

                try:
                    msg = await asyncio.wait_for(self._notif_queue.get(), timeout=min(remaining, 5.0))
                except asyncio.TimeoutError:
                    if prompt_fut.done():
                        break
                    continue

                if msg.get("method") != "session/update":
                    continue

                update = msg.get("params", {}).get("update", {})
                kind = update.get("sessionUpdate", "")

                if kind in ("agent_message_chunk", "agent_message"):
                    full_text += self._extract_text(update)
                elif kind in ("agent_thought_chunk", "agent_thought"):
                    thinking_text += self._extract_text(update)

                if on_event:
                    await on_event({"kind": kind, "thinking": thinking_text, "text": full_text, "raw": update})

                stop_reason = update.get("stopReason")
                if stop_reason:
                    if stop_reason in ("error", "refusal"):  # L8: log error stop reasons
                        print(f"[{self.name}] Warning: agent returned stop reason '{stop_reason}'", file=sys.stderr)
                    done = True

            # H5: Check stopReason in prompt response result (ACP v1)
            if not prompt_fut.done():
                try:
                    result = await asyncio.wait_for(prompt_fut, timeout=5.0)
                    if isinstance(result, dict):
                        if not full_text:
                            full_text = self._extract_text(result)
                        resp_stop = result.get("stopReason")
                        if resp_stop in ("error", "refusal"):
                            print(f"[{self.name}] Warning: prompt response stop reason '{resp_stop}'", file=sys.stderr)
                except (asyncio.TimeoutError, ACPError):
                    pass

            return full_text
        finally:
            # C5: Always clean up prompt_fut
            self._pending.pop(req_id, None)

    async def stop(self):
        """Terminate the agent process."""
        await self.cancel_session()

        if self._reader_task:
            self._reader_task.cancel()
            try:
                await asyncio.wait_for(self._reader_task, timeout=2.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass

        if self.process:
            # H7: Close stdin before terminating
            try:
                self.process.stdin.close()
            except Exception:
                pass
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
        # L5: Timestamp intentionally omitted from format — agents see only
        # [Name]: message, which is cleaner for LLM consumption.
        return f"[{self.sender}]: {self.text}"


def _strip_markdown(text: str) -> str:
    """Strip common markdown formatting characters (L1)."""
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'`([^`]+)`', r'\1', text)        # `code`
    text = re.sub(r'__([^_]+)__', r'\1', text)      # __bold__
    text = re.sub(r'_([^_]+)_', r'\1', text)         # _italic_
    return text


def _is_pass(response: str) -> bool:
    """Check if a response is a PASS.

    Only matches PASS when it's the entire response (possibly with trailing
    punctuation/whitespace). "boarding PASS" does not match.
    Handles markdown-formatted PASS (L1).
    """
    stripped = _strip_markdown(response.strip()).strip().upper()
    return stripped in ("PASS", "PASS.", "PASS:", "PASS!", "PASS-", "PASS,", "PASS;")  # L6


def _extract_message_from_pass(response: str) -> tuple[str | None, bool]:
    """Split a response into (message, passed).

    Returns (message, True) if the agent spoke then passed.
    Returns (None, True) if it's a pure PASS.
    Returns (response, False) if it's a regular message.

    PASS must be on its own line to count.
    M1: Does NOT strip trailing dots from the message itself.
    """
    stripped = response.strip()

    if _is_pass(stripped):
        return None, True

    lines = stripped.split('\n')
    last_line = lines[-1].strip()
    if _is_pass(last_line):
        message = '\n'.join(lines[:-1]).strip()  # M1: don't rstrip('.')
        if message:
            return message, True
        return None, True

    return stripped, False


class Consortium:
    def __init__(self, topic: str, agent_configs: list[dict],
                 max_messages: int = 5, initiator: str = "Human",
                 interactive: bool = False, prompt_timeout: int = 300,
                 unsafe: bool = False, max_cycles: int = 100):  # M11
        self.topic = topic
        self.agent_configs = agent_configs
        self.max_messages = max_messages
        self.initiator = initiator
        self.interactive = interactive
        self.prompt_timeout = prompt_timeout
        self.unsafe = unsafe  # C3
        self.max_cycles = max_cycles  # M11

        self.agents = [(c["id"], c.get("name", c["id"])) for c in agent_configs]

        self.acp_agents: dict[str, ACPAgent] = {}
        self.queues: dict[str, asyncio.Queue] = {aid: asyncio.Queue() for aid, _ in self.agents}
        self.quotas: dict[str, int] = {aid: max_messages for aid, _ in self.agents}
        self.passed: set[str] = set()
        self.prev_passed: set[str] = set()  # M8: snapshot for update_prompt context
        self.active: set[str] = set()
        self.last_said: dict[str, str | None] = {aid: None for aid, _ in self.agents}

        self.transcript: list[ConsortiumMessage] = []
        self.lock = asyncio.Lock()
        self.ending = False
        self.transcript_path: Path | None = None
        self._started_agents: set[str] = set()  # L7: replace monkey-patching
        self._start_time: datetime | None = None  # L2: capture actual start time

    def name(self, aid: str) -> str:
        for agent_id, name in self.agents:
            if agent_id == aid:
                return name
        return aid[:12]

    def all_names(self, exclude: str | None = None) -> str:
        # M12: only include active agents
        return ", ".join(self.name(aid) for aid, _ in self.agents if aid != exclude and aid in self.active)

    def ts(self) -> str:
        return datetime.now().strftime("%H:%M:%S")

    def log(self, msg: str):
        print(f"[{self.ts()}] {msg}", flush=True)

    async def setup(self):
        """Spawn ACP subprocesses for all agents."""
        for config in self.agent_configs:
            aid = config["id"]
            name = config.get("name", aid)
            model = config.get("model")
            self.active.add(aid)
            model_str = f" (model: {model})" if model else ""
            self.log(f"Starting {name}{model_str}...")
            try:
                agent = ACPAgent(config, unsafe=self.unsafe)  # C3
                await asyncio.wait_for(agent.start(), timeout=90)
                self.acp_agents[aid] = agent
                self.log(f"  {name} ready (session: {agent.session_id[:12]}...)")
            except Exception as e:
                self.log(f"  {name} failed: {e}")
                self.active.discard(aid)

    async def broadcast(self, sender_id: str, text: str, msg_type: str = "message"):
        msg = ConsortiumMessage(self.name(sender_id), text, msg_type)
        self.transcript.append(msg)
        if msg_type == "message":
            # L10: iterate active agents only
            for aid in list(self.active):
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

        if self.last_said.get(aid):
            last_context = f'Your last message was delivered to the group: "{self.last_said[aid]}"\n\n'
        elif aid in self.prev_passed:  # M8: use snapshot from last cycle
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
        """Process one message cycle for an agent."""
        name = self.name(aid)
        agent = self.acp_agents.get(aid)
        if not agent or aid not in self.active or self.ending:
            return

        first = aid not in self._started_agents  # L7

        new_msgs = []
        try:
            first_msg = await asyncio.wait_for(self.queues[aid].get(), timeout=2.0)
            new_msgs.append(first_msg)
            while not self.queues[aid].empty():
                new_msgs.append(self.queues[aid].get_nowait())
        except asyncio.TimeoutError:
            return

        prompt = self.first_prompt(aid) if first else self.update_prompt(aid, new_msgs)
        if first:
            self._started_agents.add(aid)

        self.log(f"*{name} is thinking...*")

        async def on_event(event):
            kind = event.get("kind", "")
            if kind in ("agent_thought_chunk", "agent_thought"):
                thinking = event.get("thinking", "")
                sys.stdout.write(f"\r  {name} (thinking): {thinking[-80:]}")
                sys.stdout.flush()
            elif kind in ("agent_message_chunk", "agent_message"):
                sys.stdout.write("\r" + " " * 100 + "\r")
                sys.stdout.flush()

        try:
            response = await asyncio.wait_for(
                agent.prompt(prompt, on_event=on_event),
                timeout=self.prompt_timeout
            )
            sys.stdout.write("\r" + " " * 100 + "\r")
            sys.stdout.flush()
        except asyncio.TimeoutError:
            self.log(f"  {name} timed out — PASS")
            await agent.cancel_session()
            self.passed.add(aid)
            await self.broadcast(aid, "(timed out)", "pass")
            return
        except ACPError as e:
            self.log(f"  {name} error: {e}")
            self.passed.add(aid)
            self.active.discard(aid)  # M2: dead agent — remove from active
            return

        response = response.strip()

        # BUG FIX: Treat empty responses as PASS to avoid broadcasting empty messages.
        # Empty responses provide no value and can cause cascading empty-message cycles.
        if not response:
            self.passed.add(aid)
            self.log(f"  {name}: PASS (empty response)")
            await self.broadcast(aid, "explicitly passed", "pass")
            return
        message, passed = _extract_message_from_pass(response)

        if passed and message is None:
            self.passed.add(aid)
            self.log(f"  {name}: PASS")
            await self.broadcast(aid, "explicitly passed", "pass")
            return

        if passed and message is not None:
            self.quotas[aid] -= 1
            self.passed.discard(aid)
            await self.broadcast(aid, message)
            self.last_said[aid] = message  # M1: track what was said
            self.passed.add(aid)
            self.log(f"  {name}: (spoke then PASS)")
            await self.broadcast(aid, "said their piece, then passed", "pass")
            if self.quotas[aid] <= 0:
                self.active.discard(aid)
            return

        actual_response = message if message else response

        # C6: Only hold lock for the queue drain, not during re-prompt
        async with self.lock:
            missed = []
            while not self.queues[aid].empty():
                missed.append(self.queues[aid].get_nowait())

        if missed:
            self.log(f"  {name}: context changed, re-prompting...")
            try:
                revised = await asyncio.wait_for(
                    agent.prompt(self.reprompt(aid, actual_response, missed)),
                    timeout=self.prompt_timeout
                )
                rev_msg, rev_passed = _extract_message_from_pass(revised)
                if rev_passed:
                    # C8: properly handle PASS from re-prompt
                    if rev_msg:
                        self.quotas[aid] -= 1
                        self.passed.discard(aid)
                        await self.broadcast(aid, rev_msg)
                        self.last_said[aid] = rev_msg  # M1
                    self.passed.add(aid)
                    if not rev_msg:
                        await self.broadcast(aid, "explicitly passed", "pass")
                    else:
                        await self.broadcast(aid, "said their piece, then passed", "pass")
                    if self.quotas[aid] <= 0:
                        self.active.discard(aid)
                    return
                elif rev_msg:
                    actual_response = rev_msg
            except asyncio.TimeoutError:
                # M3: call cancel_session on re-prompt timeout
                self.log(f"  {name} re-prompt timed out — using original response")
                await agent.cancel_session()
            except ACPError:
                pass

        self.quotas[aid] -= 1
        self.passed.discard(aid)
        await self.broadcast(aid, actual_response)
        self.last_said[aid] = actual_response  # M1: track what was said

        if self.quotas[aid] <= 0:
            self.log(f"  {name} is out of messages")
            self.active.discard(aid)

    async def human_loop(self):
        if not self.interactive:
            return
        loop = asyncio.get_running_loop()
        while not self.ending:
            try:
                # C1/L7: Use asyncio.to_thread (daemon thread) with os.read.
                # os.read on fileno() is interruptible by closing stdin.
                line_bytes = await asyncio.to_thread(os.read, sys.stdin.fileno(), 65536)
                if not line_bytes:
                    break
                line = line_bytes.decode(errors="replace").strip()  # I1: consistent with M7
                if line == "/end":
                    self.ending = True
                    break
                if line:
                    msg = ConsortiumMessage("Human", line)
                    self.transcript.append(msg)
                    for aid in list(self.active):  # L10
                        await self.queues[aid].put(msg)
                    self.log(f"**[Human]** {line}")
            except asyncio.CancelledError:
                break
            except Exception as e:  # M9: log exceptions
                print(f"[human_loop] error: {e}", file=sys.stderr)
                break

    async def run(self):
        await self.setup()

        if not self.active:
            self.log("No agents available. Exiting.")
            return
        if len(self.active) < 2:  # M4: need at least 2 agents for discussion
            self.log("Need at least 2 active agents. Exiting.")
            return

        self.log(f"\nStarting consortium: {self.topic}")
        self._start_time = datetime.now()  # L2: capture actual start
        self.log(f"Agents: {', '.join(self.name(aid) for aid, _ in self.agents if aid in self.active)}")
        self.log(f"Max messages per agent: {self.max_messages}\n")

        # H12: Add topic to transcript
        await self.broadcast(self.initiator, self.topic)

        human_task = asyncio.create_task(self.human_loop())

        for cycle in range(self.max_cycles):  # M11
            if self.ending:
                break

            self.log(f"--- Cycle {cycle + 1} ---")
            self.transcript.append(ConsortiumMessage("System", f"--- Cycle {cycle + 1} ---", "system"))

            # C7: capture active list BEFORE creating tasks
            active_list = list(self.active)
            tasks = [asyncio.create_task(self.agent_loop(aid)) for aid in active_list]
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        aid = active_list[i] if i < len(active_list) else "?"
                        self.log(f"  Warning: agent_loop error for {aid}: {result}")

            if not self.active:
                break

            all_passed = self.active.issubset(self.passed)
            has_pending = any(not self.queues[aid].empty() for aid in self.active)
            has_quota = any(self.quotas[aid] > 0 for aid in self.active)

            # Core end condition: if no agent has pending messages, the
            # consortium is done. Messages only enter queues via:
            # 1. Initial topic (consumed in cycle 1)
            # 2. Broadcast from agents who spoke (queued during this cycle)
            # 3. Interactive human input (queued by human_loop)
            #
            # If has_pending=False after a cycle, no agent broadcast anything
            # and the topic was already consumed. There is genuinely nothing
            # for any agent to process next cycle. Ending here is correct
            # regardless of quota or pass state — an agent with quota but no
            # messages has nothing to respond to.
            #
            # Previous versions checked all_passed, has_quota, any_acted — all
            # of which had edge cases where the consortium cycled endlessly.
            if not has_pending:
                if all_passed:
                    self.log("All agents passed. Discussion complete.")
                elif not has_quota:
                    self.log("All agents out of messages.")
                else:
                    self.log("No pending messages. Ending.")
                break

            self.prev_passed = set(self.passed)  # M8: snapshot before clearing
            self.passed.clear()
        else:
            # M11: warn when hitting cycle limit
            self.log(f"Warning: reached cycle limit ({self.max_cycles}). Ending.")

        self.ending = True
        human_task.cancel()
        try:
            await human_task
        except asyncio.CancelledError:
            pass

        await self.reflection_phase()

        # H8: parallel agent shutdown
        stop_tasks = [agent.stop() for agent in self.acp_agents.values()]
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)

        self.save_transcript()
        msg_count = sum(1 for m in self.transcript if m.type == "message")
        self.log(f"\nConsortium ended. {msg_count} messages.")
        if self.transcript_path:
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
        reflect_agents = list(self.acp_agents.items())
        for aid, agent in reflect_agents:
            name = self.name(aid)
            tasks.append(self._reflect(aid, agent, name, reflection_prompt))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    aid = reflect_agents[i][0] if i < len(reflect_agents) else "?"
                    self.log(f"  Warning: reflection error for {aid}: {result}")

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
            await agent.cancel_session()
        except Exception as e:
            self.log(f"  {name} reflection error: {e}")

    def save_transcript(self):
        try:
            now = datetime.now()  # M8: call once
            ts = now.strftime("%Y%m%d-%H%M%S")
            slug = re.sub(r'[^a-z0-9]+', '-', self.topic.lower())[:50].strip('-')
            d = Path.home() / "consortium-transcripts"
            d.mkdir(exist_ok=True, parents=True)  # M7
            self.transcript_path = d / f"{ts}-{slug}.md"

            now_str = now.strftime('%Y-%m-%d %H:%M:%S')
            start_str = self._start_time.strftime('%Y-%m-%d %H:%M:%S') if self._start_time else now_str  # L2
            lines = [
                f"# Consortium: {self.topic}",
                f"**Participants:** {', '.join(name for _, name in self.agents)}",
                f"**Transport:** ACP (raw JSON-RPC over stdio)",
                f"**Started:** {start_str}",  # L2: use actual start time
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
            lines += ["---", f"**Ended:** {now_str}"]
            self.transcript_path.write_text("\n".join(lines), encoding="utf-8")  # L2
        except Exception as e:
            print(f"Warning: failed to save transcript: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="ACP-native multi-agent group chat — works with any ACP-compatible agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # With config file:
  consortium.py --topic "Design the API" --config agents.yaml

  # With explicit agents (name:command):
  consortium.py --topic "..." --agent "alice:copilot.exe" --agent "bob:letta-acp --yolo"

  # Interactive (human participates):
  consortium.py --topic "..." --config agents.yaml --interactive

  # Unsafe mode (unrestricted agent permissions):
  consortium.py --topic "..." --config agents.yaml --unsafe
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
    parser.add_argument("--timeout", type=int, default=300,
                        help="Per-agent prompt timeout in seconds (default: 300)")
    parser.add_argument("--unsafe", action="store_true",
                        help="Use unrestricted permissions (agents can run any command without approval)")
    parser.add_argument("--max-cycles", type=int, default=100,
                        help="Maximum number of consortium cycles (default: 100)")
    args = parser.parse_args()

    # M5: validate args
    if args.max_messages <= 0:
        print("Error: --max-messages must be > 0", file=sys.stderr)
        sys.exit(1)
    if args.timeout <= 0:
        print("Error: --timeout must be > 0", file=sys.stderr)
        sys.exit(1)
    if args.max_cycles <= 0:
        print("Error: --max-cycles must be > 0", file=sys.stderr)
        sys.exit(1)

    agent_configs = []

    if args.config:
        config = load_config(args.config)
        agents_from_config = config.get("agents", [])
        if not isinstance(agents_from_config, list):  # L3: validate type
            print(f"Error: 'agents' in config must be a list, got {type(agents_from_config).__name__}", file=sys.stderr)
            sys.exit(1)
        agent_configs.extend(agents_from_config)

    for flag in args.agent:
        agent_configs.append(parse_agent_flag(flag))

    if len(agent_configs) < 2:
        print("Error: need at least 2 agents. Use --config or --agent flags.", file=sys.stderr)
        sys.exit(1)

    seen = set()
    unique_configs = []
    for c in agent_configs:
        lower_id = c["id"].lower()
        if lower_id not in seen:
            seen.add(lower_id)
            unique_configs.append(c)
    agent_configs = unique_configs

    c = Consortium(args.topic, agent_configs, args.max_messages,
                   args.initiator, args.interactive, args.timeout,
                   unsafe=args.unsafe, max_cycles=args.max_cycles)
    asyncio.run(c.run())


if __name__ == "__main__":
    main()
