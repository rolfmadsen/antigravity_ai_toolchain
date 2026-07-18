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
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "agent-skills",
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
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if not match:
        return None, content
    
    try:
        return yaml.safe_load(match.group(1)), match.group(2)
    except yaml.YAMLError:
        return None, match.group(2)

def bootstrap_workspace(cwd: Path):
    """Creates persistent domain documentation structures if missing."""
    context_file = cwd / "CONTEXT.md"
    adrs_dir = cwd / "docs" / "adrs"

    if not context_file.exists():
        context_file.write_text(
            "# CONTEXT.md\n\n"
            "This file contains the **Ubiquitous Language** and domain model. "
            "Never delete it. Update it during `/grill-with-docs` sessions.\n\n"
            "## Glossary\n"
        )
    
    if not adrs_dir.exists():
        adrs_dir.mkdir(parents=True, exist_ok=True)

@mcp.tool()
def list_skills() -> str:
    """List all available engineering skills (e.g. grill-with-docs, to-spec, tdd)."""
    skills_dir = get_skills_dir()
    if not skills_dir.exists():
        return json.dumps({"error": f"Skills directory not found at {skills_dir}. Run setup-pocock-toolchain.sh workspace."})
    
    skills = []
    for skill_path in skills_dir.rglob("*.md"):
        if skill_path.name in ["README.md", "CONTEXT.md", "CLAUDE.md"]:
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
    Bootstrap domain files automatically on first run.
    """
    root = Path(cwd).resolve()
    bootstrap_workspace(root)
    
    files = [f.name.lower() for f in root.glob("*")]
    
    report = {
        "spec_found": "spec.md" in files,
        "task_found": "task.md" in files,
        "phase": "",
        "directive": ""
    }
    
    if not report["spec_found"]:
        report["phase"] = "Phase 1: Discovery & Specification"
        report["directive"] = (
            "STOP. No spec.md found. "
            "1. Invoke 'list_skills()' to find the exact name of the grilling skill (likely 'grill-with-docs'). "
            "2. Execute the grilling skill to establish a ubiquitous language and update CONTEXT.md. "
            "3. Once the user is satisfied, invoke the 'to-spec' skill to generate the spec.md document."
        )
    elif not report["task_found"]:
        report["phase"] = "Phase 2: Task Breakdown"
        report["directive"] = (
            "STOP. spec.md exists, but no task.md found. "
            "1. Invoke 'list_skills()' to find the breakdown skill (likely 'to-tickets'). "
            "2. Break the spec into vertical tracer-bullet slices inside task.md."
        )
    else:
        report["phase"] = "Phase 3: Execution"
        report["directive"] = (
            "GO. Project is fully specified. "
            "Read task.md. Implement the next vertical slice using the 'implement' skill, "
            "which drives the '/tdd' loop. Close out with '/code-review'."
        )
        
    return json.dumps(report, indent=2)

if __name__ == "__main__":
    mcp.run()
