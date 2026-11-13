"""CLI healthcheck 子命令测试。

只看 HTTP 状态码会把同端口上其他服务的 200 页面误判为就绪，因此这里用
真实本地 HTTP 服务覆盖三种响应形态。
"""

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer

from aur_metadata.cli import _healthcheck


class _Handler(BaseHTTPRequestHandler):
    """按类属性决定响应体，便于一个测试内切换场景"""

    body: bytes = b'{"code":0,"message":"ok","data":{"packages":[]}}'
    status: int = 200

    def do_GET(self) -> None:
        self.send_response(self.status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(self.body)

    def log_message(self, format: str, *args: object) -> None:
        """静默请求日志，避免污染测试输出"""


@contextmanager
def _serve(status: int, body: bytes) -> Iterator[int]:
    """启动一次性本地服务，产出端口号"""
    handler = type("_H", (_Handler,), {"status": status, "body": body})
    server = HTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()


def test_healthcheck_ready_on_business_success() -> None:
    with _serve(200, b'{"code":0,"message":"ok","data":{"packages":[]}}') as port:
        assert _healthcheck(port) == 0


def test_healthcheck_fails_when_body_is_not_our_api() -> None:
    """同端口其他服务返回 200 HTML 时必须判为未就绪"""
    with _serve(200, b"<html><body>Access Temporarily Unavailable</body></html>") as port:
        assert _healthcheck(port) == 1


def test_healthcheck_fails_on_non_zero_business_code() -> None:
    with _serve(200, b'{"code":50000,"message":"err","data":null}') as port:
        assert _healthcheck(port) == 1


def test_healthcheck_fails_on_http_error_status() -> None:
    with _serve(503, b'{"code":50300,"message":"not ready","data":null}') as port:
        assert _healthcheck(port) == 1


def test_healthcheck_fails_when_nothing_listens() -> None:
    """连接被拒也应返回未就绪，而不是抛异常"""
    assert _healthcheck(1) == 1
