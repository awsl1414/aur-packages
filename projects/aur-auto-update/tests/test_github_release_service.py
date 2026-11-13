"""GithubReleaseService 单测：release JSON → ParsedPackage。

用 ``httpx.MockTransport`` 提供固定的 release 响应，不触真实网络。覆盖三个真实
包的规则形态（固定 tag + name 双规则、latest + 后缀匹配、缺 asset、限流重试与
token 头）。
"""

import json
from typing import Any

import httpx

from aur_auto_update.config import GithubSourceConfig, PackageConfig
from aur_auto_update.fetcher import Fetcher
from aur_auto_update.services.github_release_service import GithubReleaseService

_ORCA_RELEASE: dict[str, Any] = {
    "tag_name": "v1.4.258",
    "name": "1.4.258",
    "assets": [
        {"name": "orca-ide-1.4.258.x86_64.rpm", "browser_download_url": "https://x/rpm"},
        {"name": "orca-ide_1.4.258_amd64.deb", "browser_download_url": "https://x/amd64.deb"},
        {"name": "orca-ide_1.4.258_arm64.deb", "browser_download_url": "https://x/arm64.deb"},
    ],
}

_ZEN_RELEASE: dict[str, Any] = {
    "tag_name": "twilight-1",
    "name": "Twilight build - 1.25t (2026-11-11 at 22:04:21)",
    "assets": [
        {"name": "zen.linux-x86_64.tar.xz", "browser_download_url": "https://x/zen-x64"},
        {"name": "zen.linux-aarch64.tar.xz", "browser_download_url": "https://x/zen-arm"},
        {"name": "zen-x86_64.AppImage", "browser_download_url": "https://x/appimage"},
    ],
}


def _service(
    payload: dict[str, Any],
    *,
    status: int = 200,
    calls: list[httpx.Request] | None = None,
) -> GithubReleaseService:
    """构造带 MockTransport 的服务；``calls`` 记录所有请求便于断言头与次数"""

    def handler(request: httpx.Request) -> httpx.Response:
        if calls is not None:
            calls.append(request)
        return httpx.Response(status, json=payload)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    fetcher = Fetcher(timeout=5, max_retries=0)
    # 用 MockTransport 客户端替换真实客户端，避免测试触网
    fetcher.client = client
    return GithubReleaseService(fetcher)


def _pkg(
    github: GithubSourceConfig, arch: list[str] | None = None
) -> PackageConfig:
    return PackageConfig(
        name="app",
        pkgbuild="packages/app/PKGBUILD",
        arch=arch or ["x86_64"],
        github=github,
    )


async def test_orca_latest_tag_and_suffix_assets() -> None:
    """latest + tag_name 正则 + 后缀匹配，避开同仓库 rpm"""
    github = GithubSourceConfig(
        repo="stablyai/orca",
        version=[{"source": "tag_name", "regex": r"^v(\d+\.\d+\.\d+)$", "group": 1}],
        assets={"x86_64": "*_amd64.deb", "aarch64": "*_arm64.deb"},
    )
    parsed = await _service(_ORCA_RELEASE).fetch(_pkg(github, ["x86_64", "aarch64"]))
    assert parsed is not None
    assert parsed.version == "1.4.258"
    assert parsed.urls == {
        "x86_64": "https://x/amd64.deb",
        "aarch64": "https://x/arm64.deb",
    }
    # GitHub 直链无需签名：download_urls 与 urls 相同，但只有 urls 会写 PKGBUILD
    assert parsed.download_urls == parsed.urls


async def test_zen_fixed_tag_dated_version_template() -> None:
    """固定 tag + name 双规则：首条带日期模板命中，精确 asset 名匹配"""
    github = GithubSourceConfig(
        repo="zen-browser/desktop",
        tag="twilight-1",
        version=[
            {
                "source": "name",
                "regex": r"(\d+\.\d+[a-z]?)\s*\((\d{4})-(\d{2})-(\d{2})",
                "template": "{0}.{1}{2}{3}",
            },
            {"source": "name", "regex": r"\d+\.\d+[a-z]?"},
        ],
        assets={
            "x86_64": "zen.linux-x86_64.tar.xz",
            "aarch64": "zen.linux-aarch64.tar.xz",
        },
    )
    parsed = await _service(_ZEN_RELEASE).fetch(_pkg(github, ["x86_64", "aarch64"]))
    assert parsed is not None
    assert parsed.version == "1.25t.20261111"
    assert parsed.urls == {
        "x86_64": "https://x/zen-x64",
        "aarch64": "https://x/zen-arm",
    }


