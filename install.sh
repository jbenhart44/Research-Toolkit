#!/bin/bash
# Research Amp Toolkit — Installer
# Usage (counts derived at runtime — see SHARED_COMMANDS / STUDENT_ONLY arrays):
#   bash install.sh               # Full toolkit
#   bash install.sh --minimal     # Instructor toolkit
#   bash install.sh --hooks       # Also install optional hooks (token budget, folder guard)
#   bash install.sh --dry-run     # Show what would be installed without copying
#   bash install.sh --help        # Show this help

set -e

TOOLKIT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMMANDS_DIR="$HOME/.claude/commands"
SKILLS_DIR="$HOME/.claude/skills"
AGENTS_DIR="$HOME/.claude/agents"
CONFIG_FILE="$HOME/.claude/toolkit-config.md"

# Colors (if terminal supports them)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Command sets — single source of truth for both install paths AND banner counts.
# Defined BEFORE show_help() so --help can render correct counts without running install.
SHARED_COMMANDS=(coa pace improve quarto readable help review)
STUDENT_ONLY=(startup dailysummary weeklysummary commit simplify audit runlog)
SHARED_COUNT=${#SHARED_COMMANDS[@]}
STUDENT_COUNT=${#STUDENT_ONLY[@]}
FULL_COUNT=$((SHARED_COUNT + STUDENT_COUNT + 1))   # +1 for /pcv (skill)
MIN_COUNT=$((SHARED_COUNT + 1))                    # +1 for /pcv (skill)

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
    echo "  bash install.sh --dry-run     Show what would be installed without copying"
    echo "  bash install.sh --help        Show this help"
    echo ""
    echo "What gets installed:"
    echo "  Commands    → ~/.claude/commands/"
    echo "  PCV skill   → ~/.claude/skills/pcv/"
    echo "  PCV agents  → ~/.claude/agents/"
    echo "  Config      → ~/.claude/toolkit-config.md (if not present)"
    echo "  Hooks       → ~/.claude/hooks/ (optional, with --hooks)"
    echo ""
    echo "Existing files are backed up before overwriting."
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
for arg in "$@"; do
    case $arg in
        --minimal) MINIMAL=true ;;
        --dry-run) DRY_RUN=true ;;
        --hooks) INSTALL_HOOKS=true ;;
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
    # Backup existing pcv skill dir if present (single snapshot, not per-file)
    if [ -d "$SKILLS_DIR/pcv" ] && [ "$(ls -A "$SKILLS_DIR/pcv" 2>/dev/null)" ]; then
        BACKUP_DIR="$SKILLS_DIR/pcv.bak.$(date +%Y%m%d-%H%M%S)"
        cp -r "$SKILLS_DIR/pcv" "$BACKUP_DIR"
        print_warning "Backed up existing pcv skill → $(basename "$BACKUP_DIR")"
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

# Install config template (only if not present)
if [ ! -f "$CONFIG_FILE" ]; then
    echo ""
    echo "Creating configuration template..."
    if [ "$DRY_RUN" = true ]; then
        print_success "Would install: toolkit-config.md → $CONFIG_FILE"
    else
        cp "$TOOLKIT_DIR/toolkit-config.md" "$CONFIG_FILE"
        print_success "toolkit-config.md (edit this to match your project)"
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
    for f in "$TOOLKIT_DIR"/hooks/*.sh; do
        fname=$(basename "$f")
        install_file "$f" "$HOOKS_DIR/$fname" "hooks/$fname"
    done
    if [ "$DRY_RUN" = false ]; then
        chmod +x "$HOOKS_DIR"/*.sh 2>/dev/null
    fi
    echo ""
    print_warning "Hooks installed but NOT registered. To activate them,"
    print_warning "add hook entries to your .claude/settings.json."
    print_warning "See hooks/README.md for registration instructions."
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
    echo "  2. Edit ~/.claude/toolkit-config.md with your project details."
    echo "  3. Open Claude Code in your project directory and type /pcv to start structured planning."
fi
echo ""
# Render command list from the arrays (avoids hand-maintained drift)
if [ "$MINIMAL" = true ]; then
    INSTALLED_LIST="/pcv"
    for c in "${SHARED_COMMANDS[@]}"; do INSTALLED_LIST="$INSTALLED_LIST, /$c"; done
else
    INSTALLED_LIST="/pcv"
    for c in "${SHARED_COMMANDS[@]}"; do INSTALLED_LIST="$INSTALLED_LIST, /$c"; done
    for c in "${STUDENT_ONLY[@]}";    do INSTALLED_LIST="$INSTALLED_LIST, /$c"; done
fi
echo "Commands installed: $INSTALLED_LIST"
echo ""
