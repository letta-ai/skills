#!/usr/bin/env python3
"""
Asana REST API Client for Claude Code.

A self-contained client with 30-second timeouts and automatic retries.
No external dependencies beyond requests.

Environment Variables:
    ASANA_ACCESS_TOKEN: Personal Access Token (required)
    ASANA_WORKSPACE: Default workspace GID (optional)

Usage as CLI:
    python3 asana_client.py workspaces
    python3 asana_client.py projects
    python3 asana_client.py tasks --project <gid> --incomplete
    python3 asana_client.py task <gid>
    python3 asana_client.py search "keyword"
    python3 asana_client.py create "Task name" --project <gid>
    python3 asana_client.py update <gid> --completed true
    python3 asana_client.py comment <gid> "Comment text"
    python3 asana_client.py my-tasks

Usage as library:
    from asana_client import AsanaClient
    client = AsanaClient()
    tasks = client.search_tasks(text="keyword")
"""

import argparse
import json
import os
import sys
from typing import List, Optional

try:
    import requests
except ImportError:
    print("Error: requests package required. Install with: pip install requests")
    sys.exit(1)

# Constants
ASANA_BASE_URL = "https://app.asana.com/api/1.0"
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3


class AsanaError(Exception):
    """Base exception for Asana errors."""
    pass


class AsanaAPIError(AsanaError):
    """Raised when Asana API returns an error."""

    def __init__(self, message: str, status_code: int = None):
        self.status_code = status_code
        super().__init__(message)


class AsanaAuthError(AsanaError):
    """Raised when authentication fails."""
    pass


