#!/usr/bin/env bash
# memfs-search — semantic search over agent memory files
#
# Usage:
#   memfs-search setup              Initialize backend and index memory
#   memfs-search search <query>     Keyword search (BM25)
#   memfs-search vsearch <query>    Semantic vector search
#   memfs-search query <query>      Hybrid search (best quality)
#   memfs-search status             Show index health
#   memfs-search reindex            Re-index after memory changes
#
# Environment:
#   MEMORY_DIR          Agent memory directory (required)
#   MEMFS_BACKEND       Force backend: qmd (default: auto-detect)
#   QMD_EMBED_MODEL     Override QMD embedding model
#
# All extra arguments are forwarded to the underlying backend.

set -euo pipefail

# --- Configuration -----------------------------------------------------------

COLLECTION_NAME="memory"
MASK="**/*.md"

# --- Helpers ------------------------------------------------------------------

die()  { echo "error: $*" >&2; exit 1; }
info() { echo ":: $*" >&2; }

detect_backend() {
  if [ -n "${MEMFS_BACKEND:-}" ]; then
    echo "$MEMFS_BACKEND"
    return
  fi
  if command -v qmd &>/dev/null; then
    echo "qmd"
    return
  fi
  echo "none"
}

require_memory_dir() {
  [ -n "${MEMORY_DIR:-}" ] || die "MEMORY_DIR is not set"
  [ -d "$MEMORY_DIR" ]     || die "MEMORY_DIR does not exist: $MEMORY_DIR"
}

# --- QMD Backend --------------------------------------------------------------

qmd_cmd() {
  # Ensure Node runtime (Bun's sqlite doesn't support extensions)
  unset BUN_INSTALL 2>/dev/null || true

  # Prefer the Node binary next to the qmd executable. Cameron's machine can
  # have a broken Homebrew node earlier in PATH, while qmd is installed under
  # nvm with a working Node runtime.
  local qmd_bin qmd_dir
  qmd_bin="$(command -v qmd)"
  qmd_dir="$(dirname "$qmd_bin")"
  if [ -x "$qmd_dir/node" ]; then
    PATH="$qmd_dir:$PATH" command qmd "$@"
  else
    command qmd "$@"
  fi
}

qmd_setup() {
  require_memory_dir
  info "Setting up QMD backend..."

  # Create collection if it doesn't exist
  if ! qmd_cmd collection list 2>/dev/null | grep -q "^$COLLECTION_NAME"; then
    qmd_cmd collection add "$MEMORY_DIR" --name "$COLLECTION_NAME" --mask "$MASK"
  else
    info "Collection '$COLLECTION_NAME' already exists"
  fi

  # Add context annotations
  qmd_cmd context add "qmd://$COLLECTION_NAME" \
    "Agent memory blocks — system prompt files and reference materials" 2>/dev/null || true
  qmd_cmd context add "qmd://$COLLECTION_NAME/system" \
    "In-context memory blocks rendered in the system prompt every turn" 2>/dev/null || true
  qmd_cmd context add "qmd://$COLLECTION_NAME/reference" \
    "Reference materials loaded on-demand via tools" 2>/dev/null || true

  # Generate embeddings
  info "Generating embeddings..."
  qmd_cmd embed

  info "Setup complete. Run 'memfs-search status' to verify."
}

qmd_search()  { qmd_cmd search  "$@" -c "$COLLECTION_NAME"; }
qmd_vsearch() { qmd_cmd vsearch "$@" -c "$COLLECTION_NAME"; }
qmd_query()   { qmd_cmd query   "$@" -c "$COLLECTION_NAME"; }
qmd_status()  { qmd_cmd status; }
qmd_reindex() {
  require_memory_dir
  info "Re-indexing memory..."
  qmd_cmd update
  qmd_cmd embed
  info "Done."
}

# --- Dispatch -----------------------------------------------------------------

BACKEND=$(detect_backend)
CMD="${1:-help}"
shift || true

case "$CMD" in
  setup)
    case "$BACKEND" in
      qmd)  qmd_setup "$@" ;;
      none) die "No backend available. Install QMD: npm install -g @tobilu/qmd" ;;
      *)    die "Unknown backend: $BACKEND" ;;
    esac
    ;;
  search)
    [ $# -ge 1 ] || die "Usage: memfs-search search <query> [options]"
    case "$BACKEND" in
      qmd)  qmd_search "$@" ;;
      none) die "No backend available. Run 'memfs-search setup' first." ;;
      *)    die "Unknown backend: $BACKEND" ;;
    esac
    ;;
  vsearch)
    [ $# -ge 1 ] || die "Usage: memfs-search vsearch <query> [options]"
    case "$BACKEND" in
      qmd)  qmd_vsearch "$@" ;;
      none) die "No backend. Semantic search requires QMD: npm install -g @tobilu/qmd" ;;
      *)    die "Unknown backend: $BACKEND" ;;
    esac
    ;;
  query)
    [ $# -ge 1 ] || die "Usage: memfs-search query <query> [options]"
    case "$BACKEND" in
      qmd)  qmd_query "$@" ;;
      none) die "No backend. Hybrid search requires QMD: npm install -g @tobilu/qmd" ;;
      *)    die "Unknown backend: $BACKEND" ;;
    esac
    ;;
  status)
    case "$BACKEND" in
      qmd)  qmd_status "$@" ;;
      none) echo "backend: none"; echo "No search backend configured." ;;
      *)    die "Unknown backend: $BACKEND" ;;
    esac
    ;;
  reindex)
    case "$BACKEND" in
      qmd)  qmd_reindex "$@" ;;
      none) die "No backend available. Run 'memfs-search setup' first." ;;
      *)    die "Unknown backend: $BACKEND" ;;
    esac
    ;;
  help|--help|-h)
    echo "Usage: memfs-search <command> [args...]"
    echo ""
    echo "Commands:"
    echo "  setup              Initialize backend and index memory"
    echo "  search <query>     Keyword search (BM25, fast)"
    echo "  vsearch <query>    Semantic vector search"
    echo "  query <query>      Hybrid search (best quality)"
    echo "  status             Show index health"
    echo "  reindex            Re-index after memory changes"
    echo ""
    echo "Backend: $BACKEND"
    echo ""
    echo "Extra arguments are forwarded to the backend (e.g. -n 10, --json, --files)."
    ;;
  *)
    die "Unknown command: $CMD. Run 'memfs-search help' for usage."
    ;;
esac
