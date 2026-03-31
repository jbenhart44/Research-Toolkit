#!/bin/bash
# AI-Assisted Research Toolkit — Installer
# Usage:
#   bash install.sh               # Full student toolkit (12 commands)
#   bash install.sh --minimal     # Instructor toolkit (6 commands)
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
    echo "  bash install.sh               Full student toolkit (12 commands)"
    echo "  bash install.sh --minimal     Instructor toolkit (6 commands)"
    echo "  bash install.sh --help        Show this help"
    echo ""
    echo "What gets installed:"
    echo "  Commands    → ~/.claude/commands/"
    echo "  PCV skill   → ~/.claude/skills/pcv/"
    echo "  PCV agents  → ~/.claude/agents/"
    echo "  Config      → ~/.claude/toolkit-config.md (if not present)"
    echo ""
    echo "Existing files are backed up before overwriting."
    exit 0
}

# Parse arguments
MINIMAL=false
for arg in "$@"; do
    case $arg in
        --minimal) MINIMAL=true ;;
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
mkdir -p "$COMMANDS_DIR"
mkdir -p "$SKILLS_DIR/pcv"
mkdir -p "$AGENTS_DIR"

# Define command sets
SHARED_COMMANDS=(coa pace improve quarto pdftotxt)
STUDENT_ONLY=(startup dailysummary weeklysummary commit simplify pcv-research)

# Install shared commands (both products)
echo "Installing shared commands..."
for cmd in "${SHARED_COMMANDS[@]}"; do
    src="$TOOLKIT_DIR/shared/commands/$cmd.md"
    dst="$COMMANDS_DIR/$cmd.md"
    if [ -f "$src" ]; then
        if [ -f "$dst" ]; then
            cp "$dst" "$dst.bak"
            print_warning "Backed up existing $cmd.md → $cmd.md.bak"
        fi
        cp "$src" "$dst"
        print_success "$cmd.md"
    else
        print_error "$cmd.md not found in toolkit"
    fi
done

# Install student-only commands (unless --minimal)
if [ "$MINIMAL" = false ]; then
    echo ""
    echo "Installing student workflow commands..."
    for cmd in "${STUDENT_ONLY[@]}"; do
        src="$TOOLKIT_DIR/shared/commands/$cmd.md"
        dst="$COMMANDS_DIR/$cmd.md"
        if [ -f "$src" ]; then
            if [ -f "$dst" ]; then
                cp "$dst" "$dst.bak"
                print_warning "Backed up existing $cmd.md → $cmd.md.bak"
            fi
            cp "$src" "$dst"
            print_success "$cmd.md"
        else
            print_error "$cmd.md not found in toolkit"
        fi
    done
fi

# Install PCV skill files
echo ""
echo "Installing PCV v3.9..."
for f in "$TOOLKIT_DIR"/pcv/skill/*; do
    fname=$(basename "$f")
    dst="$SKILLS_DIR/pcv/$fname"
    if [ -f "$dst" ]; then
        cp "$dst" "$dst.bak"
    fi
    cp "$f" "$dst"
    print_success "pcv/$fname"
done

# Install PCV agent files
echo ""
echo "Installing PCV agents..."
for f in "$TOOLKIT_DIR"/pcv/agents/*; do
    fname=$(basename "$f")
    dst="$AGENTS_DIR/$fname"
    if [ -f "$dst" ]; then
        cp "$dst" "$dst.bak"
    fi
    cp "$f" "$dst"
    print_success "agents/$fname"
done

# Install config template (only if not present)
if [ ! -f "$CONFIG_FILE" ]; then
    echo ""
    echo "Creating configuration template..."
    cp "$TOOLKIT_DIR/toolkit-config.md" "$CONFIG_FILE"
    print_success "toolkit-config.md (edit this to match your project)"
else
    print_warning "toolkit-config.md already exists — not overwriting"
fi

# Summary
echo ""
echo "================================================"
if [ "$MINIMAL" = true ]; then
    echo "  Instructor Toolkit installed (6 commands + PCV)"
else
    echo "  Student Toolkit installed (12 commands + PCV)"
fi
echo "================================================"
echo ""
echo "Next steps:"
echo "  1. Edit ~/.claude/toolkit-config.md with your project details"
echo "  2. Open Claude Code in your project directory"
echo "  3. Type /pcv to start structured planning"
echo ""
if [ "$MINIMAL" = true ]; then
    echo "Commands installed: /pcv, /coa, /pace, /improve, /quarto, /pdftotxt"
else
    echo "Commands installed: /pcv, /coa, /pace, /pcv-research, /improve,"
    echo "  /quarto, /pdftotxt, /startup, /dailysummary, /weeklysummary,"
    echo "  /commit, /simplify"
fi
echo ""
