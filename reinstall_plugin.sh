#!/bin/bash

# Script to reinstall pytest-jsonschema-snapshot plugin
# Used for debugging updates

set -e  # Abort on errors

echo "Starting pytest-jsonschema-snapshot plugin reinstall..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Removing old version of the plugin...${NC}"
pip uninstall pytest-jsonschema-snapshot -y 2>/dev/null || echo -e "${YELLOW}Warning: plugin was not installed previously${NC}"

echo -e "${BLUE}Cleaning pip cache...${NC}"
pip cache purge

echo -e "${BLUE}Cleaning Python cache...${NC}"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

echo -e "${BLUE}Cleaning build directory...${NC}"
rm -rf build/ dist/ *.egg-info/ 2>/dev/null || true

echo -e "${BLUE}Rebuilding package...${NC}"
python3 -m build

echo -e "${BLUE}Installing plugin in development mode...${NC}"
pip install -e .

echo -e "${BLUE}Checking plugin installation...${NC}"
if pip list | grep -q pytest-jsonschema-snapshot; then
    echo -e "${GREEN}Plugin installed successfully!${NC}"
    pip show pytest-jsonschema-snapshot
else
    echo -e "${RED}Error: plugin not found after installation${NC}"
    exit 1
fi

echo -e "${BLUE}Checking if pytest sees the plugin...${NC}"
if pytest --help | grep -q "schemashot"; then
    echo -e "${GREEN}Pytest successfully detected the plugin!${NC}"
else
    echo -e "${YELLOW}Warning: pytest did not detect plugin options${NC}"
fi

#echo -e "${BLUE}Running basic tests...${NC}"
#pytest tests/ -v

echo -e "${GREEN}Plugin reinstall completed successfully!${NC}"
echo -e "${BLUE}Now you can test plugin updates${NC}"

