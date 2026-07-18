#!/bin/bash

==============================================================================

Antigravity AI Toolchain Setup (Optimized for Matt Pocock's Skills)

==============================================================================

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

install_global() {
echo -e "${BLUE}[*] Installing global tools...${NC}"

# Ensure base dependencies exist
sudo apt update && sudo apt install -y nodejs npm

# Install uv if missing
if ! command -v uv &> /dev/null; then
    echo -e "${BLUE}[*] Installing uv...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

# Install graphify and agentmemory
npm install -g @agentmemory/agentmemory
uv tool install graphifyy

# Configure Antigravity MCP
echo -e "${BLUE}[*] Configuring Antigravity MCP...${NC}"
mkdir -p ~/.gemini/config

# We assume you have cloned the toolchain to ~/Github/antigravity_ai_toolchain
cat <<EOF > ~/.gemini/config/mcp_config.json


{
"mcpServers": {
"graphify": {
"command": "graphify",
"args": [
"mcp"
]
},
"agentmemory": {
"command": "npx",
"args": [
"-y",
"@agentmemory/agentmemory",
"--storage",
"./.memory",
"--mcp"
]
},
"toolchain-guardrail": {
"command": "uv",
"args": [
"run",
"$HOME/Github/antigravity_ai_toolchain/mcp_server.py"
]
}
}
}
EOF
echo -e "${GREEN}[+] Global setup complete!${NC}"
}

init_workspace() {
echo -e "${BLUE}=== Initializing Matt Pocock's Skills ===${NC}"

# Use Matt's official installer
npx skills@latest add mattpocock/skills

echo -e "${GREEN}[+] Workspace initialized.${NC}"
echo -e "${BLUE}Next step: Open your Antigravity IDE and run '/setup-matt-pocock-skills' in the agent chat.${NC}"


}

--- CLI Router ---

if [ "$1" == "global" ]; then
install_global
exit 0
elif [ "$1" == "workspace" ]; then
init_workspace
exit 0
else
echo -e "${RED}Error: Invalid or missing command.${NC}"
echo -e "${BLUE}Usage:${NC}"
echo "  ./setup-pocock-toolchain.sh global    # Run once to install CLI tools & configure IDE"
echo "  ./setup-pocock-toolchain.sh workspace # Run inside each new project folder"
exit 1
fi
