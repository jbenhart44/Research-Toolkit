#!/bin/bash
# Research Amp Toolkit — Installer
# Usage (counts derived at runtime — see SHARED_COMMANDS / STUDENT_ONLY arrays):
#   bash install.sh               # Full toolkit
#   bash install.sh --minimal     # Instructor toolkit
#   bash install.sh --hooks       # Also copy the optional hooks (see OPTIONAL_HOOKS); none is registered
#   bash install.sh --addon-seats # Also copy the add-on /coa seats (see ADDON_SEATS)
#   bash install.sh --dry-run     # Show what would be installed without copying
#   bash install.sh --help        # Show this help

set -e

TOOLKIT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMMANDS_DIR="$HOME/.claude/commands"
SKILLS_DIR="$HOME/.claude/skills"
AGENTS_DIR="$HOME/.claude/agents"
RUNTIME_DIR="$HOME/.claude/toolkit/scripts"
CONFIG_FILE="$HOME/.claude/toolkit-config.md"

# Colors (if terminal supports them)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Command sets — single source of truth for both install paths AND banner counts.
# Defined BEFORE show_help() so --help can render correct counts without running install.
SHARED_COMMANDS=(setup coa pace improve quarto readable help review)
STUDENT_ONLY=(startup daily-summary weekly-summary commit simplify audit run-log acquire)
POINTER_COMMANDS=(dailysummary weeklysummary runlog)   # shared/pointers/<old>.md → ~/.claude/commands/ (full install; v2.2.0 only): each says the new name
RUNTIME_SCRIPTS=(emit_run_report check_coa_evidence_paths acquire check_transcription)   # scripts/<name>.py → ~/.claude/toolkit/scripts/
SKILLS=(quick-ten guard-hook bulletproof list-maker step-by-step automate meeting-breakdown)   # shared/skills/<name>/ → ~/.claude/skills/<name>/ (full install only)
OPTIONAL_HOOKS=(usage_counter token_budget_guard summary_folder_guard protect_files)   # hooks/<name>.sh + .py → ~/.claude/hooks/ (--hooks only, never registered)
HOOK_LIBS=(_toolkit_config)         # hooks/<name>.py → ~/.claude/hooks/ (--hooks only): read by the hooks above
SEAT_AGENTS=(coa-advocate coa-economist coa-end-user coa-practitioner coa-skeptic)   # coa/agents/<name>.md → ~/.claude/agents/ (every install)
ADDON_SEATS=(coa-editor coa-historian coa-paper-reviewer)   # coa/agents/addon/<name>.md → ~/.claude/agents/ (--addon-seats only)
SHARED_COUNT=${#SHARED_COMMANDS[@]}
STUDENT_COUNT=${#STUDENT_ONLY[@]}
SKILL_COUNT=${#SKILLS[@]}
FULL_COUNT=$((SHARED_COUNT + STUDENT_COUNT + SKILL_COUNT + 1))   # +1 for /pcv (skill)
MIN_COUNT=$((SHARED_COUNT + 1))                                  # +1 for /pcv (skill)
BACKUP_ROOT="$HOME/.claude/toolkit-backups/$(date +%Y%m%d-%H%M%S)"   # outside skills/, so a backup never loads as a skill

print_header() {
    echo ""
    echo "================================================"
    echo "  Research Amp Toolkit Installer"
    echo "================================================"
    echo ""
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERR]${NC} $1"
}

show_help() {
    echo "Research Amp Toolkit — Installer"
    echo ""
    echo "Usage:"
    echo "  bash install.sh               Full toolkit (${FULL_COUNT} commands)"
    echo "  bash install.sh --minimal     Instructor toolkit (${MIN_COUNT} commands)"
    echo "  bash install.sh --hooks       Also copy the optional hooks (never registered)"
    echo "  bash install.sh --addon-seats Also copy the add-on /coa seats: ${ADDON_SEATS[*]}"
    echo "  bash install.sh --dry-run     Show what would be installed without copying"
    echo "  bash install.sh --help        Show this help"
    echo ""
    echo "What gets installed:"
    echo "  Commands    → ~/.claude/commands/"
    echo "  PCV skill   → ~/.claude/skills/pcv/"
    echo "  Skills      → ~/.claude/skills/ (full install only)"
    echo "  PCV agents  → ~/.claude/agents/"
    echo "  Seat agents → ~/.claude/agents/ (the /coa council seats)"
    echo "  Scripts     → ~/.claude/toolkit/scripts/ (run reports)"
    echo "  Config     → ~/.claude/toolkit-config.md (if not present)"
    echo "  Hooks       → ~/.claude/hooks/ (optional, with --hooks; never registered)"
    echo ""
    echo "Existing files are backed up before overwriting (skills to ~/.claude/toolkit-backups/)."
    exit 0
}

install_file() {
    local src="$1"
    local dst="$2"
    local label="$3"
    if [ ! -f "$src" ]; then
        print_error "$label not found in toolkit"
        return
    fi
    if [ "$DRY_RUN" = true ]; then
        if [ -f "$dst" ]; then
            print_warning "Would backup: $label → ${label}.bak"
        fi
        print_success "Would install: $label → $dst"
    else
        if [ -f "$dst" ]; then
            cp "$dst" "$dst.bak"
            print_warning "Backed up existing $label → ${label}.bak"
        fi
        cp "$src" "$dst"
        print_success "$label"
    fi
}

# Parse arguments
MINIMAL=false
DRY_RUN=false
INSTALL_HOOKS=false
ADDON=false
for arg in "$@"; do
    case $arg in
        --minimal) MINIMAL=true ;;
        --dry-run) DRY_RUN=true ;;
        --hooks) INSTALL_HOOKS=true ;;
        --addon-seats) ADDON=true ;;
        --help|-h) show_help ;;
        *) echo "Unknown argument: $arg"; show_help ;;
    esac
