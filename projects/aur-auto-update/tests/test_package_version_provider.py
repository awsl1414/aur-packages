"""PackageVersionProvider 单测：metadata 优先，失败时按配置回退 GitHub。

用桩替换 ``Fetcher`` 与 ``GithubReleaseService``，断言：
- metadata 成功时不触 GitHub
- metadata 失败且包配置了 ``github`` 时回退
- 非 GitHub 包失败时不回退
- 回退也不成功时返回 None
"""

import json
from typing import cast

from aur_auto_update.config import GithubSourceConfig, PackageConfig
from aur_auto_update.fetcher import Fetcher
from aur_auto_update.parsers.api_parser import ApiParser, ParsedPackage
from aur_auto_update.services.github_release_service import GithubReleaseService
from aur_auto_update.services.package_version_provider import PackageVersionProvider

_METADATA_BODY: str = json.dumps(
    {
        "code": 0,
        "message": "ok",
        "data": {
            "name": "orca-ide",
            "version": "1.4.258",
            "urls": {"x86_64": "https://metadata/amd64.deb"},
            "download_urls": {"x86_64": "https://metadata/signed.deb"},
        },
    }
)


class _FakeFetcher:
    """返回预设文本的桩；``text=None`` 模拟 metadata 请求失败"""

    def __init__(self, text: str | None) -> None:
        self._text = text
        self.calls: int = 0

    async def fetch_text(self, url: str, headers: dict[str, str] | None = None) -> str | None:
        self.calls += 1
        return self._text


class _FakeGithub:
    """返回预设结果的桩，记录调用次数"""

    def __init__(self, parsed: ParsedPackage | None) -> None:
        self._parsed = parsed
        self.calls: int = 0

    async def fetch(self, package_config: PackageConfig) -> ParsedPackage | None:
        self.calls += 1
        return self._parsed


_GITHUB_PARSED = ParsedPackage(
    version="1.4.258",
    urls={"x86_64": "https://github/amd64.deb"},
    download_urls={"x86_64": "https://github/amd64.deb"},
)

_GITHUB_CFG = GithubSourceConfig(
    repo="stablyai/orca",
    version=[{"source": "tag_name", "regex": r"^v(\d+\.\d+\.\d+)$", "group": 1}],
    assets={"x86_64": "*_amd64.deb"},
)


def _provider(
    metadata_text: str | None, github_parsed: ParsedPackage | None
) -> tuple[PackageVersionProvider, _FakeFetcher, _FakeGithub]:
    fetcher = _FakeFetcher(metadata_text)
    github = _FakeGithub(github_parsed)
    provider = PackageVersionProvider(
        cast(Fetcher, fetcher),
        ApiParser(),
        cast(GithubReleaseService, github),
    )
    return provider, fetcher, github


def _pkg(github: GithubSourceConfig | None) -> PackageConfig:
    return PackageConfig(
        name="orca-ide",
        pkgbuild="packages/orca-ide/PKGBUILD",
        arch=["x86_64"],
        github=github,
    )


async def test_metadata_success_skips_github() -> None:
    """metadata 正常时直接采用其响应，不触 GitHub"""
    provider, fetcher, github = _provider(_METADATA_BODY, _GITHUB_PARSED)
    parsed = await provider.fetch(_pkg(_GITHUB_CFG), "https://metadata/orca-ide")
    assert parsed is not None
    assert parsed.version == "1.4.258"
    assert parsed.urls == {"x86_64": "https://metadata/amd64.deb"}
    assert fetcher.calls == 1 and github.calls == 0


async def test_metadata_failure_falls_back_when_github_configured() -> None:
    """metadata 请求失败且配置了 github → 回退到 release 解析"""
    provider, fetcher, github = _provider(None, _GITHUB_PARSED)
    parsed = await provider.fetch(_pkg(_GITHUB_CFG), "https://metadata/orca-ide")
    assert parsed is not None
    assert parsed.urls == {"x86_64": "https://github/amd64.deb"}
    assert fetcher.calls == 1 and github.calls == 1


async def test_metadata_parse_failure_falls_back() -> None:
    """metadata 响应结构不合规（解析为 None）同样触发回退"""
    provider, _fetcher, github = _provider("not-json", _GITHUB_PARSED)
    parsed = await provider.fetch(_pkg(_GITHUB_CFG), "https://metadata/orca-ide")
    assert parsed is not None and github.calls == 1


async def test_non_github_package_does_not_fall_back() -> None:
    """未配置 github 的包在 metadata 失败时直接返回 None"""
    provider, _fetcher, github = _provider(None, _GITHUB_PARSED)
    assert await provider.fetch(_pkg(None), "https://metadata/qq") is None
    assert github.calls == 0


async def test_fallback_failure_returns_none() -> None:
    """回退也失败时返回 None，调用方据此放弃该包"""
    provider, _fetcher, github = _provider(None, None)
    assert await provider.fetch(_pkg(_GITHUB_CFG), "https://metadata/orca-ide") is None
    assert github.calls == 1


def test_provider_accepts_real_fetcher() -> None:
    """真实 Fetcher 可构造 provider（类型面校验）"""
    fetcher = Fetcher(timeout=5, max_retries=0)
    provider = PackageVersionProvider(
        fetcher, ApiParser(), cast(GithubReleaseService, _FakeGithub(None))
    )
    assert isinstance(provider, PackageVersionProvider)