class AsanaClient:
    """
    Asana REST API client.

    All operations have 30-second timeouts and automatic retries.
    """

    def __init__(self, token: str = None, workspace: str = None):
        """
        Initialize client.

        Args:
            token: Access token. If not provided, uses ASANA_ACCESS_TOKEN env var.
            workspace: Default workspace GID. If not provided, uses ASANA_WORKSPACE env var.
        """
        self._token = token or os.environ.get("ASANA_ACCESS_TOKEN")
        self._workspace = workspace or os.environ.get("ASANA_WORKSPACE")
        self._session = requests.Session()
        self._session.headers["Accept"] = "application/json"

        if not self._token:
            raise AsanaAuthError(
                "No Asana token provided.\n"
                "Set ASANA_ACCESS_TOKEN environment variable or pass token to constructor.\n"
                "Get a Personal Access Token at: https://app.asana.com/0/my-apps"
            )

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict = None,
        json_data: dict = None,
        retries: int = MAX_RETRIES,
    ) -> dict:
        """Make authenticated request with retry logic."""
        headers = {"Authorization": f"Bearer {self._token}"}
        url = f"{ASANA_BASE_URL}/{endpoint}"

        try:
            resp = self._session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data,
                timeout=REQUEST_TIMEOUT,
            )

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 60))
                raise AsanaAPIError(f"Rate limited. Retry after {retry_after}s", 429)

            if resp.status_code == 401:
                raise AsanaAuthError("Authentication failed. Check your access token.")

            if not resp.ok:
                error_detail = ""
                try:
                    error_json = resp.json()
                    if "errors" in error_json:
                        error_detail = "; ".join(
                            e.get("message", str(e)) for e in error_json["errors"]
                        )
                except Exception:
                    error_detail = resp.text[:200]

                raise AsanaAPIError(f"API error {resp.status_code}: {error_detail}", resp.status_code)

            return resp.json()

        except requests.Timeout:
            if retries > 0:
                return self._request(method, endpoint, params, json_data, retries - 1)
            raise AsanaAPIError(f"Request timed out after {REQUEST_TIMEOUT}s")

        except requests.ConnectionError as e:
            if retries > 0:
                return self._request(method, endpoint, params, json_data, retries - 1)
            raise AsanaAPIError(f"Connection error: {e}")

    def _get_workspace(self, workspace: str = None) -> str:
        """Get workspace GID, resolving default if needed."""
        if workspace:
            return workspace
        if self._workspace:
            return self._workspace

        # Auto-detect: get first workspace
        workspaces = self.list_workspaces()
        if not workspaces:
            raise AsanaError("No workspaces found for this user")
        self._workspace = workspaces[0]["gid"]
        return self._workspace

    # ========== Workspace Operations ==========

    def list_workspaces(self) -> List[dict]:
        """List all accessible workspaces."""
        result = self._request("GET", "workspaces", {"opt_fields": "name,is_organization"})
        return result.get("data", [])

    # ========== Project Operations ==========

    def get_projects(
        self,
        workspace: str = None,
        archived: bool = False,
        limit: int = 50,
    ) -> List[dict]:
        """List projects in workspace."""
        params = {
            "workspace": self._get_workspace(workspace),
            "archived": str(archived).lower(),
            "opt_fields": "name,owner.name,due_on,current_status.color",
            "limit": str(limit),
        }
        result = self._request("GET", "projects", params)
        return result.get("data", [])

    def get_project_sections(self, project_gid: str) -> List[dict]:
        """Get sections in a project."""
        result = self._request("GET", f"projects/{project_gid}/sections", {"opt_fields": "name"})
        return result.get("data", [])

    # ========== Task Operations ==========

    def get_task(self, task_gid: str) -> dict:
        """Get task details."""
        params = {
            "opt_fields": "name,notes,due_on,completed,assignee.name,projects.name,"
                          "custom_fields.name,custom_fields.display_value,tags.name,"
                          "memberships.section.name,dependencies,dependents"
        }
        result = self._request("GET", f"tasks/{task_gid}", params)
        return result.get("data", {})

    def get_tasks(
        self,
        project: str = None,
        section: str = None,
        assignee: str = None,
        workspace: str = None,
        completed: bool = None,
        limit: int = 100,
    ) -> List[dict]:
        """Get tasks from project, section, or by assignee."""
        params = {
            "opt_fields": "name,due_on,completed,assignee.name,projects.name",
            "limit": str(limit),
        }

        if project:
            endpoint = f"projects/{project}/tasks"
        elif section:
            endpoint = f"sections/{section}/tasks"
        elif assignee:
            endpoint = "tasks"
            params["assignee"] = assignee
            params["workspace"] = self._get_workspace(workspace)
        else:
            raise ValueError("Must provide project, section, or assignee")

        if completed is not None:
            params["completed_since"] = "now" if not completed else None

        result = self._request("GET", endpoint, params)
        return result.get("data", [])

    def search_tasks(
        self,
        text: str = None,
        workspace: str = None,
        assignee: str = None,
        projects: str = None,
        completed: bool = None,
        limit: int = 100,
    ) -> List[dict]:
        """Search tasks with filters."""
        params = {
            "opt_fields": "name,due_on,completed,assignee.name,projects.name",
            "limit": str(min(limit, 100)),
            "sort_by": "modified_at",
            "sort_ascending": "false",
        }

        if text:
            params["text"] = text
        if assignee:
            params["assignee.any"] = assignee
        if projects:
            params["projects.any"] = projects
        if completed is not None:
            params["completed"] = str(completed).lower()

        ws = self._get_workspace(workspace)
        result = self._request("GET", f"workspaces/{ws}/tasks/search", params)
        return result.get("data", [])

    def create_task(
        self,
        name: str,
        project: str = None,
        section: str = None,
        assignee: str = None,
        due_on: str = None,
        notes: str = None,
        workspace: str = None,
    ) -> dict:
        """Create a new task."""
        data = {"name": name}

        if project:
            data["projects"] = [project]
        if assignee:
            data["assignee"] = assignee
        if due_on:
            data["due_on"] = due_on
        if notes:
            data["notes"] = notes
        if workspace and not project:
            data["workspace"] = self._get_workspace(workspace)
        elif not project:
            data["workspace"] = self._get_workspace()

        result = self._request("POST", "tasks", json_data={"data": data})
        task = result.get("data", {})

        # Move to section if specified
        if section and task.get("gid"):
            self._request(
                "POST",
                f"sections/{section}/addTask",
                json_data={"data": {"task": task["gid"]}},
            )

        return task

    def update_task(
        self,
        task_gid: str,
        name: str = None,
        completed: bool = None,
        assignee: str = None,
        due_on: str = None,
        notes: str = None,
    ) -> dict:
        """Update a task."""
        data = {}

        if name is not None:
            data["name"] = name
        if completed is not None:
            data["completed"] = completed
        if assignee is not None:
            data["assignee"] = assignee
        if due_on is not None:
            data["due_on"] = due_on
        if notes is not None:
            data["notes"] = notes

        if not data:
            raise ValueError("No updates provided")

        result = self._request("PUT", f"tasks/{task_gid}", json_data={"data": data})
        return result.get("data", {})

    def delete_task(self, task_gid: str) -> bool:
        """Delete a task."""
        self._request("DELETE", f"tasks/{task_gid}")
        return True

    # ========== Subtask Operations ==========

    def get_subtasks(self, task_gid: str) -> List[dict]:
        """Get subtasks of a task."""
        params = {"opt_fields": "name,completed,due_on,assignee.name"}
        result = self._request("GET", f"tasks/{task_gid}/subtasks", params)
        return result.get("data", [])

    def create_subtask(
        self,
        parent_gid: str,
        name: str,
        assignee: str = None,
        due_on: str = None,
        notes: str = None,
    ) -> dict:
        """Create a subtask."""
        data = {"name": name}
        if assignee:
            data["assignee"] = assignee
        if due_on:
            data["due_on"] = due_on
        if notes:
            data["notes"] = notes

        result = self._request("POST", f"tasks/{parent_gid}/subtasks", json_data={"data": data})
        return result.get("data", {})

    # ========== Comment Operations ==========

    def get_comments(self, task_gid: str, limit: int = 50) -> List[dict]:
        """Get comments on a task."""
        params = {
            "opt_fields": "created_at,created_by.name,text,type,resource_subtype",
            "limit": str(limit),
        }
        result = self._request("GET", f"tasks/{task_gid}/stories", params)
        # Filter to just comments
        stories = result.get("data", [])
        return [s for s in stories if s.get("resource_subtype") == "comment_added"]

    def add_comment(self, task_gid: str, text: str) -> dict:
        """Add a comment to a task."""
        result = self._request(
            "POST", f"tasks/{task_gid}/stories", json_data={"data": {"text": text}}
        )
        return result.get("data", {})

    # ========== Dependency Operations ==========

    def get_dependencies(self, task_gid: str) -> List[dict]:
        """Get tasks that this task depends on."""
        result = self._request(
            "GET", f"tasks/{task_gid}/dependencies", {"opt_fields": "name,completed"}
        )
        return result.get("data", [])

    def add_dependency(self, task_gid: str, depends_on_gid: str) -> dict:
        """Make task depend on another task."""
        result = self._request(
            "POST",
            f"tasks/{task_gid}/addDependencies",
            json_data={"data": {"dependencies": [depends_on_gid]}},
        )
        return result.get("data", {})

    # ========== User Operations ==========

    def get_me(self) -> dict:
        """Get current user info."""
        result = self._request("GET", "users/me", {"opt_fields": "name,email,workspaces.name"})
        return result.get("data", {})


