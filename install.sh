#!/bin/bash
set -e

# cwp-claude-marketplace installer
# Usage: curl -fsSL https://raw.githubusercontent.com/codewithpassion/cwp-claude-marketplace/main/install.sh | bash
# With specific command: curl -fsSL ... | bash -s -- --cmd mclaude

REPO="codewithpassion/cwp-claude-marketplace"
MARKETPLACE="cwp-claude-marketplace"
CLAUDE_CMD="claude"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --cmd)
            CLAUDE_CMD="$2"
            shift 2
            ;;
        --scope)
            SCOPE="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  cwp-claude-marketplace installer${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Detect cc-mirror installation
CC_MIRROR_DIR="$HOME/.cc-mirror"
CC_MIRROR_VARIANTS=()

if [[ -d "$CC_MIRROR_DIR" ]]; then
    echo -e "${CYAN}cc-mirror detected!${NC}"
    echo ""

    # Find all variants
    for variant_dir in "$CC_MIRROR_DIR"/*/; do
        if [[ -f "${variant_dir}variant.json" ]]; then
            variant_name=$(basename "$variant_dir")
            variant_provider=$(grep -o '"provider": *"[^"]*"' "${variant_dir}variant.json" | cut -d'"' -f4)
            CC_MIRROR_VARIANTS+=("$variant_name|$variant_provider")
        fi
    done

    # If no --cmd was specified and we have variants, ask the user
    if [[ "$CLAUDE_CMD" == "claude" && ${#CC_MIRROR_VARIANTS[@]} -gt 0 ]]; then
        echo -e "${YELLOW}Available Claude commands:${NC}"
        echo ""
        echo -e "  ${GREEN}1)${NC} claude (default)"

        i=2
        for variant in "${CC_MIRROR_VARIANTS[@]}"; do
            name="${variant%|*}"
            provider="${variant#*|}"
            echo -e "  ${GREEN}${i})${NC} ${name} (${provider})"
            ((i++))
        done
        echo ""

        echo -e "${YELLOW}Which command do you want to use? [1-$((i-1))]${NC} "
        read -r choice

        if [[ "$choice" =~ ^[0-9]+$ ]]; then
            if [[ "$choice" -eq 1 ]]; then
                CLAUDE_CMD="claude"
            elif [[ "$choice" -ge 2 && "$choice" -lt "$i" ]]; then
                idx=$((choice - 2))
                variant="${CC_MIRROR_VARIANTS[$idx]}"
                CLAUDE_CMD="${variant%|*}"
            fi
        fi
        echo ""
    fi
fi

# Check if the selected claude command is available
if ! command -v "$CLAUDE_CMD" &> /dev/null; then
    echo -e "${RED}Error: '${CLAUDE_CMD}' is not installed or not in PATH${NC}"
    echo ""
    echo "Please install Claude Code first:"
    echo "  https://docs.anthropic.com/en/docs/claude-code/quickstart"
    exit 1
fi

# Check claude version
VERSION=$($CLAUDE_CMD --version 2>/dev/null | head -1 || echo "unknown")
echo -e "${GREEN}Using: ${CLAUDE_CMD}${NC}"
echo -e "${GREEN}Version: ${VERSION}${NC}"
echo ""

# Build scope flag if specified
SCOPE_FLAG=""
if [[ -n "$SCOPE" ]]; then
    SCOPE_FLAG=" --scope $SCOPE"
    echo -e "${CYAN}Installation scope: ${SCOPE}${NC}"
    echo ""
fi

# Define the commands to run
COMMANDS=(
    "${CLAUDE_CMD} plugin marketplace add ${REPO}"
    "${CLAUDE_CMD} plugin install cwp-claude-framework@${MARKETPLACE}${SCOPE_FLAG}"
    "${CLAUDE_CMD} plugin install cwp-how-i-vibe@${MARKETPLACE}${SCOPE_FLAG}"
)

# Show what will be executed
echo -e "${YELLOW}The following commands will be executed:${NC}"
echo ""
for cmd in "${COMMANDS[@]}"; do
    echo -e "  ${BLUE}\$${NC} ${cmd}"
done
echo ""

# Ask for confirmation
echo -e "${YELLOW}Do you want to proceed? [y/N]${NC} "
read -r response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Installation cancelled."
    exit 0
fi

echo ""
echo -e "${GREEN}Installing...${NC}"
echo ""

# Execute each command
for cmd in "${COMMANDS[@]}"; do
    echo -e "${BLUE}\$${NC} ${cmd}"
    if eval "$cmd"; then
        echo -e "${GREEN}Done${NC}"
    else
        echo -e "${RED}Failed${NC}"
        exit 1
    fi
    echo ""
done

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Installation complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "You can now use the installed plugins in Claude Code."
echo ""
echo "Available commands:"
echo "  - View plugins:   ${CLAUDE_CMD} plugin list --installed"
echo "  - Update:         ${CLAUDE_CMD} plugin marketplace update ${MARKETPLACE}"
echo ""
