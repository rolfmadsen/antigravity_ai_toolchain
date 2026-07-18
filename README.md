# 🚀 Antigravity AI Toolchain Setup Guide

A complete standard operating procedure for integrating Graphify (codebase AST mapping), Agentmemory (persistent, versionable AI context), and Matt Pocock's Skills (TDD/workflow prompts) into the Google Antigravity IDE.

This setup is optimized for TS/Node/React environments and focuses on project-level scoping, ensuring your AI's memory and strict skill workflows travel seamlessly with your Git branch.

## 🏗️ 1. Architecture Overview

To achieve project-level isolation, this toolchain uses two different integration methods based on the tool's function:

Dynamic Data (MCP Servers): Tools that require active compute, databases, or real-time searching run via the Model Context Protocol (MCP).
1. Graphify: Runs an MCP server to map your TS/Node codebase into a queryable graph.
2. Agentmemory: Runs an MCP server to manage a local vector database (./.memory), allowing memory to travel with the Git branch.

Static Workflows (Local Files):
1. Matt Pocock's Skills: Installed locally via CLI into the repository. These are static prompt rules and instructions that enforce engineering workflows (like TDD). They don't need a server; the agent just reads them from the directory.

## 🛠️ 2. Global Installation

Install the base CLI tools required to run the servers.

### Install Agentmemory globally via npm
```bash
npm install -g @agentmemory/agentmemory
```

### Install Graphify via uv (recommended for Python environment isolation)
```bash
uv tool install graphifyy
```

## 📁 3. Workspace Initialization (Per Project)

When starting a new project or cloning an existing one, set up the workspace for Graphify, Git-tracked memory, and your engineering skills.

**Step 3.1: Configure Ignore Rules**

Create a .graphifyignore file in your root to prevent indexing massive dependency folders:

#### TS/Node/React
node_modules/
dist/
build/
.next/
coverage/

#### Rust / Python (occasional)
target/
venv/
__pycache__/


**Step 3.2: Initialize Graphify**

Run this in the root of your workspace to create local graph mappings specific to this project:

```bash
graphify install --project
```

**Step 3.3: Install Matt Pocock's Skills**

Instead of running a background server for skills, install Matt Pocock's collection directly into your project. This allows you to version-control your workflow standard alongside your code.

## Install the skills bundle into your project
```bash
npx skills add mattpocock/skills
```

Once installed, use the setup command in your agent or terminal to configure your issue tracker and docs structure:

> /setup-matt-pocock-skills

## ⚙️ 4. Antigravity IDE Integration (MCP Config)

Configure Antigravity to automatically boot Graphify and your local Git-tracked Agentmemory databases whenever you open the IDE.

Open ~/.gemini/config/mcp_config.json and replace its contents with the following:

```json
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
    }
  }
}
```

Note: Matt Pocock's skills are not included in this JSON because they are read directly from your local project files (.claude/skills), not from a background server.

## 🔄 5. Recommended Workflow

Coding: Open your project in Antigravity. Use Matt Pocock's slash commands (like /tdd or /improve-codebase-architecture) to guide the agent.

Context & Memory: The agent will automatically use the Graphify MCP server for architectural context and the Agentmemory MCP server (reading/writing to ./.memory) to remember past decisions.

Version Control: When you commit your code, include the .memory folder and your local skills directory.

```bash
git add src/ .memory/ .claude/
git commit -m "feat: implement auth with agent skills and memory"
```

✨ The Benefit: If you check out an older branch or a colleague pulls your code, the AI agent's memory and strict skill workflows roll back or update perfectly to match the state of that specific branch!
