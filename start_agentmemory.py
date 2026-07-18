#!/usr/bin/env python3
import os
import sys
import socket
import hashlib
import subprocess
import time
from pathlib import Path

def find_workspace_root(start_path: Path) -> Path:
    """Traverse upwards to find the nearest workspace root containing .git, .agents, or .graphifyignore."""
    current = start_path.resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".git").exists() or (parent / ".agents").exists() or (parent / ".graphifyignore").exists():
            return parent
    return current

def is_port_in_use(port: int) -> bool:
    """Check if a port is currently listening on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def main():
    # 1. Determine active workspace root
    cwd = Path.cwd()
    workspace_root = find_workspace_root(cwd)
    
    # 2. Compute a stable, collision-free port based on the workspace path
    # Hash the absolute workspace path to map it to a port in the range 3111 - 3300
    h = hashlib.sha256(str(workspace_root).encode('utf-8')).hexdigest()
    port_offset = int(h, 16) % 190
    port = 3111 + port_offset
    
    # 3. Ensure local .memory directory exists inside the workspace
    memory_dir = workspace_root / ".memory"
    try:
        memory_dir.mkdir(exist_ok=True)
    except Exception:
        # Fallback to home directory if workspace root is read-only or root '/'
        memory_dir = Path.home() / ".memory"
        memory_dir.mkdir(exist_ok=True)
    
    # 4. Check if the local agentmemory daemon is already running on this port
    if not is_port_in_use(port):
        # Start the background daemon with working directory set to .memory/
        # This forces the SQLite database file to be written to .memory/data/state_store.db
        cmd = ["npx", "-y", "@agentmemory/agentmemory", "--port", str(port)]
        
        # Spawn daemon detached so it survives and doesn't get blocked by stdin/stdout
        subprocess.Popen(
            cmd,
            cwd=str(memory_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        # Wait a brief moment for the daemon server to bind to the port
        attempts = 0
        while not is_port_in_use(port) and attempts < 10:
            time.sleep(0.5)
            attempts += 1

    # 5. Spawn the MCP client, pointing AGENTMEMORY_URL to our local port,
    # and pipe standard input/output directly to the IDE.
    client_env = os.environ.copy()
    client_env["AGENTMEMORY_URL"] = f"http://127.0.0.1:{port}"
    
    # Run the client in the current process
    client_cmd = ["npx", "--no-install", "@agentmemory/mcp"]
    try:
        sys.exit(
            subprocess.call(
                client_cmd,
                env=client_env,
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr
            )
        )
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()
