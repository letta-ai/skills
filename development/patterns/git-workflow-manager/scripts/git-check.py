#!/usr/bin/env python3
"""
Git Workflow Validation Script

Validates commit messages and branch names according to git-workflow-manager
skill conventions.

Usage:
    # Validate current branch name
    ./git-check.py --branch

    # Validate a commit message
    ./git-check.py --commit "Add new feature"

    # Validate commit message from file
    ./git-check.py --commit-file .git/COMMIT_EDITMSG

    # Validate both
    ./git-check.py --branch --commit-file .git/COMMIT_EDITMSG
"""

import sys
import re
import subprocess
from pathlib import Path


def get_current_branch():
    """Get the current git branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def validate_branch_name(branch_name):
    """
    Validate branch name follows conventions.
    
    Valid patterns:
    - feature/description or add/description
    - fix/description
    - update/description
    - refactor/description
    - docs/description
    - chore/description
    - Or descriptive name without prefix
    """
    errors = []
    warnings = []
    
    # Check for protected branches
    if branch_name in ["main", "master", "develop"]:
        return [], []  # Protected branches are valid
    
    # Check for common prefixes
    prefixes = ["feature/", "add/", "fix/", "update/", "refactor/", "docs/", "chore/"]
    has_prefix = any(branch_name.startswith(prefix) for prefix in prefixes)
    
    if not has_prefix:
        warnings.append(
            f"Branch '{branch_name}' doesn't use a standard prefix "
            f"(feature/, fix/, update/, etc.)"
        )
    
    # Check for spaces (not allowed in branch names)
    if " " in branch_name:
        errors.append("Branch name contains spaces (not allowed)")
    
    # Check for uppercase letters (convention is lowercase)
    if branch_name != branch_name.lower():
        warnings.append("Branch name contains uppercase letters (convention is lowercase)")
    
    # Check length
    if len(branch_name) > 100:
        warnings.append(f"Branch name is very long ({len(branch_name)} chars)")
    
    return errors, warnings


def validate_commit_message(message):
    """
    Validate commit message follows conventions.
    
    Expected format:
    <summary line>
    
    🐾 Generated with [Letta Code](https://letta.com)
    
    Co-Authored-By: Letta <noreply@letta.com>
    """
    errors = []
    warnings = []
    
    lines = message.split("\n")
    
    if not lines:
        errors.append("Commit message is empty")
        return errors, warnings
    
    # Validate summary line
    summary = lines[0].strip()
    
    if not summary:
        errors.append("Summary line is empty")
    else:
        # Check length
        if len(summary) > 72:
            warnings.append(
                f"Summary line is {len(summary)} chars (recommended: ≤72 chars)"
            )
        
        # Check for period at end
        if summary.endswith("."):
            warnings.append("Summary line ends with period (convention: no period)")
        
        # Check for common prefixes (imperative mood)
        imperative_verbs = [
            "add", "update", "fix", "remove", "refactor", "improve",
            "document", "test", "chore", "feat", "docs", "style", "perf"
        ]
        starts_with_verb = any(
            summary.lower().startswith(verb) for verb in imperative_verbs
        )
        
        if not starts_with_verb:
            warnings.append(
                "Summary line should start with imperative verb "
                "(Add, Update, Fix, etc.)"
            )
    
    # Check for required footer
    message_lower = message.lower()
    
    if "letta code" not in message_lower:
        errors.append("Missing required footer: 'Generated with [Letta Code]'")
    
    if "co-authored-by: letta" not in message_lower:
        errors.append("Missing required footer: 'Co-Authored-By: Letta'")
    
    return errors, warnings


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate git branch names and commit messages"
    )
    parser.add_argument(
        "--branch",
        action="store_true",
        help="Validate current branch name"
    )
    parser.add_argument(
        "--commit",
        type=str,
        help="Validate commit message (direct string)"
    )
    parser.add_argument(
        "--commit-file",
        type=Path,
        help="Validate commit message from file"
    )
    
    args = parser.parse_args()
    
    if not (args.branch or args.commit or args.commit_file):
        parser.print_help()
        sys.exit(1)
    
    all_errors = []
    all_warnings = []
    
    # Validate branch
    if args.branch:
        branch = get_current_branch()
        if branch is None:
            print("❌ Error: Not in a git repository")
            sys.exit(1)
        
        print(f"🔍 Validating branch: {branch}")
        errors, warnings = validate_branch_name(branch)
        all_errors.extend(errors)
        all_warnings.extend(warnings)
        
        if not errors and not warnings:
            print("✅ Branch name is valid")
    
    # Validate commit message
    commit_msg = None
    if args.commit:
        commit_msg = args.commit
    elif args.commit_file:
        if not args.commit_file.exists():
            print(f"❌ Error: File not found: {args.commit_file}")
            sys.exit(1)
        commit_msg = args.commit_file.read_text()
    
    if commit_msg:
        print(f"🔍 Validating commit message")
        errors, warnings = validate_commit_message(commit_msg)
        all_errors.extend(errors)
        all_warnings.extend(warnings)
        
        if not errors and not warnings:
            print("✅ Commit message is valid")
    
    # Report results
    if all_warnings:
        print("\n⚠️  Warnings:")
        for warning in all_warnings:
            print(f"  - {warning}")
    
    if all_errors:
        print("\n❌ Errors:")
        for error in all_errors:
            print(f"  - {error}")
        sys.exit(1)
    
    if not all_errors and not all_warnings:
        print("\n✅ All validations passed!")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
