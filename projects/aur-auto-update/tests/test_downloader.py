"""Downloader 单元测试（aria2c 参数拼装与 URL 安全校验）"""

from pathlib import Path
from typing import Any
from unittest.mock import patch

from aur_auto_update.utils.downloader import Downloader


def _make_downloader(**kwargs: Any) -> Downloader:
    """构造 Downloader，mock 掉 aria2c 存在性检查（CI 环境可能未安装）"""
    with patch("aur_auto_update.utils.downloader.shutil.which", return_value="/usr/bin/aria2c"):
        return Downloader(**kwargs)


class TestBuildBaseArgs:
    def test_check_certificate_default(self) -> None:
        """默认开启证书校验（--check-certificate=true）"""
        downloader = _make_downloader()
        assert "--check-certificate=true" in downloader._build_base_args()

    def test_check_certificate_disabled(self) -> None:
        """verify_ssl=False 时传给 aria2c --check-certificate=false"""
        downloader = _make_downloader(verify_ssl=False)
        assert "--check-certificate=false" in downloader._build_base_args()

    def test_file_allocation_fixed(self) -> None:
        """file-allocation 固化为 none（跳过预分配，避免大文件写盘两次）"""
        downloader = _make_downloader()
        assert "--file-allocation=none" in downloader._build_base_args()


class TestUrlSafety:
    async def test_control_chars_in_url_rejected(self, tmp_path: Path) -> None:
        """URL 含控制字符（aria2c input file 指令注入面）→ 直接记失败，不触 aria2c"""
        downloader = _make_downloader()
        results = await downloader.download_all(
            {"x86_64": ("https://example.com/a.deb\n  dir=/etc/cron.d/", tmp_path / "a.deb")}
        )
        assert results["x86_64"].success is False
        assert "控制字符" in (results["x86_64"].error or "")
        assert not (tmp_path / "a.deb").exists()

    def test_base_args_contain_common_flags(self) -> None:
        """基础参数包含重试/超时/连接数等核心标志"""
        downloader = _make_downloader(max_retries=5, timeout=30, connections=8)
        args = downloader._build_base_args()
        assert args[0] == "aria2c"
        assert "--max-tries=5" in args
        assert "--timeout=30" in args
        assert "--max-connection-per-server=8" in args
        assert "--split=8" in args
