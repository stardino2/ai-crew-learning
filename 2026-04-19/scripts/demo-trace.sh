#!/bin/sh
# demo-trace.sh — print a banner and append to the demo trace log.
# Used by Cline during the autonomous feature workflow so the audience
# can follow progress on the terminal.
#
# Usage:
#   sh scripts/demo-trace.sh "Step 1 — Worktree 분리"
#   sh scripts/demo-trace.sh reset               # truncate the log and stamp a header
#
# Log file: logs/demo-trace.md (fixed, overwritten per demo run)

LOG_FILE="logs/demo-trace.md"
mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null

if [ "$1" = "reset" ]; then
  {
    echo "# Demo Trace"
    echo ""
    echo "_run started: $(date '+%Y-%m-%d %H:%M:%S')_"
    echo ""
  } > "$LOG_FILE"
  echo ""
  echo "═══════════════════════════════════════════════════"
  echo "  DEMO TRACE RESET — $(date '+%H:%M:%S')"
  echo "═══════════════════════════════════════════════════"
  echo ""
  exit 0
fi

TITLE="$1"
if [ -z "$TITLE" ]; then
  echo "usage: sh scripts/demo-trace.sh \"<step title>\" | reset" >&2
  exit 2
fi

echo ""
echo "═══════════════════════════════════════════════════"
echo "  $TITLE"
echo "═══════════════════════════════════════════════════"
echo ""

{
  echo ""
  echo "## $TITLE"
  echo ""
  echo "_$(date '+%H:%M:%S')_"
  echo ""
} >> "$LOG_FILE"
