#!/usr/bin/env python3
"""Lightweight Discord CLI for AI agents. Wraps the Discord REST API v10."""

import argparse
import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import quote, urlencode

BASE = "https://discord.com/api/v10"


def get_token():
    token = os.environ.get("DISCORD_BOT_TOKEN") or os.environ.get("DISCORD_TOKEN")
    if not token:
        print(
            json.dumps(
                {
                    "error": "DISCORD_BOT_TOKEN is not set. Export it: export DISCORD_BOT_TOKEN=your_token"
                }
            ),
            file=sys.stderr,
        )
        sys.exit(1)
    return token


def api(method, path, token, body=None, params=None):
    url = f"{BASE}{path}"
    if params:
        url += "?" + urlencode(params)
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
        "User-Agent": "DiscordBot (https://letta.com, 1.0)",
    }
    data = json.dumps(body).encode() if body else None
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except HTTPError as e:
        raw = e.read().decode()
        try:
            err = json.loads(raw)
        except Exception:
            err = {"error": raw}
        err["status"] = e.code
        print(json.dumps(err), file=sys.stderr)
        sys.exit(1)


def out(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))


# --- Commands ---


def cmd_auth_test(args, token):
    data = api("GET", "/users/@me", token)
    out(
        {
            "ok": True,
            "user": data.get("username"),
            "id": data.get("id"),
            "discriminator": data.get("discriminator"),
        }
    )


def cmd_server_list(args, token):
    guilds = api("GET", "/users/@me/guilds", token)
    out([{"id": g["id"], "name": g["name"]} for g in guilds])


def cmd_server_info(args, token):
    data = api(
        "GET", f"/guilds/{args.server_id}", token, params={"with_counts": "true"}
    )
    out(
        {
            "id": data["id"],
            "name": data["name"],
            "member_count": data.get("approximate_member_count"),
            "online_count": data.get("approximate_presence_count"),
            "owner_id": data.get("owner_id"),
        }
    )


def cmd_channel_list(args, token):
    channels = api("GET", f"/guilds/{args.server_id}/channels", token)
    # Filter to text-like channels and sort by position
    text_types = {0, 5, 15}  # text, announcement, forum
    filtered = [c for c in channels if c.get("type") in text_types]
    filtered.sort(key=lambda c: (c.get("parent_id") or "", c.get("position", 0)))
    out(
        [
            {
                "id": c["id"],
                "name": c["name"],
                "type": c["type"],
                "category": c.get("parent_id"),
                "topic": c.get("topic"),
            }
            for c in filtered
        ]
    )


def cmd_message_list(args, token):
    params = {"limit": str(args.limit)}
    messages = api("GET", f"/channels/{args.channel_id}/messages", token, params=params)
    messages.reverse()  # chronological order
    out([_fmt_msg(m) for m in messages])


def cmd_message_get(args, token):
    m = api("GET", f"/channels/{args.channel_id}/messages/{args.message_id}", token)
    out(_fmt_msg(m))


def cmd_message_send(args, token):
    body = {"content": args.content}
    m = api("POST", f"/channels/{args.channel_id}/messages", token, body=body)
    out({"id": m["id"], "channel_id": m["channel_id"]})


def cmd_message_edit(args, token):
    body = {"content": args.content}
    m = api(
        "PATCH",
        f"/channels/{args.channel_id}/messages/{args.message_id}",
        token,
        body=body,
    )
    out({"id": m["id"], "edited": True})


def cmd_message_delete(args, token):
    api("DELETE", f"/channels/{args.channel_id}/messages/{args.message_id}", token)
    out({"deleted": True})


def cmd_message_search(args, token):
    params = {"content": args.query}
    if args.channel_id:
        params["channel_id"] = args.channel_id
    if args.author_id:
        params["author_id"] = args.author_id
    if args.limit:
        params["limit"] = str(args.limit)
    data = api("GET", f"/guilds/{args.server_id}/messages/search", token, params=params)
    results = []
    for thread in data.get("messages", []):
        for m in thread:
            if m.get("hit"):
                results.append(_fmt_msg(m))
    out(results)


