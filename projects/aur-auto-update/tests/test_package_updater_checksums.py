"""PackageUpdater._get_checksums 本地下载计算的单测。

覆盖 URL 优先级（download_urls 优先、缺失退回 urls）与完整性校验，不触真实
网络/aria2c：用桩下载器替换实例属性，文件内容由桩写入本地临时文件，校验和走
真实计算路径。
"""

from pathlib import Path
from typing import cast

from aur_auto_update.constants import ArchEnum
from aur_auto_update.parsers.api_parser import ParsedPackage
from aur_auto_update.services.package_updater import PackageUpdater
from aur_auto_update.utils.downloader import Downloader, DownloadResult


class _FakeDownloader:
    """记录各架构请求 URL 的桩下载器：写入固定内容文件模拟下载成功。"""

    def __init__(self) -> None:
        self.requested_urls: dict[str, str] = {}

    async def download_all(
        self, downloads: dict[str, tuple[str, Path]]
    ) -> dict[str, DownloadResult]:
        results: dict[str, DownloadResult] = {}
        for arch, (url, dest) in downloads.items():
            self.requested_urls[arch] = url
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(b"payload")
            results[arch] = DownloadResult(success=True, file_path=dest)
        return results

    def as_downloader(self) -> Downloader:
        """伪装成 Downloader 供 PackageUpdater 使用（ty 兼容）。"""
        return cast(Downloader, self)


def _updater(tmp_path: Path, fake: _FakeDownloader) -> PackageUpdater:
    """绕开 __init__（其依赖 config.yaml 与 aria2c），只装配 _get_checksums 所需属性。"""
    updater = object.__new__(PackageUpdater)
    updater.pkgbuild_root = tmp_path
    updater.downloader = fake.as_downloader()
    return updater


def _parsed(
    urls: dict[str, str],
    download_urls: dict[str, str] | None = None,
) -> ParsedPackage:
    return ParsedPackage(
        version="1.0.0",
        urls=urls,
        download_urls=download_urls or {},
    )


async def test_get_checksums_prefers_download_urls(tmp_path: Path) -> None:
    """下载时优先使用实时可下载链接（QQ 签名场景）"""
    fake = _FakeDownloader()
    updater = _updater(tmp_path, fake)
    checksums, success = await updater._get_checksums(
        _parsed(
            urls={"x86_64": "https://raw/x.deb"},
            download_urls={"x86_64": "https://signed/x.deb"},
        ),
        [ArchEnum.X86_64],
        "qq",
        "1.0.0",
        "b2",
    )
    assert success is True
    assert set(checksums) == {"x86_64"}
    assert fake.requested_urls == {"x86_64": "https://signed/x.deb"}


async def test_get_checksums_falls_back_to_urls(tmp_path: Path) -> None:
    """download_urls 中该架构缺失（如签名失败被过滤）→ 回退原始 urls 下载"""
    fake = _FakeDownloader()
    updater = _updater(tmp_path, fake)
    checksums, success = await updater._get_checksums(
        _parsed(urls={"x86_64": "https://raw/x.deb"}),
        [ArchEnum.X86_64],
        "qq",
        "1.0.0",
        "b2",
    )
    assert success is True
    assert set(checksums) == {"x86_64"}
    assert fake.requested_urls == {"x86_64": "https://raw/x.deb"}


async def test_get_checksums_no_url_skips_arch(tmp_path: Path) -> None:
    """urls 与 download_urls 均无该架构 → 不下载，返回部分校验和与失败标记"""
    fake = _FakeDownloader()
    updater = _updater(tmp_path, fake)
    checksums, success = await updater._get_checksums(
        _parsed(urls={}),
        [ArchEnum.X86_64],
        "qq",
        "1.0.0",
        "b2",
    )
    assert success is False
    assert checksums == {}
    assert fake.requested_urls == {}


async def test_get_checksums_partial_arch_without_url_fails(tmp_path: Path) -> None:
    """多架构缺一且该架构无任何可用 URL → 立即整体失败，不下载其余架构"""
    fake = _FakeDownloader()
    updater = _updater(tmp_path, fake)
    checksums, success = await updater._get_checksums(
        _parsed(urls={"x86_64": "https://raw/x.deb"}),
        [ArchEnum.X86_64, ArchEnum.AARCH64],
        "qq",
        "1.0.0",
        "b2",
    )
    assert success is False
    assert checksums == {}
    # 缺 URL 已注定整体放弃，不应白下载 x86_64 的安装包
    assert fake.requested_urls == {}
