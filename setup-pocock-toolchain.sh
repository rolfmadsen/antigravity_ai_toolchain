#!/bin/bash

# ==============================================================================
# Antigravity AI Toolchain Setup (Optimized for Matt Pocock's Skills)
# ==============================================================================

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

install_global() {
    echo -e "${BLUE}[*] Installing global tools...${NC}"

    # Get absolute path of this script's directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

    # Ensure base dependencies exist
    sudo apt update && sudo apt install -y nodejs npm

    # Install uv if missing
    if ! command -v uv &> /dev/null; then
        echo -e "${BLUE}[*] Installing uv...${NC}"
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source $HOME/.cargo/env
    fi

    # Ensure local bin is in PATH for the rest of this installation process
    export PATH="$HOME/.local/bin:$PATH"

    # Install graphify and agentmemory
    npm install -g @agentmemory/agentmemory @agentmemory/mcp
    uv tool install graphifyy

    # Configure Antigravity MCP
    echo -e "${BLUE}[*] Configuring Antigravity MCP...${NC}"
    mkdir -p ~/.gemini/config

    cat <<EOF > ~/.gemini/config/mcp_config.json
{
  "mcpServers": {
    "graphify": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "graphifyy[mcp]",
        "python",
        "-m",
        "graphify.serve",
        "graphify-out/graph.json"
      ]
    },
    "agentmemory": {
      "command": "python3",
      "args": [
        "$SCRIPT_DIR/start_agentmemory.py"
      ]
    },
    "toolchain-guardrail": {
      "command": "uv",
      "args": [
        "run",
        "$SCRIPT_DIR/mcp_server.py"
      ]
    }
  }
}
EOF
    echo -e "${GREEN}[+] Global setup complete!${NC}"
}

init_workspace() {
    echo -e "${BLUE}=== Initializing Workspace ===${NC}"

    # Opret .graphifyignore automatisk for at undgå at parse node_modules m.m.
    echo -e "${BLUE}[*] Creating .graphifyignore...${NC}"
    cat <<EOF > .graphifyignore
node_modules/
dist/
.git/
.memory/
.agents/
.venv/
EOF

    # Opret venv og installer afhængigheder lokalt til brug for IDE'ens linter
    echo -e "${BLUE}[*] Setting up local virtual environment (.venv) for IDE...${NC}"
    uv venv
    source .venv/bin/activate
    uv pip install mcp pyyaml "graphifyy[mcp]"

    # Installer Matt Pocock's skills (non-interaktivt)
    echo -e "${BLUE}[*] Installing Matt Pocock's skills...${NC}"
    npx skills@latest add mattpocock/skills --all --yes

    # Byg Graphify-indeks første gang for at forhindre timeout ved MCP opstart (kun kildekode, ingen LLM-nøgler påkrævet)
    echo -e "${BLUE}[*] Pre-building Graphify index (this avoids MCP startup timeout)...${NC}"
    graphify . --code-only

    echo -e "${GREEN}[+] Workspace initialized successfully.${NC}"
    echo -e "${BLUE}Next step: Open your Antigravity IDE and run '/setup-matt-pocock-skills' in the agent chat.${NC}"
}

# --- CLI Router ---

if [ "$1" == "global" ]; then
    install_global
    exit 0
elif [ "$1" == "workspace" ]; then
    init_workspace
    exit 0
else
    echo -e "${RED}Error: Invalid or missing command.${NC}"
    echo -e "${BLUE}Usage:${NC}"
    echo "  $0 global    # Run once to install CLI tools & configure IDE"
    echo "  $0 workspace # Run inside each new project folder"
    exit 1
fi
