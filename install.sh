#!/bin/bash
# AI-Assisted Research Toolkit — Installer
# Usage:
#   bash install.sh               # Full student toolkit (11 commands)
#   bash install.sh --minimal     # Instructor toolkit (6 commands)
#   bash install.sh --hooks        # Also install optional hooks (token budget, folder guard)
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

print_header() {
    echo ""
    echo "================================================"
    echo "  AI-Assisted Research Toolkit Installer"
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
    echo "AI-Assisted Research Toolkit — Installer"
    echo ""
    echo "Usage:"
    echo "  bash install.sh               Full student toolkit (11 commands)"
    echo "  bash install.sh --minimal     Instructor toolkit (6 commands)"
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
    for d in "$COMMANDS_DIR" "$SKILLS_DIR/pcv" "$SKILLS_DIR/pcvjake" "$AGENTS_DIR"; do
        if [ ! -d "$d" ]; then
            print_success "Would create: $d"
        fi
    done
else
    mkdir -p "$COMMANDS_DIR"
    mkdir -p "$SKILLS_DIR/pcv"
    mkdir -p "$SKILLS_DIR/pcvjake"
    mkdir -p "$AGENTS_DIR"
fi

# Define command sets
SHARED_COMMANDS=(coa pace improve quarto pdftotxt)
STUDENT_ONLY=(startup dailysummary weeklysummary commit simplify pcv-research pcv-researchJake)

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

# Install PCV skill files
echo ""
echo "Installing PCV v3.9..."
for f in "$TOOLKIT_DIR"/pcv/skill/*; do
    fname=$(basename "$f")
    install_file "$f" "$SKILLS_DIR/pcv/$fname" "pcv/$fname"
done

# Install PCV agent files
echo ""
echo "Installing PCV agents..."
for f in "$TOOLKIT_DIR"/pcv/agents/*; do
    fname=$(basename "$f")
    install_file "$f" "$AGENTS_DIR/$fname" "agents/$fname"
done

# Install pcvJake skill files (student only)
if [ "$MINIMAL" = false ]; then
    echo ""
    echo "Installing /pcvJake (toolkit-integrated PCV)..."
    for f in "$TOOLKIT_DIR"/pcvjake/skill/*; do
        fname=$(basename "$f")
        install_file "$f" "$SKILLS_DIR/pcvjake/$fname" "pcvjake/$fname"
    done
    # pcvJake agents go to the shared agents directory
    for f in "$TOOLKIT_DIR"/pcvjake/agents/*; do
        fname="pcvjake-$fname"
        install_file "$f" "$AGENTS_DIR/pcvjake-$(basename "$f")" "agents/pcvjake-$(basename "$f")"
    done
fi

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
        echo "  Instructor Toolkit dry run (6 commands + PCV)"
    else
        echo "  Student Toolkit dry run (11 commands + PCV)"
    fi
    echo "================================================"
    echo ""
    echo "This was a dry run. No files were modified."
    echo "Run without --dry-run to install."
else
    if [ "$MINIMAL" = true ]; then
        echo "  Instructor Toolkit installed (6 commands + PCV)"
    else
        echo "  Student Toolkit installed (11 commands + PCV)"
    fi
    echo "================================================"
    echo ""
    echo "Next steps:"
    echo "  1. Edit ~/.claude/toolkit-config.md with your project details"
    echo "  2. Open Claude Code in your project directory"
    echo "  3. Type /pcv to start structured planning, or /pcvJake for toolkit-integrated PCV"
fi
echo ""
if [ "$MINIMAL" = true ]; then
    echo "Commands installed: /pcv, /coa, /pace, /improve, /quarto, /pdftotxt"
else
    echo "Commands installed: /pcv, /pcvJake, /coa, /pace, /pcv-research,"
    echo "  /pcv-researchJake, /improve, /quarto, /pdftotxt, /startup,"
    echo "  /dailysummary, /weeklysummary, /commit, /simplify"
fi
echo ""
