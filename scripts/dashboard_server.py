#!/usr/bin/env python3
"""Local dashboard server for the sales board."""

from __future__ import annotations

import argparse
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from sales_db import DEFAULT_DB_PATH, 生成看板数据, 连接数据库

ROOT = Path(__file__).resolve().parents[1]
看板目录 = ROOT / "assets" / "dashboard"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


class 看板请求处理器(BaseHTTPRequestHandler):
    server_version = "SalesDashboard/1.0"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/health":
            self._返回JSON({"状态": "正常"})
            return
        if path == "/api/dashboard":
            self._处理看板数据(parsed.query)
            return
        self._处理静态文件(path)

    def end_headers(self) -> None:  # noqa: N802
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _处理看板数据(self, query: str) -> None:
        参数 = parse_qs(query)
        当前阶段 = 参数.get("阶段", [None])[0]
        优先级 = 参数.get("优先级", [None])[0]
        with 连接数据库(self.server.数据库路径) as conn:  # type: ignore[attr-defined]
            数据 = 生成看板数据(conn, 当前阶段=当前阶段, 优先级=优先级)
        self._返回JSON(数据)

    def _处理静态文件(self, path: str) -> None:
        if path in {"", "/"}:
            目标路径 = 看板目录 / "index.html"
        else:
            目标路径 = (看板目录 / path.lstrip("/")).resolve()
            if not str(目标路径).startswith(str(看板目录.resolve())):
                self.send_error(HTTPStatus.FORBIDDEN, "禁止访问")
                return

        if not 目标路径.exists() or not 目标路径.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "文件不存在")
            return

        内容类型 = mimetypes.guess_type(str(目标路径))[0] or "application/octet-stream"
        数据 = 目标路径.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{内容类型}; charset=utf-8")
        self.send_header("Content-Length", str(len(数据)))
        self.end_headers()
        self.wfile.write(数据)

    def _返回JSON(self, 数据: dict) -> None:
        内容 = json.dumps(数据, ensure_ascii=False).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(内容)))
        self.end_headers()
        self.wfile.write(内容)


class 看板服务(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], handler_class, 数据库路径: str):
        super().__init__(server_address, handler_class)
        self.数据库路径 = 数据库路径


def main() -> None:
    parser = argparse.ArgumentParser(description="本地销售看板服务")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    args = parser.parse_args()

    服务 = 看板服务((args.host, args.port), 看板请求处理器, args.db)
    print(f"销售看板服务已启动：http://{args.host}:{args.port}")
    print(f"SQLite 数据库：{args.db}")
    服务.serve_forever()


if __name__ == "__main__":
    main()