# ========== CLI ==========

def format_task(task: dict, verbose: bool = False) -> str:
    """Format task for display."""
    status = "✓" if task.get("completed") else " "
    due = task.get("due_on") or "-"
    name = task.get("name", "Untitled")
    assignee = (task.get("assignee") or {}).get("name", "-")

    line = f"[{status}] {due:<12} {assignee:<15} {name}"

    if verbose:
        gid = task.get("gid", "")
        line = f"{gid:<20} {line}"

    return line


def cmd_workspaces(client: AsanaClient, args):
    """List workspaces."""
    workspaces = client.list_workspaces()
    if args.json:
        print(json.dumps(workspaces, indent=2))
        return

    print(f"{'GID':<20} {'Name':<40} {'Organization'}")
    print("-" * 70)
    for ws in workspaces:
        org = "Yes" if ws.get("is_organization") else "No"
        print(f"{ws['gid']:<20} {ws['name']:<40} {org}")


def cmd_projects(client: AsanaClient, args):
    """List projects."""
    projects = client.get_projects(archived=args.archived, limit=args.limit)
    if args.json:
        print(json.dumps(projects, indent=2))
        return

    print(f"{'GID':<20} {'Due':<12} {'Project Name'}")
    print("-" * 60)
    for p in projects:
        due = p.get("due_on") or "-"
        print(f"{p['gid']:<20} {due:<12} {p['name']}")


