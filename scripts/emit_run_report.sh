#!/bin/bash
# emit_run_report.sh — shared helper for toolkit commands to emit
# a structured run_report.md + append one row to run_log.csv.
#
# Usage (commands invoke with ONE line near end of execution):
#   emit_run_report.sh \
#     --command audit \
#     --run-dir ".toolkit/evidence/audit_runs/$(date +%Y-%m-%d_%H%M%S)_doc" \
#     --outcome complete \
#     --fields "input_file=path/to.md citations_checked=12 mismatches=0 verdict=pass"
#
# Required args: --command, --run-dir, --outcome
# Optional args: --fields "k1=v1 k2=v2 ..." (space-separated), --task-summary "text"
#
# Writes:
#   <run-dir>/run_report.md (YAML frontmatter + body sections)
#   <evidence-dir>/run_log.csv (one row appended, creates with header if absent)
#
# PLN-verifiability: all fields are deterministic inputs. No LLM-judged quality scores.
# Re-running on the same inputs produces the same outputs (modulo timestamp).
#
# v1.1 — shared by /audit, /improve, /dailysummary, /commit, /startup (and /pace, /coa,
# /pcv-research via parallel path in their own SKILL.md; not required to switch).
#
# SILENT FAILURE on any error (exit 0, stderr-only diag) — the calling command's
# primary output must NEVER be blocked by instrumentation failure.

set -uo pipefail
exec 2>>/tmp/emit_run_report_errors.log  # diagnostics only, never blocks

# ── Parse args ─────────────────────────────────────────────────────────────
COMMAND=""
RUN_DIR=""
OUTCOME=""
FIELDS=""
TASK_SUMMARY=""
EVIDENCE_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}/.toolkit/evidence"
TOOL_VERSION="v1.1"

while [ $# -gt 0 ]; do
  case "$1" in
    --command) COMMAND="$2"; shift 2 ;;
    --run-dir) RUN_DIR="$2"; shift 2 ;;
    --outcome) OUTCOME="$2"; shift 2 ;;
    --fields)  FIELDS="$2"; shift 2 ;;
    --task-summary) TASK_SUMMARY="$2"; shift 2 ;;
    --evidence-dir) EVIDENCE_DIR="$2"; shift 2 ;;
    --tool-version) TOOL_VERSION="$2"; shift 2 ;;
    *) shift ;;  # ignore unknown args silently
  esac
done

# ── Validate ───────────────────────────────────────────────────────────────
if [ -z "$COMMAND" ] || [ -z "$RUN_DIR" ] || [ -z "$OUTCOME" ]; then
  echo "emit_run_report.sh: missing required arg (command=$COMMAND run-dir=$RUN_DIR outcome=$OUTCOME)" >&2
  exit 0  # silent fail
fi

case "$OUTCOME" in
  complete|partial|failed) ;;
  *) echo "emit_run_report.sh: invalid outcome '$OUTCOME' (must be complete|partial|failed)" >&2; exit 0 ;;
esac

mkdir -p "$RUN_DIR" "$EVIDENCE_DIR" 2>/dev/null || true

RUN_ID=$(basename "$RUN_DIR")
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
DATE=$(date +"%Y-%m-%d")
MODEL="${CLAUDE_MODEL:-claude-opus-4-7}"

# ── Build YAML frontmatter ─────────────────────────────────────────────────
{
  echo "---"
  echo "schema_version: \"1.0\""
  echo "run_id: \"$RUN_ID\""
  echo "tool: \"$COMMAND\""
  echo "tool_version: \"$TOOL_VERSION\""
  echo "date: \"$DATE\""
  echo "timestamp: \"$TIMESTAMP\""
  echo "model: \"$MODEL\""
  [ -n "$TASK_SUMMARY" ] && echo "task_summary: \"$(echo "$TASK_SUMMARY" | sed 's/"/\\"/g')\""
  echo "outcome: \"$OUTCOME\""

  # Parse FIELDS into YAML — expects "k1=v1 k2=v2" (space-separated)
  if [ -n "$FIELDS" ]; then
    IFS=' ' read -ra PAIRS <<< "$FIELDS"
    for pair in "${PAIRS[@]}"; do
      key="${pair%%=*}"
      val="${pair#*=}"
      # Numeric stays unquoted, string quotes
      if [[ "$val" =~ ^-?[0-9]+(\.[0-9]+)?$ ]]; then
        echo "$key: $val"
      else
        echo "$key: \"$(echo "$val" | sed 's/"/\\"/g')\""
      fi
    done
  fi

  echo "---"
  echo ""
  echo "## Task"
  echo ""
  echo "${TASK_SUMMARY:-Run of /$COMMAND on $DATE.}"
  echo ""
  echo "## Fields Captured"
  echo ""
  if [ -n "$FIELDS" ]; then
    IFS=' ' read -ra PAIRS <<< "$FIELDS"
    for pair in "${PAIRS[@]}"; do
      echo "- \`${pair}\`"
    done
  else
    echo "- (none)"
  fi
  echo ""
  echo "## Evidence Footer"
  echo ""
  echo "- Command: /$COMMAND"
  echo "- Tool version: $TOOL_VERSION"
  echo "- Run ID: $RUN_ID"
  echo "- Timestamp: $TIMESTAMP"
  echo "- Model: $MODEL"
  echo "- Verifiable: re-running this command on the same inputs produces the same fields (modulo timestamp)."
} > "$RUN_DIR/run_report.md"

