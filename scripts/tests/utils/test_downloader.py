"""Downloader 单元测试（aria2c 参数拼装）"""

from typing import Any
from unittest.mock import patch

from utils.downloader import Downloader


def _make_downloader(**kwargs: Any) -> Downloader:
    """构造 Downloader，mock 掉 aria2c 存在性检查（CI 环境可能未安装）"""
    with patch("utils.downloader.shutil.which", return_value="/usr/bin/aria2c"):
        return Downloader(**kwargs)


class TestBuildBaseArgs:
    def test_check_certificate_default(self) -> None:
        """默认开启证书校验（--check-certificate=true）"""
        downloader = _make_downloader()
        assert "--check-certificate=true" in downloader._build_base_args()

    def test_check_certificate_disabled(self) -> None:
        """check_certificate=False 时传给 aria2c --check-certificate=false"""
        downloader = _make_downloader(check_certificate=False)
        assert "--check-certificate=false" in downloader._build_base_args()

    def test_base_args_contain_common_flags(self) -> None:
        """基础参数包含重试/超时/连接数等核心标志"""
        downloader = _make_downloader(max_retries=5, timeout=30, connections=8)
        args = downloader._build_base_args()
        assert args[0] == "aria2c"
        assert "--max-tries=5" in args
        assert "--timeout=30" in args
        assert "--max-connection-per-server=8" in args
        assert "--split=8" in args