def cmd_task(client: AsanaClient, args):
    """Get task details."""
    task = client.get_task(args.task_gid)
    if args.json:
        print(json.dumps(task, indent=2))
        return

    print(f"Task: {task.get('name')}")
    print(f"GID: {args.task_gid}")
    print(f"URL: https://app.asana.com/0/0/{args.task_gid}")
    print(f"Completed: {'Yes' if task.get('completed') else 'No'}")
    print(f"Due: {task.get('due_on') or 'None'}")
    print(f"Assignee: {(task.get('assignee') or {}).get('name', 'Unassigned')}")

    projects = task.get("projects", [])
    if projects:
        print(f"Projects: {', '.join(p['name'] for p in projects)}")

    notes = task.get("notes")
    if notes:
        print(f"\nDescription:\n{notes}")


def cmd_tasks(client: AsanaClient, args):
    """List tasks."""
    tasks = client.get_tasks(
        project=args.project,
        section=args.section,
        completed=False if args.incomplete else None,
        limit=args.limit,
    )
    if args.json:
        print(json.dumps(tasks, indent=2))
        return

    for task in tasks:
        print(format_task(task, verbose=args.verbose))
    print(f"\n({len(tasks)} tasks)")


def cmd_search(client: AsanaClient, args):
    """Search tasks."""
    tasks = client.search_tasks(
        text=args.query,
        completed=False if args.incomplete else None,
        limit=args.limit,
    )
    if args.json:
        print(json.dumps(tasks, indent=2))
        return

    for task in tasks:
        print(format_task(task, verbose=args.verbose))
    print(f"\n({len(tasks)} tasks)")


def cmd_my_tasks(client: AsanaClient, args):
    """Get my tasks."""
    tasks = client.get_tasks(
        assignee="me",
        completed=False if args.incomplete else None,
        limit=args.limit,
    )
    if args.json:
        print(json.dumps(tasks, indent=2))
        return

    for task in tasks:
        print(format_task(task, verbose=args.verbose))
    print(f"\n({len(tasks)} tasks)")


def cmd_create(client: AsanaClient, args):
    """Create task."""
    task = client.create_task(
        name=args.name,
        project=args.project,
        assignee=args.assignee,
        due_on=args.due,
        notes=args.notes,
    )
    if args.json:
        print(json.dumps(task, indent=2))
        return

    print(f"Created: {task.get('name')}")
    print(f"GID: {task.get('gid')}")
    print(f"URL: https://app.asana.com/0/0/{task.get('gid')}")


