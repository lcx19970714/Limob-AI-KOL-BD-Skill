#!/usr/bin/env python3
"""One-click launcher for the local sales dashboard."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

from dashboard_server import DEFAULT_HOST, DEFAULT_PORT
from sales_db import DEFAULT_DB_PATH

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
日志文件 = ROOT / "data" / "dashboard_server.log"


def 健康地址(host: str, port: int) -> str:
    return f"http://{host}:{port}/api/health"


def 看板地址(host: str, port: int) -> str:
    return f"http://{host}:{port}/"


def 服务已启动(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        with urllib.request.urlopen(健康地址(host, port), timeout=timeout) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def 启动后台服务(host: str, port: int, db_path: str) -> None:
    日志文件.parent.mkdir(parents=True, exist_ok=True)
    with 日志文件.open("ab") as log_file:
        creationflags = 0
        creationflags |= getattr(subprocess, "DETACHED_PROCESS", 0)
        creationflags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        subprocess.Popen(
            [
                sys.executable,
                str(SCRIPT_DIR / "dashboard_server.py"),
                "--host",
                host,
                "--port",
                str(port),
                "--db",
                db_path,
            ],
            cwd=SCRIPT_DIR,
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=log_file,
            close_fds=True,
            creationflags=creationflags,
        )


def 确保服务可用(host: str, port: int, db_path: str) -> bool:
    if 服务已启动(host, port):
        return True
    启动后台服务(host, port, db_path)
    for _ in range(20):
        time.sleep(0.5)
        if 服务已启动(host, port):
            return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="一键启动销售看板")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    ok = 确保服务可用(args.host, args.port, args.db)
    if not ok:
        raise SystemExit(f"销售看板服务启动失败，请查看日志：{日志文件}")

    url = 看板地址(args.host, args.port)
    if not args.no_browser:
        webbrowser.open(url)
    print(f"销售看板已就绪：{url}")
    print(f"SQLite 数据库：{args.db}")


if __name__ == "__main__":
    main()
