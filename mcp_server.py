# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "mcp",
#     "pyyaml",
# ]
# ///

"""
mcp_server.py — Opinionated MCP adapter for Matt Pocock's Agent Skills.

Acts as a "Guardrail" manager, forcing the AI to step through:
Phase 1: Grilling & Shared Language (CONTEXT.md)
Phase 2: Technical Spec (spec.md)
Phase 3: Ticket Breakdown (task.md)
Phase 4: Execution (TDD)
"""

import os
import yaml
import re
from pathlib import Path
import json
import subprocess
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "toolchain-guardrail",
    instructions=(
        "You are an expert AI orchestrator enforcing Matt Pocock's engineering methodology. "
        "You MUST run validate_state() before taking ANY action to determine the project phase. "
        "Follow the directives provided by validate_state() exactly. "
        "Use list_skills() to find exact skill references."
    ),
)

def get_skills_dir() -> Path:
    """Find the agents directory in the current workspace."""
    # Matt's skills installer usually creates an .agents folder
    return Path.cwd() / ".agents"

def parse_skill_md(file_path: Path):
    """Parse YAML frontmatter and Markdown content."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return None, ""
    
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if not match:
        return None, content
    
    try:
        return yaml.safe_load(match.group(1)), match.group(2)
    except yaml.YAMLError:
        return None, content

def bootstrap_workspace(cwd: Path):
    """Creates persistent domain documentation structures and guardrail rules if missing."""
    context_file = cwd / "CONTEXT.md"
    adrs_dir = cwd / "docs" / "adrs"
    agents_dir = cwd / ".agents"
    agents_rule_file = agents_dir / "AGENTS.md"

    if not context_file.exists():
        context_file.write_text(
            "# CONTEXT.md\n\n"
            "This file contains the **Ubiquitous Language** and domain model. "
            "Never delete it. Update it during `/grill-with-docs` sessions.\n\n"
            "## Glossary\n",
            encoding="utf-8"
        )
    
    if not adrs_dir.exists():
        adrs_dir.mkdir(parents=True, exist_ok=True)

    # Ensure .agents folder exists
    if not agents_dir.exists():
        agents_dir.mkdir(parents=True, exist_ok=True)

    # Write the process-guardrail rules to AGENTS.md so the IDE's custom rules system enforces it.
    guardrail_rules = (
        "# Antigravity Guardrail Rules\n\n"
        "> [!IMPORTANT]\n"
        "> Du er underlagt en streng proces-guardrail (toolchain-guardrail).\n"
        "> \n"
        "> 1. Før du foretager NOGEN form for kildekodeændringer eller opretter nye filer (undtagen dokumentationsfiler som `CONTEXT.md`, `spec.md` og `task.md`), SKAL du kalde `validate_state()` værktøjet.\n"
        "> 2. Hvis `validate_state()` returnerer et `STOP` direktiv (f.eks. fordi `spec.md` eller `task.md` mangler), er det strengt forbudt at skrive eller modificere kildekodefiler. Du skal stoppe og følge direktivets instruktioner (f.eks. køre en grill-session eller nedbryde opgaver).\n"
        "> 3. Du skal respektere og følge de foreskrevne faser nøje.\n"
    )
    agents_rule_file.write_text(guardrail_rules, encoding="utf-8")

@mcp.tool()
def list_skills() -> str:
    """List all available engineering skills (e.g. grill-with-docs, to-spec, tdd)."""
    skills_dir = get_skills_dir()
    if not skills_dir.exists():
        return json.dumps({"error": f"Skills directory not found at {skills_dir}. Run setup-pocock-toolchain.sh workspace."})
    
    skills = []
    for skill_path in skills_dir.rglob("*.md"):
        if skill_path.name in ["README.md", "CONTEXT.md", "CLAUDE.md", "AGENTS.md"]:
            continue
        frontmatter, _ = parse_skill_md(skill_path)
        if frontmatter:
            skills.append({
                "name": frontmatter.get("name", skill_path.stem),
                "description": frontmatter.get("description", ""),
                "skill_id": skill_path.stem
            })
    return json.dumps(skills, indent=2)

@mcp.tool()
def get_skill(skill_id: str) -> str:
    """Get the full content of an engineering skill by its ID."""
    skills_dir = get_skills_dir()
    
    # Search recursively for the skill markdown
    for skill_path in skills_dir.rglob(f"{skill_id}*.md"):
        _, markdown = parse_skill_md(skill_path)
        return markdown
        
    return f"Error: Skill '{skill_id}' not found."

@mcp.tool()
def validate_state(cwd: str = ".") -> str:
    """
    Evaluates the project state and commands the AI on what phase to execute.
    Fallback to current working directory if generic path provided.
    """
    # Robust absolute path handling
    root = Path(cwd).resolve() if cwd and cwd != "." else Path.cwd().resolve()
    bootstrap_workspace(root)
    
    # Case-insensitive check of existing files in project root
    files = [f.name.lower() for f in root.iterdir() if f.is_file()]
    
    report = {
        "spec_found": "spec.md" in files,
        "task_found": "task.md" in files,
        "phase": "",
        "directive": ""
    }
    
    if not report["spec_found"]:
        report["phase"] = "Phase 1: Discovery & Specification"
        report["directive"] = (
            "CRITICAL GUARDRAIL: STOP. No spec.md found. You are NOT allowed to write or modify codebase files yet. "
            "1. Invoke 'list_skills()' to find the exact name of the grilling skill (likely 'grill-with-docs'). "
            "2. Execute the grilling process (use the 'skill_grill_with_docs' tool) and document findings in CONTEXT.md. "
            "3. Generate spec.md using the 'to-spec' blueprint before proceeding."
        )
    elif not report["task_found"]:
        report["phase"] = "Phase 2: Task Breakdown"
        report["directive"] = (
            "CRITICAL GUARDRAIL: STOP. spec.md exists, but task.md is missing. "
            "You cannot code blindly. Break down the specifications into clear, isolated, "
            "vertical tracer-bullet slices inside task.md first (use the breakdown skill, e.g. 'skill_to_issues' or 'skill_to_tickets')."
        )
    else:
        report["phase"] = "Phase 3: Execution"
        report["directive"] = (
            "GO. Project state verified. Read task.md and proceed with implementation using TDD (e.g. use 'skill_tdd')."
        )
        
    return json.dumps(report, indent=2)

# --- Dynamic Skill Tool Registration ---

def create_skill_tool(skill_id: str, skill_path: Path, description: str, markdown_content: str):
    """Factory function to dynamically create executable MCP tools from Matt's markdown skills."""
    def run_skill(context: str = "") -> str:
        # Check for scripts folder next to the skill markdown file
        script_dir = skill_path.parent / "scripts"
        script_output = ""
        
        if script_dir.exists() and script_dir.is_dir():
            scripts = [f for f in script_dir.iterdir() if f.is_file()]
            if scripts:
                # Find a python or shell script
                script_to_run = None
                for s in scripts:
                    if s.suffix in [".py", ".sh", ".bash"]:
                        script_to_run = s
                        break
                if not script_to_run:
                    script_to_run = scripts[0]
                
                try:
                    cmd = []
                    if script_to_run.suffix == ".py":
                        cmd = ["python3", str(script_to_run)]
                    elif script_to_run.suffix in [".sh", ".bash"]:
                        cmd = ["bash", str(script_to_run)]
                    else:
                        cmd = [str(script_to_run)]
                    
                    env = os.environ.copy()
                    env["SKILL_CONTEXT"] = context
                    
                    res = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        env=env,
                        cwd=Path.cwd()
                    )
                    script_output = (
                        f"\n\n--- [Script Execution: {script_to_run.name}] ---\n"
                        f"Exit Code: {res.returncode}\n"
                        f"Stdout:\n{res.stdout}\n"
                        f"Stderr:\n{res.stderr}\n"
                    )
                except Exception as e:
                    script_output = f"\n\n--- [Script Execution Failed] ---\nError: {str(e)}"
                    
        return (
            f"# Skill: {skill_id}\n\n"
            f"## Instructions\n"
            f"{markdown_content}\n"
            f"{script_output}"
        )
    
    # FastMCP uses the function name and docstring for MCP registration.
    # Replace invalid hyphens with underscores.
    safe_name = f"skill_{skill_id.lower().replace('-', '_')}"
    run_skill.__name__ = safe_name
    run_skill.__doc__ = f"Executes and loads instructions for skill '{skill_id}'.\n\nDescription: {description}"
    return run_skill

def register_dynamic_skills():
    """Scan and register all Markdown skills in .agents/ recursively as MCP tools."""
    skills_dir = get_skills_dir()
    if not skills_dir.exists():
        return
    
    for skill_path in skills_dir.rglob("*.md"):
        if skill_path.name in ["README.md", "CONTEXT.md", "CLAUDE.md", "AGENTS.md"]:
            continue
        
        frontmatter, markdown_content = parse_skill_md(skill_path)
        if frontmatter:
            skill_id = skill_path.stem
            description = frontmatter.get("description", f"Run the {skill_id} skill.")
            
            try:
                # Create the dynamic function and register it as an MCP tool
                tool_func = create_skill_tool(skill_id, skill_path, description, markdown_content)
                mcp.tool()(tool_func)
            except Exception as e:
                # Silently catch registration issues to prevent server crash
                pass

# Register skills dynamically during import/startup
register_dynamic_skills()

if __name__ == "__main__":
    mcp.run()
