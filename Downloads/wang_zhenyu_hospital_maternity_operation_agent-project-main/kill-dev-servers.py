#!/usr/bin/env python3

"""
Kill all Next.js and FastAPI development servers
Usage: python kill-dev-servers.py
"""

from typing import List
import sys
import subprocess
from dataclasses import dataclass


@dataclass
class Process:
    """Represents a system process with PID and command."""

    pid: str
    command: str

    def is_nextjs_process(self) -> bool:
        """Check if this process is a Next.js development server."""
        if 'node' not in self.command.lower():
            return False

        keywords = [
            'next-server',
            'next dev',
            'next/dist/server',
            '.next/server',
            'npm run next-dev',
            'npm run dev',
            'concurrently'
        ]
        return any(keyword in self.command.lower() for keyword in keywords)

    def is_fastapi_process(self) -> bool:
        """Check if this process is a FastAPI/Uvicorn server."""
        fastapi_keywords = [
            'uvicorn',
            'fastapi',
            'api/index.py',
            'api.index',
            'npm run fastapi-dev',
        ]

        if not any(keyword in self.command.lower() for keyword in fastapi_keywords):
            return False

        # Ensure it's a Python process or npm command
        process_types = ['python', 'uvicorn', 'npm']
        return any(ptype in self.command.lower() for ptype in process_types)

    def get_display_command(self, max_length: int = 100) -> str:
        """Get truncated command for display purposes."""
        if len(self.command) <= max_length:
            return self.command
        return self.command[:max_length - 3] + "..."


@dataclass
class CommandResult:
    """Result from running a shell command."""

    output: str
    success: bool

    @property
    def lines(self) -> List[str]:
        """Get output as list of non-empty lines."""
        return [line for line in self.output.split('\n') if line.strip()]


@dataclass
class FindProcessesResult:
    """Result from finding Next.js and FastAPI processes."""

    next_processes: List[Process]
    fastapi_processes: List[Process]

    def all_processes(self) -> List[Process]:
        """Get all processes found."""
        return self.next_processes + self.fastapi_processes

    @property
    def has_processes(self) -> bool:
        """Check if any processes were found."""
        return len(self.next_processes) > 0 or len(self.fastapi_processes) > 0


@dataclass
class KillProcessResult:
    """Result from killing a process."""

    pid: str
    success: bool

    def __str__(self) -> str:
        """Get string representation of kill result."""
        status = "✅ Killed" if self.success else "❌ Failed to kill"
        return f"  {status} PID {self.pid}"


@dataclass
class PortCheckResult:
    """Result from checking a port."""

    port: int
    in_use: bool
    pids: List[str]

    @property
    def is_free(self) -> bool:
        """Check if the port is free."""
        return not self.in_use


def run_command(cmd: List[str]) -> CommandResult:
    """Run a shell command and return result with output and status."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        return CommandResult(
            output=result.stdout,
            success=result.returncode == 0
        )
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return CommandResult(output="", success=False)


def find_processes() -> FindProcessesResult:
    """Find Next.js and FastAPI development server processes."""
    ps_result = run_command(["ps", "aux"])

    next_processes = []
    fastapi_processes = []

    for line in ps_result.output.split('\n'):
        if not line.strip():
            continue

        # Skip header line
        if 'USER' in line and 'PID' in line:
            continue

        # Skip grep itself and this script
        if 'grep' in line or 'kill-dev-servers' in line:
            continue

        parts = line.split(None, 10)  # Split into at most 11 parts
        if len(parts) < 11:
            continue

        process = Process(pid=parts[1], command=parts[10])

        # Categorize processes
        if process.is_nextjs_process():
            next_processes.append(process)
        elif process.is_fastapi_process():
            fastapi_processes.append(process)

    return FindProcessesResult(
        next_processes=next_processes,
        fastapi_processes=fastapi_processes
    )


def kill_process(process: Process) -> KillProcessResult:
    """Kill a process by PID."""
    try:
        subprocess.run(['kill', '-9', process.pid], check=True, capture_output=True)
        return KillProcessResult(pid=process.pid, success=True)
    except subprocess.CalledProcessError:
        return KillProcessResult(pid=process.pid, success=False)


def check_port(port: int) -> PortCheckResult:
    """Check if a port is in use and return PIDs using it."""
    result = run_command(['lsof', '-ti', f':{port}'])

    if result.output.strip():
        pids = [pid.strip() for pid in result.lines if pid.strip()]
        return PortCheckResult(port=port, in_use=True, pids=pids)
    else:
        return PortCheckResult(port=port, in_use=False, pids=[])


def main():
    print("🔍 Searching for development server processes...\n")

    # Find processes
    find_result = find_processes()

    # Display Next.js processes
    if find_result.next_processes:
        print(f"🟢 Found {len(find_result.next_processes)} Next.js process(es):")
        for process in find_result.next_processes:
            print(f"  PID {process.pid}: {process.get_display_command()}")
        print()
    else:
        print("ℹ️  No Next.js processes found\n")

    # Display FastAPI processes
    if find_result.fastapi_processes:
        print(f"🟠 Found {len(find_result.fastapi_processes)} FastAPI/Uvicorn process(es):")
        for process in find_result.fastapi_processes:
            print(f"  PID {process.pid}: {process.get_display_command()}")
        print()
    else:
        print("ℹ️  No FastAPI processes found\n")

    # Kill processes found by pattern matching
    if find_result.has_processes:
        print("🛑 Terminating processes...\n")

    kill_results = []
    for process in find_result.all_processes():
        result = kill_process(process)
        kill_results.append(result)
        print(result)

    killed_count = sum(1 for r in kill_results if r.success)
    failed_count = sum(1 for r in kill_results if not r.success)

    if killed_count > 0 or failed_count > 0:
        print()
        print(f"✨ Pattern-based cleanup complete!")
        print(f"   Terminated: {killed_count} process(es)")
        if failed_count > 0:
            print(f"   Failed: {failed_count} process(es)")

    # Check and clean up common development ports
    print("\n📊 Checking and cleaning up common development ports:")
    additional_kills = 0

    for port in [3000, 3001, 3002, 8000, 8080]:
        port_result = check_port(port)

        if port_result.in_use:
            print(f"  ⚠️  Port {port} in use by PID(s): {', '.join(port_result.pids)}")
            # Kill these PIDs
            for pid in port_result.pids:
                process = Process(pid=pid, command="<port-based>")
                kill_result = kill_process(process)
                if kill_result.success:
                    additional_kills += 1
                else:
                    print(f"     ❌ Failed to kill PID {pid} on port {port}")
        else:
            print(f"  ✅ Port {port} is free")

    if additional_kills > 0:
        print(f"\n🧹 Killed {additional_kills} additional process(es) by port")

    # Final summary
    total_killed = killed_count + additional_kills
    if total_killed > 0:
        print(f"\n✅ All done! Killed {total_killed} total process(es)")
    elif killed_count == 0 and additional_kills == 0:
        print(f"\n✅ All ports are free! No dev servers to kill")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)