def cmd_update(client: AsanaClient, args):
    """Update task."""
    updates = {}
    if args.name:
        updates["name"] = args.name
    if args.completed is not None:
        updates["completed"] = args.completed.lower() == "true"
    if args.assignee:
        updates["assignee"] = args.assignee
    if args.due:
        updates["due_on"] = args.due

    task = client.update_task(args.task_gid, **updates)
    if args.json:
        print(json.dumps(task, indent=2))
        return

    print(f"Updated: {task.get('name')}")
    print(f"Completed: {'Yes' if task.get('completed') else 'No'}")


def cmd_comment(client: AsanaClient, args):
    """Add comment."""
    story = client.add_comment(args.task_gid, args.text)
    if args.json:
        print(json.dumps(story, indent=2))
        return

    print(f"Added comment to task {args.task_gid}")


def cmd_subtasks(client: AsanaClient, args):
    """Get subtasks."""
    subtasks = client.get_subtasks(args.task_gid)
    if args.json:
        print(json.dumps(subtasks, indent=2))
        return

    if not subtasks:
        print("No subtasks")
        return

    for task in subtasks:
        print(format_task(task))


def main():
    parser = argparse.ArgumentParser(
        description="Asana CLI - Direct REST API client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show GIDs")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # workspaces
    ws = subparsers.add_parser("workspaces", help="List workspaces")
    ws.set_defaults(func=cmd_workspaces)

    # projects
    proj = subparsers.add_parser("projects", help="List projects")
    proj.add_argument("--archived", action="store_true")
    proj.add_argument("-l", "--limit", type=int, default=50)
    proj.set_defaults(func=cmd_projects)

    # task
    task = subparsers.add_parser("task", help="Get task details")
    task.add_argument("task_gid", help="Task GID")
    task.set_defaults(func=cmd_task)

    # tasks
    tasks = subparsers.add_parser("tasks", help="List tasks in project/section")
    tasks.add_argument("-p", "--project", help="Project GID")
    tasks.add_argument("-s", "--section", help="Section GID")
    tasks.add_argument("-i", "--incomplete", action="store_true")
    tasks.add_argument("-l", "--limit", type=int, default=100)
    tasks.set_defaults(func=cmd_tasks)

    # search
    search = subparsers.add_parser("search", help="Search tasks")
    search.add_argument("query", help="Search text")
    search.add_argument("-i", "--incomplete", action="store_true")
    search.add_argument("-l", "--limit", type=int, default=50)
    search.set_defaults(func=cmd_search)

    # my-tasks
    my = subparsers.add_parser("my-tasks", help="Get my tasks")
    my.add_argument("-i", "--incomplete", action="store_true")
    my.add_argument("-l", "--limit", type=int, default=50)
    my.set_defaults(func=cmd_my_tasks)

    # create
    create = subparsers.add_parser("create", help="Create task")
    create.add_argument("name", help="Task name")
    create.add_argument("-p", "--project", help="Project GID")
    create.add_argument("-a", "--assignee", help="Assignee (GID or 'me')")
    create.add_argument("-d", "--due", help="Due date (YYYY-MM-DD)")
    create.add_argument("-n", "--notes", help="Description")
    create.set_defaults(func=cmd_create)

    # update
    update = subparsers.add_parser("update", help="Update task")
    update.add_argument("task_gid", help="Task GID")
    update.add_argument("--name", help="New name")
    update.add_argument("-c", "--completed", help="true/false")
    update.add_argument("-a", "--assignee", help="Assignee")
    update.add_argument("-d", "--due", help="Due date")
    update.set_defaults(func=cmd_update)

    # comment
    comment = subparsers.add_parser("comment", help="Add comment")
    comment.add_argument("task_gid", help="Task GID")
    comment.add_argument("text", help="Comment text")
    comment.set_defaults(func=cmd_comment)

    # subtasks
    subtasks = subparsers.add_parser("subtasks", help="Get subtasks")
    subtasks.add_argument("task_gid", help="Task GID")
    subtasks.set_defaults(func=cmd_subtasks)

    args = parser.parse_args()

    try:
        client = AsanaClient()
        args.func(client, args)
    except AsanaError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