# ── Append to run_log.csv (create with canonical 13-column header if absent) ─
# The live schema across the project is 13 columns (compatible with historical
# /pace, /coa, /pcv-research rows written before this helper existed). We write
# the same schema so /runlog can aggregate across all rows cleanly.
#
# Canonical schema v1.1 (13 columns):
#   run_id,tool,tool_version,date,task_summary,outcome,model,
#   agent_count,convergence_rate,agree_count,diverge_count,report_path,notes
#
# Commands that don't have agent/convergence semantics (e.g., /audit, /commit,
# /dailysummary) leave those four columns empty; the structured `fields_json`
# payload travels in the `notes` cell for forward-compatibility.
LOG_CSV="$EVIDENCE_DIR/run_log.csv"
CANONICAL_HEADER="run_id,tool,tool_version,date,task_summary,outcome,model,agent_count,convergence_rate,agree_count,diverge_count,report_path,notes"
if [ ! -f "$LOG_CSV" ]; then
  echo "$CANONICAL_HEADER" > "$LOG_CSV"
fi

# Serialize fields as JSON for the CSV `notes` cell (flat k/v, no nesting)
FIELDS_JSON="{}"
if [ -n "$FIELDS" ]; then
  FIELDS_JSON="{"
  IFS=' ' read -ra PAIRS <<< "$FIELDS"
  first=1
  for pair in "${PAIRS[@]}"; do
    key="${pair%%=*}"
    val="${pair#*=}"
    [ $first -eq 0 ] && FIELDS_JSON="${FIELDS_JSON},"
    FIELDS_JSON="${FIELDS_JSON}\"\"${key}\"\":\"\"${val}\"\""
    first=0
  done
  FIELDS_JSON="${FIELDS_JSON}}"
fi

# Extract agent_count + convergence_rate + agree_count + diverge_count from
# FIELDS if present; multi-agent commands (pace/coa/pcv-research) set them,
# single-agent commands leave them empty. Keeps the CSV uniform.
AGENT_COUNT=""
CONVERGENCE_RATE=""
AGREE_COUNT=""
DIVERGE_COUNT=""
REPORT_PATH="$RUN_DIR/run_report.md"
if [ -n "$FIELDS" ]; then
  IFS=' ' read -ra PAIRS <<< "$FIELDS"
  for pair in "${PAIRS[@]}"; do
    case "${pair%%=*}" in
      agent_count)       AGENT_COUNT="${pair#*=}" ;;
      convergence_rate)  CONVERGENCE_RATE="${pair#*=}" ;;
      agree_count)       AGREE_COUNT="${pair#*=}" ;;
      diverge_count)     DIVERGE_COUNT="${pair#*=}" ;;
    esac
  done
fi

# Escape double-quotes for CSV
TASK_CSV=$(echo "${TASK_SUMMARY:-}" | sed 's/"/""/g')

# Build the 13-column row — notes cell carries the JSON fields payload
CSV_ROW="${RUN_ID},${COMMAND},${TOOL_VERSION},${DATE},\"${TASK_CSV}\",${OUTCOME},${MODEL},${AGENT_COUNT},${CONVERGENCE_RATE},${AGREE_COUNT},${DIVERGE_COUNT},${REPORT_PATH},\"${FIELDS_JSON}\""

# Atomic append via flock (portable across Linux/WSL). Without this, concurrent
# /pace + /coa completions can race and corrupt the CSV mid-line. flock acquires
# an exclusive lock on fd 9 (pointing at the CSV), appends, and releases.
#
# The flock wrapper block is silent on success and writes to stderr on timeout
# (rare — would require another process holding the lock for >2s).
if command -v flock >/dev/null 2>&1; then
  (
    flock -w 2 -x 9 || { echo "emit_run_report.sh: flock timeout on $LOG_CSV" >&2; exit 1; }
    echo "$CSV_ROW" >&9
  ) 9>> "$LOG_CSV"
else
  # Fallback for systems without flock — still works, just not concurrency-safe
  echo "$CSV_ROW" >> "$LOG_CSV"
fi

# Report path for caller (on stdout)
echo "run_report: $RUN_DIR/run_report.md"
echo "run_log:    $LOG_CSV (1 row appended)"

exit 0