done

print_header

# Check prerequisites
if ! command -v claude &> /dev/null; then
    print_warning "Claude Code CLI not found in PATH. Commands will still be"
    print_warning "installed but you'll need Claude Code to use them."
    echo ""
fi

# /quarto renders with the Quarto CLI. It is not bundled, so warn now
# rather than at the user's first render.
if command -v quarto &> /dev/null; then
    print_success "Quarto found ($(quarto --version 2>/dev/null)) — /quarto can render slides."
else
    print_warning "Quarto not found in PATH. /quarto will install, but it cannot"
    print_warning "render slides until you install Quarto:"
    print_warning "  https://quarto.org/docs/get-started/"
    print_warning "  (macOS: brew install --cask quarto · Windows: winget install Posit.Quarto)"
    echo ""
fi

# Create directories
if [ "$DRY_RUN" = true ]; then
    for d in "$COMMANDS_DIR" "$SKILLS_DIR/pcv" "$AGENTS_DIR"; do
        if [ ! -d "$d" ]; then
            print_success "Would create: $d"
        fi
    done
else
    mkdir -p "$COMMANDS_DIR"
    mkdir -p "$SKILLS_DIR/pcv"
    mkdir -p "$AGENTS_DIR"
fi

# (SHARED_COMMANDS and STUDENT_ONLY arrays defined at top of file so show_help can use them.)

# Install shared commands (both products)
echo "Installing shared commands..."
for cmd in "${SHARED_COMMANDS[@]}"; do
    install_file "$TOOLKIT_DIR/shared/commands/$cmd.md" "$COMMANDS_DIR/$cmd.md" "$cmd.md"
done

# Install student-only commands (unless --minimal)
if [ "$MINIMAL" = false ]; then
    echo ""
    echo "Installing student workflow commands..."
    for cmd in "${STUDENT_ONLY[@]}"; do
        install_file "$TOOLKIT_DIR/shared/commands/$cmd.md" "$COMMANDS_DIR/$cmd.md" "$cmd.md"
    done
    # One-release pointers from a renamed command's old name to its new one (not counted as commands)
    for cmd in "${POINTER_COMMANDS[@]}"; do
        install_file "$TOOLKIT_DIR/shared/pointers/$cmd.md" "$COMMANDS_DIR/$cmd.md" "$cmd.md (renamed: a pointer)"
    done
