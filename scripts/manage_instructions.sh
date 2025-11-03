#!/bin/bash
# Script para gestionar las instrucciones externas del MCP
# Usage: ./scripts/manage_instructions.sh [check|update|backup]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Paths
EXTERNAL_INSTRUCTIONS="/Users/esanz/Desktop/ia-mvp/project/server/InstructionsMCP/api_instructions.md"
LOCAL_INSTRUCTIONS_DIR="/Users/esanz/Desktop/ia-mvp/iCardsMCP/app/mcp/instructions"
LOCAL_INSTRUCTIONS="$LOCAL_INSTRUCTIONS_DIR/api_instructions.md"

echo -e "${BLUE}📖 MCP Instructions Manager${NC}"
echo "=============================="
echo

# Function to check if external instructions exist
check_external() {
    if [ -f "$EXTERNAL_INSTRUCTIONS" ]; then
        echo -e "${GREEN}✅ External instructions found: $EXTERNAL_INSTRUCTIONS${NC}"
        echo "   Size: $(wc -c < "$EXTERNAL_INSTRUCTIONS") bytes"
        echo "   Modified: $(stat -f "%Sm" "$EXTERNAL_INSTRUCTIONS")"
    else
        echo -e "${RED}❌ External instructions not found: $EXTERNAL_INSTRUCTIONS${NC}"
        return 1
    fi
}

# Function to check if local instructions exist
check_local() {
    if [ -f "$LOCAL_INSTRUCTIONS" ]; then
        echo -e "${YELLOW}⚠️  Local instructions still exist: $LOCAL_INSTRUCTIONS${NC}"
        echo "   This should be removed as we now use external instructions"
    else
        echo -e "${GREEN}✅ No local instructions found (correct)${NC}"
    fi
}

# Function to backup local instructions if they exist
backup_local() {
    if [ -f "$LOCAL_INSTRUCTIONS" ]; then
        BACKUP_FILE="$LOCAL_INSTRUCTIONS.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$LOCAL_INSTRUCTIONS" "$BACKUP_FILE"
        echo -e "${YELLOW}📦 Local instructions backed up to: $BACKUP_FILE${NC}"
    fi
}

# Function to show instructions info
show_info() {
    echo -e "${BLUE}📊 Instructions Status:${NC}"
    echo

    echo "External instructions:"
    if [ -f "$EXTERNAL_INSTRUCTIONS" ]; then
        echo "  ✅ Exists: $EXTERNAL_INSTRUCTIONS"
        echo "  📏 Size: $(wc -c < "$EXTERNAL_INSTRUCTIONS") bytes"
        echo "  🕒 Modified: $(stat -f "%Sm" "$EXTERNAL_INSTRUCTIONS")"
    else
        echo "  ❌ Missing: $EXTERNAL_INSTRUCTIONS"
    fi

    echo
    echo "Local instructions:"
    if [ -f "$LOCAL_INSTRUCTIONS" ]; then
        echo "  ⚠️  Still exists: $LOCAL_INSTRUCTIONS"
        echo "  📏 Size: $(wc -c < "$LOCAL_INSTRUCTIONS") bytes"
    else
        echo "  ✅ Cleaned up (correct)"
    fi

    echo
    echo "MCP Configuration:"
    echo "  📖 Instructions path: $EXTERNAL_INSTRUCTIONS"
    echo "  🔄 Auto-loads from external location"
}

# Function to clean up local instructions
cleanup_local() {
    if [ -f "$LOCAL_INSTRUCTIONS" ]; then
        echo -e "${YELLOW}🧹 Removing local instructions file...${NC}"
        backup_local
        rm "$LOCAL_INSTRUCTIONS"
        echo -e "${GREEN}✅ Local instructions removed${NC}"
    else
        echo -e "${GREEN}ℹ️  No local instructions to clean up${NC}"
    fi
}

# Function to validate instructions can be loaded
validate_loading() {
    echo -e "${BLUE}🔍 Testing instructions loading...${NC}"

    if [ ! -f "$EXTERNAL_INSTRUCTIONS" ]; then
        echo -e "${RED}❌ External instructions file not found${NC}"
        return 1
    fi

    # Try to read the file
    if head -5 "$EXTERNAL_INSTRUCTIONS" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ External instructions file is readable${NC}"
    else
        echo -e "${RED}❌ Cannot read external instructions file${NC}"
        return 1
    fi

    # Check if it contains expected content
    if grep -q "Flashcard Learning Platform" "$EXTERNAL_INSTRUCTIONS"; then
        echo -e "${GREEN}✅ External instructions contain expected content${NC}"
    else
        echo -e "${YELLOW}⚠️  External instructions may not contain expected content${NC}"
    fi
}

# Main logic
case "${1:-info}" in
    "check")
        echo "Checking instructions status..."
        check_external
        check_local
        validate_loading
        ;;
    "cleanup")
        echo "Cleaning up local instructions..."
        cleanup_local
        ;;
    "backup")
        echo "Backing up local instructions..."
        backup_local
        ;;
    "validate")
        echo "Validating instructions..."
        validate_loading
        ;;
    "info"|*)
        show_info
        echo
        echo -e "${BLUE}💡 Available commands:${NC}"
        echo "  check   - Check status of instructions"
        echo "  cleanup - Remove local instructions (recommended)"
        echo "  backup  - Backup local instructions before cleanup"
        echo "  validate- Test if instructions can be loaded"
        echo "  info    - Show current status (default)"
        ;;
esac

echo
echo -e "${GREEN}🎯 Remember: MCP now loads instructions from external location for centralized management!${NC}"