def cmd_reaction_add(args, token):
    emoji = quote(args.emoji, safe="")
    api(
        "PUT",
        f"/channels/{args.channel_id}/messages/{args.message_id}/reactions/{emoji}/@me",
        token,
    )
    out({"ok": True})


def cmd_reaction_remove(args, token):
    emoji = quote(args.emoji, safe="")
    api(
        "DELETE",
        f"/channels/{args.channel_id}/messages/{args.message_id}/reactions/{emoji}/@me",
        token,
    )
    out({"ok": True})


def cmd_reaction_list(args, token):
    m = api("GET", f"/channels/{args.channel_id}/messages/{args.message_id}", token)
    reactions = m.get("reactions", [])
    out(
        [
            {
                "emoji": r["emoji"].get("name"),
                "count": r["count"],
                "me": r.get("me", False),
            }
            for r in reactions
        ]
    )


def cmd_user_list(args, token):
    params = {"limit": str(args.limit)}
    members = api("GET", f"/guilds/{args.server_id}/members", token, params=params)
    out(
        [
            {
                "id": m["user"]["id"],
                "username": m["user"]["username"],
                "display_name": m.get("nick")
                or m["user"].get("global_name")
                or m["user"]["username"],
            }
            for m in members
        ]
    )


def cmd_user_info(args, token):
    data = api("GET", f"/users/{args.user_id}", token)
    out(
        {
            "id": data["id"],
            "username": data["username"],
            "global_name": data.get("global_name"),
        }
    )


def cmd_thread_create(args, token):
    body = {"name": args.name, "auto_archive_duration": args.auto_archive or 1440}
    if args.message_id:
        t = api(
            "POST",
            f"/channels/{args.channel_id}/messages/{args.message_id}/threads",
            token,
            body=body,
        )
    else:
        body["type"] = 11  # public thread
        t = api("POST", f"/channels/{args.channel_id}/threads", token, body=body)
    out({"id": t["id"], "name": t["name"]})


def cmd_pin_add(args, token):
    api("PUT", f"/channels/{args.channel_id}/pins/{args.message_id}", token)
    out({"pinned": True})


def cmd_pin_remove(args, token):
    api("DELETE", f"/channels/{args.channel_id}/pins/{args.message_id}", token)
    out({"unpinned": True})


def cmd_pin_list(args, token):
    messages = api("GET", f"/channels/{args.channel_id}/pins", token)
    out([_fmt_msg(m) for m in messages])


# --- Helpers ---


def _fmt_msg(m):
    result = {
        "id": m["id"],
        "author": m["author"].get("username"),
        "author_id": m["author"]["id"],
        "content": m.get("content"),
        "timestamp": m.get("timestamp"),
    }
    if m.get("thread"):
        result["thread_id"] = m["thread"]["id"]
    if m.get("attachments"):
        result["attachments"] = [
            {"filename": a["filename"], "url": a["url"]} for a in m["attachments"]
        ]
    if m.get("reactions"):
        result["reactions"] = [
            {"emoji": r["emoji"].get("name"), "count": r["count"]}
            for r in m["reactions"]
        ]
    # Prune None/empty values
    return {k: v for k, v in result.items() if v is not None and v != [] and v != ""}