fi

# Install skills (full install only): SKILL.md and assets/, never a self-test or mutation file.
# An existing copy is backed up outside skills/ first.
if [ "$MINIMAL" = false ]; then
    echo ""
    echo "Installing skills..."
    for s in "${SKILLS[@]}"; do
        src="$TOOLKIT_DIR/shared/skills/$s"
        if [ ! -f "$src/SKILL.md" ]; then
            print_error "skills/$s/SKILL.md not found in toolkit"
            continue
        fi
        if [ "$DRY_RUN" = true ]; then
            print_success "Would install: skills/$s → $SKILLS_DIR/$s"
        else
            if [ -d "$SKILLS_DIR/$s" ]; then
                mkdir -p "$BACKUP_ROOT/skills"
                cp -r "$SKILLS_DIR/$s" "$BACKUP_ROOT/skills/$s"
                print_warning "Backed up existing $s skill → ${BACKUP_ROOT/#$HOME/~}/skills/$s"
            fi
            mkdir -p "$SKILLS_DIR/$s"
            cp "$src/SKILL.md" "$SKILLS_DIR/$s/SKILL.md"
            for f in "$src"/assets/*; do
                [ -f "$f" ] || continue
                case "$f" in *_selftest.py|*_mutations.py) continue ;; esac
                mkdir -p "$SKILLS_DIR/$s/assets"
                cp "$f" "$SKILLS_DIR/$s/assets/"
            done
            print_success "skills/$s"
        fi
        if [ -f "$COMMANDS_DIR/$s.md" ]; then
            print_warning "A command /$s also exists ($COMMANDS_DIR/$s.md). The skill takes precedence; nothing was removed."
        fi
    done
fi

# Install PCV skill files (v3.14: recursive — skill/ contains subdirs like
# handlers/, hooks/, planning/, construction/, verification/, transition/, bundled/)
PCV_VERSION=$(head -1 "$TOOLKIT_DIR/pcv/skill/VERSION" 2>/dev/null | tr -d '[:space:]' || echo "unknown")
echo ""
echo "Installing PCV v$PCV_VERSION..."
if [ "$DRY_RUN" = true ]; then
    find "$TOOLKIT_DIR/pcv/skill" -type f | while read f; do
        rel="${f#$TOOLKIT_DIR/pcv/skill/}"
        print_success "Would install: pcv/$rel → $SKILLS_DIR/pcv/$rel"
    done
else
    # Backup existing pcv skill dir if present (single snapshot, not per-file), outside skills/
    if [ -d "$SKILLS_DIR/pcv" ] && [ "$(ls -A "$SKILLS_DIR/pcv" 2>/dev/null)" ]; then
        mkdir -p "$BACKUP_ROOT/skills"
        cp -r "$SKILLS_DIR/pcv" "$BACKUP_ROOT/skills/pcv"
        print_warning "Backed up existing pcv skill → ${BACKUP_ROOT/#$HOME/~}/skills/pcv"
    fi
    # Recursive copy preserving subdirectory structure
    mkdir -p "$SKILLS_DIR/pcv"
    cp -r "$TOOLKIT_DIR/pcv/skill/." "$SKILLS_DIR/pcv/"
    # OneDrive strips executable bits — restore them on shell scripts
    find "$SKILLS_DIR/pcv/handlers" "$SKILLS_DIR/pcv/hooks" \
         -type f -name '*.sh' -exec chmod +x {} + 2>/dev/null || true
    print_success "pcv skill files (recursive copy from bundle v$PCV_VERSION)"
fi

# Install PCV agent files
echo ""
echo "Installing PCV agents..."
for f in "$TOOLKIT_DIR"/pcv/agents/*; do
    fname=$(basename "$f")
    install_file "$f" "$AGENTS_DIR/$fname" "agents/$fname"
done

# Install the /coa council seat agents (every install: /coa is in SHARED_COMMANDS)
echo ""
echo "Installing council seat agents..."
for a in "${SEAT_AGENTS[@]}"; do
    install_file "$TOOLKIT_DIR/coa/agents/$a.md" "$AGENTS_DIR/$a.md" "agents/$a.md"
done
if [ "$ADDON" = true ]; then
    for a in "${ADDON_SEATS[@]}"; do
        install_file "$TOOLKIT_DIR/coa/agents/addon/$a.md" "$AGENTS_DIR/$a.md" "agents/$a.md"
    done
fi

# Install runtime scripts (every install: commands call them at the end of a run).
# Runtime files only: a script's self-test and mutation check stay in the clone.
echo ""
echo "Installing runtime scripts..."
if [ "$DRY_RUN" = true ]; then
    if [ ! -d "$RUNTIME_DIR" ]; then
        print_success "Would create: $RUNTIME_DIR"
    fi
else
    mkdir -p "$RUNTIME_DIR"
fi
for s in "${RUNTIME_SCRIPTS[@]}"; do
    install_file "$TOOLKIT_DIR/scripts/$s.py" "$RUNTIME_DIR/$s.py" "toolkit/scripts/$s.py"
done

# Install config template (only if not present)
if [ ! -f "$CONFIG_FILE" ]; then
    echo ""
    echo "Creating configuration template..."
    if [ "$DRY_RUN" = true ]; then
        print_success "Would install: toolkit-config.md → $CONFIG_FILE"
    else
        cp "$TOOLKIT_DIR/toolkit-config.md" "$CONFIG_FILE"
        print_success "toolkit-config.md (run /setup in Claude Code to fill it in)"
    fi
else
    print_warning "toolkit-config.md already exists — not overwriting"
fi

# Install hooks (optional, with --hooks flag)
if [ "$INSTALL_HOOKS" = true ]; then
    HOOKS_DIR="$HOME/.claude/hooks"
    echo ""
    echo "Installing optional hooks..."
    if [ "$DRY_RUN" = true ]; then
        if [ ! -d "$HOOKS_DIR" ]; then
            print_success "Would create: $HOOKS_DIR"
        fi
    else
        mkdir -p "$HOOKS_DIR"
    fi
    # Runtime files only: a hook's self-test and mutation check stay in the clone.
    for h in "${OPTIONAL_HOOKS[@]}"; do
        for ext in sh py; do
            install_file "$TOOLKIT_DIR/hooks/$h.$ext" "$HOOKS_DIR/$h.$ext" "hooks/$h.$ext"
        done
    done
    for l in "${HOOK_LIBS[@]}"; do
        install_file "$TOOLKIT_DIR/hooks/$l.py" "$HOOKS_DIR/$l.py" "hooks/$l.py"
    done
    if [ "$DRY_RUN" = false ]; then
        chmod +x "$HOOKS_DIR"/*.sh 2>/dev/null
    fi
    echo ""
    print_warning "Hooks copied but NOT registered: the installer never edits settings.json."
    print_warning "To turn one on, print its settings entry and paste it yourself:"
    print_warning "  python3 scripts/register_hooks.py <hook> [<hook> ...]   (from this clone; --list shows them)"
    print_warning "The guards that hold a list protect nothing until ~/.claude/toolkit-config.md names it (hooks/README.md)."
fi

# Summary
echo ""
echo "================================================"
if [ "$DRY_RUN" = true ]; then
    if [ "$MINIMAL" = true ]; then
        echo "  Instructor Toolkit dry run (${MIN_COUNT} commands incl. /pcv)"
    else
        echo "  Full Toolkit dry run (${FULL_COUNT} commands incl. /pcv)"
    fi
    echo "================================================"
    echo ""
    echo "This was a dry run. No files were modified."
    echo "Run without --dry-run to install."
else
    if [ "$MINIMAL" = true ]; then
        echo "  Instructor Toolkit installed (${MIN_COUNT} commands incl. /pcv)"
    else
        echo "  Full Toolkit installed (${FULL_COUNT} commands incl. /pcv)"
    fi
    echo "================================================"
    echo ""
    echo "Next steps:"
    echo "  1. Restart Claude Code so it picks up the newly installed commands."
    echo "  2. Open Claude Code in your project directory and type /setup. It asks about your"
    echo "     folders and workstreams and writes ~/.claude/toolkit-config.md."
    echo "  3. Type /pcv to start structured planning, or /help if you are not sure where to start."
fi
echo ""

# ──────────────────────────────────────────────────────────────────────────────
# v0.1.1 Proactive Suggestion Fragment — opt-in print block (default OFF)
# Behavior: detect CLAUDE.md, never modify it. Print the @import line so the
# user can paste it manually if they choose. Idempotent on re-run.
# Print-only by design (no read -p, no [y/N] prompt, no conditional write):
# install-time interactive prompts replicate the hub-spoke topology this
# fragment exists to avoid (Krishnan 2026, "Why Coase Needs Hayek").
# ──────────────────────────────────────────────────────────────────────────────
if [ "$DRY_RUN" != true ]; then
    FRAGMENT_PATH="$TOOLKIT_DIR/shared/proactive_fragment.md"
    IMPORT_LINE="@$FRAGMENT_PATH"

    # Search candidate CLAUDE.md locations in priority order.
    CLAUDE_MD=""
    for candidate in "$PWD/CLAUDE.md" "$HOME/.claude/CLAUDE.md" "$HOME/CLAUDE.md"; do
        if [ -f "$candidate" ]; then
            CLAUDE_MD="$candidate"
            break
        fi
    done

    echo "================================================"
    echo "  Optional: Proactive Suggestion Fragment"
    echo "================================================"
    echo ""
    echo "A declarative fragment, one rule per command, is bundled at:"
    echo "  $FRAGMENT_PATH"
    echo ""
    echo "It is NOT auto-imported. Read it first to decide whether to opt in."
    echo ""

    if [ -n "$CLAUDE_MD" ]; then
        if grep -qF "$IMPORT_LINE" "$CLAUDE_MD" 2>/dev/null; then
            print_success "Fragment already imported in $CLAUDE_MD"
            echo "  No action needed (idempotent re-install detected)."
        else
            echo "To opt in, add ONE line to $CLAUDE_MD:"
            echo ""
            echo "  $IMPORT_LINE"
            echo ""
            echo "Then (recommended): delete any existing"
            echo "  '## Council of Agents — Proactive Suggestion Rule'"
            echo "section in your CLAUDE.md to avoid /coa firing twice per turn."
            echo "(The fragment's row 2 is its successor with a sharper Gate.)"
        fi
    else
        echo "No CLAUDE.md found at \$PWD/CLAUDE.md, ~/.claude/CLAUDE.md, or ~/CLAUDE.md."
        echo "When you create one, add this line to opt in:"
        echo ""
        echo "  $IMPORT_LINE"
    fi
    echo ""
fi

# Render command list from the arrays (avoids hand-maintained drift)
if [ "$MINIMAL" = true ]; then
    INSTALLED_LIST="/pcv"
    for c in "${SHARED_COMMANDS[@]}"; do INSTALLED_LIST="$INSTALLED_LIST, /$c"; done
else
    INSTALLED_LIST="/pcv"
    for c in "${SHARED_COMMANDS[@]}"; do INSTALLED_LIST="$INSTALLED_LIST, /$c"; done
    for c in "${STUDENT_ONLY[@]}";    do INSTALLED_LIST="$INSTALLED_LIST, /$c"; done
    for c in "${SKILLS[@]}";          do INSTALLED_LIST="$INSTALLED_LIST, /$c"; done
fi
echo "Commands installed: $INSTALLED_LIST"
echo "Council seat agents: ${SEAT_AGENTS[*]}"
if [ "$ADDON" = true ]; then
    echo "Add-on seat agents: ${ADDON_SEATS[*]}"
else
    echo "Add-on seats not copied (add them with: bash install.sh --addon-seats): ${ADDON_SEATS[*]}"
fi
echo ""
