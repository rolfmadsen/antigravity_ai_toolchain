```markdown
# 🚀 Antigravity AI Toolchain Setup Guide

A highly-opinionated standard operating procedure for integrating **Graphify** (codebase AST mapping), **Agentmemory** (persistent AI context), and **Matt Pocock's Skills** into the Google Antigravity IDE.

This setup is optimized for TS/Node/React environments. It introduces a **Custom Guardrail MCP** that acts as an AI Tech Lead, refusing to let the AI write code until a rigorous ZeeSpec/Grilling session and ticket breakdown are completed.

## 🏗️ 1. Architecture Overview

To achieve strict engineering discipline and project-level isolation, this toolchain relies entirely on the **Model Context Protocol (MCP)**:

**1. Context & Memory Servers**
- **Graphify:** Maps your codebase into a queryable graph.
- **Agentmemory:** Manages a local vector database (`./.memory`), allowing AI memory to travel with your Git branch.

**2. The Guardrail Server (Opinionated Workflow)**
- **Agent-Skills (`mcp_server.py`):** A custom Python server that wraps Matt Pocock's static Markdown skills. It evaluates your workspace state and throws hard `STOP` commands if the AI attempts to code without first establishing a Ubiquitous Language (`CONTEXT.md`), a Technical Spec (`spec.md`), and Tracer-Bullet Tickets (`task.md`).

## 🛠️ 2. Global Installation

We use a single bash script to install the base CLI tools and configure your IDE to talk to the MCP servers. 

Run this on your machine to install `uv`, `npm`, `graphify`, and configure Antigravity:

```bash
chmod +x setup-pocock-toolchain.sh
./setup-pocock-toolchain.sh global

```

## 📁 3. Workspace Initialization (Per Project)

When starting a new project or cloning an existing one, run the workspace setup command.

```bash
cd ~/your/new/project
~/Github/antigravity_ai_toolchain/setup-pocock-toolchain.sh workspace

```

**What this does automatically:**

1. Installs Matt Pocock's official skills into the project.
2. Creates a `.graphifyignore` file (ignoring `node_modules`, `dist`, etc.).
3. Readies the directory for the strict Guardrail workflow.

## ⚙️ 4. Antigravity IDE Integration (MCP Config)

If you ran the global script above, your `~/.gemini/config/mcp_config.json` is already configured. For reference, it automatically boots all three servers:

```json
{
  "mcpServers": {
    "graphify": {
      "command": "graphify",
      "args": ["mcp"]
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
    "agent-skills": {
      "command": "uv",
      "args": [
        "run",
        "$HOME/Github/antigravity_ai_toolchain/mcp_server.py"
      ]
    }
  }
}

```

## 🔄 5. The Opinionated Workflow

Once configured, your AI agent operates on a strict State Machine enforced by `mcp_server.py`. The agent *cannot* skip steps.

1. **Phase 1: Discovery (The Grilling)**
* *Trigger:* No `spec.md` exists.
* *Action:* The AI is forced to use `/grill-with-docs` (using the 5W1H ZeeSpec model) to establish a shared dictionary in `CONTEXT.md` before it writes the technical `spec.md`.


2. **Phase 2: Vertical Slices**
* *Trigger:* `spec.md` exists, but no `task.md` exists.
* *Action:* The AI breaks the spec down into end-to-end "tracer bullet" tickets.


3. **Phase 3: Execution (TDD)**
* *Trigger:* Both `spec.md` and `task.md` exist.
* *Action:* The AI executes the next ticket using `/tdd` (Red-Green-Refactor) and finishes with `/code-review`.



✨ **The Benefit:** When you commit your code, include `.memory/` and `CONTEXT.md`. If you check out an older branch or a colleague pulls your code, the AI agent's memory and domain knowledge roll back or update perfectly to match that specific branch!

```

```