def main():
    parser = argparse.ArgumentParser(
        prog="discord-cli", description="Discord CLI for AI agents"
    )
    sub = parser.add_subparsers(dest="command")

    # auth
    auth = sub.add_parser("auth")
    auth_sub = auth.add_subparsers(dest="auth_cmd")
    auth_sub.add_parser("test")

    # server
    server = sub.add_parser("server")
    server_sub = server.add_subparsers(dest="server_cmd")
    server_sub.add_parser("list")
    si = server_sub.add_parser("info")
    si.add_argument("server_id")

    # channel
    channel = sub.add_parser("channel")
    channel_sub = channel.add_subparsers(dest="channel_cmd")
    cl = channel_sub.add_parser("list")
    cl.add_argument("server_id")

    # message
    message = sub.add_parser("message")
    message_sub = message.add_subparsers(dest="message_cmd")

    ml = message_sub.add_parser("list")
    ml.add_argument("channel_id")
    ml.add_argument("--limit", type=int, default=25)

    mg = message_sub.add_parser("get")
    mg.add_argument("channel_id")
    mg.add_argument("message_id")

    ms = message_sub.add_parser("send")
    ms.add_argument("channel_id")
    ms.add_argument("content")

    me = message_sub.add_parser("edit")
    me.add_argument("channel_id")
    me.add_argument("message_id")
    me.add_argument("content")

    md = message_sub.add_parser("delete")
    md.add_argument("channel_id")
    md.add_argument("message_id")

    msearch = message_sub.add_parser("search")
    msearch.add_argument("server_id")
    msearch.add_argument("query")
    msearch.add_argument("--channel-id")
    msearch.add_argument("--author-id")
    msearch.add_argument("--limit", type=int, default=25)

    # reaction
    reaction = sub.add_parser("reaction")
    reaction_sub = reaction.add_subparsers(dest="reaction_cmd")

    for name in ["add", "remove"]:
        r = reaction_sub.add_parser(name)
        r.add_argument("channel_id")
        r.add_argument("message_id")
        r.add_argument("emoji")

    rl = reaction_sub.add_parser("list")
    rl.add_argument("channel_id")
    rl.add_argument("message_id")

    # user
    user = sub.add_parser("user")
    user_sub = user.add_subparsers(dest="user_cmd")
    ul = user_sub.add_parser("list")
    ul.add_argument("server_id")
    ul.add_argument("--limit", type=int, default=100)
    ui = user_sub.add_parser("info")
    ui.add_argument("user_id")

    # thread
    thread = sub.add_parser("thread")
    thread_sub = thread.add_subparsers(dest="thread_cmd")
    tc = thread_sub.add_parser("create")
    tc.add_argument("channel_id")
    tc.add_argument("name")
    tc.add_argument("--message-id")
    tc.add_argument("--auto-archive", type=int)

    # pin
    pin = sub.add_parser("pin")
    pin_sub = pin.add_subparsers(dest="pin_cmd")
    pa = pin_sub.add_parser("add")
    pa.add_argument("channel_id")
    pa.add_argument("message_id")
    pr = pin_sub.add_parser("remove")
    pr.add_argument("channel_id")
    pr.add_argument("message_id")
    pl = pin_sub.add_parser("list")
    pl.add_argument("channel_id")

    args = parser.parse_args()
    token = get_token()

    dispatch = {
        ("auth", "test"): cmd_auth_test,
        ("server", "list"): cmd_server_list,
        ("server", "info"): cmd_server_info,
        ("channel", "list"): cmd_channel_list,
        ("message", "list"): cmd_message_list,
        ("message", "get"): cmd_message_get,
        ("message", "send"): cmd_message_send,
        ("message", "edit"): cmd_message_edit,
        ("message", "delete"): cmd_message_delete,
        ("message", "search"): cmd_message_search,
        ("reaction", "add"): cmd_reaction_add,
        ("reaction", "remove"): cmd_reaction_remove,
        ("reaction", "list"): cmd_reaction_list,
        ("user", "list"): cmd_user_list,
        ("user", "info"): cmd_user_info,
        ("thread", "create"): cmd_thread_create,
        ("pin", "add"): cmd_pin_add,
        ("pin", "remove"): cmd_pin_remove,
        ("pin", "list"): cmd_pin_list,
    }

    key = (
        (args.command, getattr(args, f"{args.command}_cmd", None))
        if args.command
        else (None, None)
    )
    handler = dispatch.get(key)
    if not handler:
        parser.print_help()
        sys.exit(1)
    handler(args, token)


if __name__ == "__main__":
    main()