async def test_zen_version_fallback_rule() -> None:
    """首条规则未命中（name 无日期）时退回纯版本号规则"""
    github = GithubSourceConfig(
        repo="zen-browser/desktop",
        tag="twilight-1",
        version=[
            {"source": "name", "regex": r"(\d+\.\d+)[a-z]?\s*\((\d{4})"},
            {"source": "name", "regex": r"\d+\.\d+[a-z]?"},
        ],
        assets={"x86_64": "zen.linux-x86_64.tar.xz"},
    )
    release = dict(_ZEN_RELEASE, name="Twilight build - 1.25t")
    parsed = await _service(release).fetch(_pkg(github))
    assert parsed is not None and parsed.version == "1.25t"


async def test_missing_asset_fails() -> None:
    """支持的架构在 assets 中找不到 → 返回 None，不下发不完整结果"""
    github = GithubSourceConfig(
        repo="stablyai/orca",
        version=[{"source": "tag_name", "regex": r"^v(\d+\.\d+\.\d+)$", "group": 1}],
        assets={"x86_64": "*_amd64.deb", "aarch64": "*_arm64.deb"},
    )
    release = dict(_ORCA_RELEASE, assets=_ORCA_RELEASE["assets"][:2])
    assert await _service(release).fetch(_pkg(github, ["x86_64", "aarch64"])) is None


async def test_non_retryable_status_fails() -> None:
    """404 属确定性失败，不重试"""
    github = GithubSourceConfig(
        repo="a/b",
        version=[{"source": "tag_name", "regex": r"v(.+)"}],
        assets={"x86_64": "*"},
    )
    calls: list[httpx.Request] = []
    assert await _service({}, status=404, calls=calls).fetch(_pkg(github)) is None
    assert len(calls) == 1


async def test_forbidden_not_retried() -> None:
    """403（限流/无权）配额按小时恢复，不盲目退避重试"""
    github = GithubSourceConfig(
        repo="a/b",
        version=[{"source": "tag_name", "regex": r"v(.+)"}],
        assets={"x86_64": "*"},
    )
    calls: list[httpx.Request] = []
    assert await _service({}, status=403, calls=calls).fetch(_pkg(github)) is None
    assert len(calls) == 1


async def test_rate_limited_429_retries_then_fails() -> None:
    """429（次限流）属瞬时，退避重试至上限"""
    github = GithubSourceConfig(
        repo="a/b",
        version=[{"source": "tag_name", "regex": r"v(.+)"}],
        assets={"x86_64": "*"},
    )
    calls: list[httpx.Request] = []
    assert await _service({}, status=429, calls=calls).fetch(_pkg(github)) is None
    assert len(calls) == 3


async def test_github_headers_and_token(monkeypatch) -> None:
    """请求带 GitHub 推荐头；设置 GITHUB_TOKEN 时附带 Authorization"""
    monkeypatch.setenv("GITHUB_TOKEN", "secret-token")
    github = GithubSourceConfig(
        repo="stablyai/orca",
        version=[{"source": "tag_name", "regex": r"^v(\d+\.\d+\.\d+)$", "group": 1}],
        assets={"x86_64": "*_amd64.deb"},
    )
    calls: list[httpx.Request] = []
    parsed = await _service(_ORCA_RELEASE, calls=calls).fetch(_pkg(github))
    assert parsed is not None
    request = calls[0]
    assert request.headers["Accept"] == "application/vnd.github+json"
    assert request.headers["X-GitHub-Api-Version"] == "2022-11-28"
    assert request.headers["Authorization"] == "Bearer secret-token"


async def test_fixed_tag_url(monkeypatch) -> None:
    """配置 tag 时请求 /releases/tags/<tag>，否则 /releases/latest"""
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    github = GithubSourceConfig(
        repo="zen-browser/desktop",
        tag="twilight-1",
        version=[{"source": "name", "regex": r"\d+\.\d+[a-z]?"}],
        assets={"x86_64": "zen.linux-x86_64.tar.xz"},
    )
    calls: list[httpx.Request] = []
    await _service(_ZEN_RELEASE, calls=calls).fetch(_pkg(github))
    assert str(calls[0].url).endswith("/repos/zen-browser/desktop/releases/tags/twilight-1")


def test_parsed_release_json_roundtrip() -> None:
    """release JSON 必须能原样序列化（MockTransport 与真实响应同形态）"""
    assert json.loads(json.dumps(_ORCA_RELEASE))["tag_name"] == "v1.4.258"
