# -*- coding: utf-8 -*-
# Author: dengwanpeng

"""Check capture server status on port 12138.

Usage:
    python check_capture_server.py

Exit codes:
    0  RUNNING           Port is listened by mitmdump or python process
    1  NOT_RUNNING       Port is not listening
    2  PORT_OCCUPIED     Port is occupied by another process
"""

import socket
import subprocess
import sys

PORT = 12138
HOST = "127.0.0.1"


def _port_listening(host: str, port: int, timeout: float = 0.5) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        return s.connect_ex((host, port)) == 0
    finally:
        s.close()


def _pid_on_port(port: int):
    """Query LISTENING PID via netstat on Windows."""
    try:
        out = subprocess.check_output(
            ["netstat", "-ano"], shell=False, stderr=subprocess.DEVNULL
        ).decode("gbk", errors="ignore")
    except Exception:
        return None
    for line in out.splitlines():
        if f":{port} " in line and "LISTENING" in line:
            parts = line.split()
            if parts:
                return parts[-1]
    return None


def _pid_exe(pid: str):
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            shell=False, stderr=subprocess.DEVNULL
        ).decode("gbk", errors="ignore")
        if out.strip():
            return out.strip().split(",")[0].strip('"')
    except Exception:
        pass
    return None


def main() -> int:
    listening = _port_listening(HOST, PORT)
    if not listening:
        print("NOT_RUNNING")
        return 1

    pid = _pid_on_port(PORT)
    if pid is None:
        print("RUNNING")
        return 0

    exe = _pid_exe(pid) or ""
    exe_lower = exe.lower()
    if "mitm" in exe_lower or "python" in exe_lower:
        print(f"RUNNING pid={pid} exe={exe}")
        return 0

    print(f"PORT_OCCUPIED pid={pid} exe={exe}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
