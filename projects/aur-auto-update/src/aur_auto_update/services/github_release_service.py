"""GitHub release 回退解析：metadata API 不可用时为 GitHub 来源包提供版本与 URL。

只在 ``package_version_provider`` 判定 metadata 请求失败后调用，不参与正常路径。
从**同一个 release JSON 对象**同时提取版本与各架构下载链接，保证 version 与
urls 指向同一次发布（固定 tag 的每日覆盖发布尤其依赖这点）。
"""

import asyncio
import json
import logging
import os
import re
from typing import Any

from httpx import HTTPError

from aur_auto_update.config import GithubSourceConfig, PackageConfig, VersionRule
from aur_auto_update.fetcher import Fetcher
from aur_auto_update.parsers.api_parser import ParsedPackage

logger = logging.getLogger(__name__)

_GITHUB_API = "https://api.github.com"
# GitHub 推荐的头；Accept 决定响应形态，版本头固定 API 版本避免随默认值漂移
_GITHUB_HEADERS: dict[str, str] = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
# 429（次限流）与 5xx 值得退避重试；403 单独处理——GitHub 的主限流配额在小时级
# 窗口内不会因 1~2 秒退避而恢复，重试只是白等，故立即放弃并提示检查 token
_RETRYABLE_STATUS: frozenset[int] = frozenset({408, 429, 500, 502, 503, 504})


class GithubReleaseService:
    """按包配置解析 GitHub release，产出 ``ParsedPackage``（不含校验和）。"""

    def __init__(self, fetcher: Fetcher) -> None:
        self._fetcher = fetcher
        # token 只从环境变量读，避免凭证落进 config.yaml
        self._token: str | None = os.environ.get("GITHUB_TOKEN") or None

    def _release_url(self, github: GithubSourceConfig) -> str:
        base: str = f"{_GITHUB_API}/repos/{github.repo}/releases"
        return f"{base}/tags/{github.tag}" if github.tag else f"{base}/latest"

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = dict(_GITHUB_HEADERS)
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def fetch(self, package_config: PackageConfig) -> ParsedPackage | None:
        """抓取并解析 release；配置缺失、请求失败或结构不符时返回 None。"""
        github: GithubSourceConfig | None = package_config.github
        if github is None:
            return None

        release: dict[str, Any] | None = await self._fetch_release(github)
        if release is None:
            return None

        version: str | None = _extract_version(release, github.version)
        if version is None:
            logger.error(
                "  GitHub 回退: %s 的 release 未能按规则提取版本号", package_config.name
            )
            return None

        urls: dict[str, str] = _extract_asset_urls(release, github.assets)
        missing: list[str] = [
            arch.value
            for arch in package_config.get_supported_archs()
            if arch.value not in urls
        ]
        if missing:
            logger.error("  GitHub 回退: %s 缺少架构 asset: %s", package_config.name, missing)
            return None

        logger.info(
            "  GitHub 回退成功: %s version=%s archs=%s",
            package_config.name,
            version,
            sorted(urls),
        )
        # GitHub 的 browser_download_url 是稳定直链，无需签名：
        # download_urls 与 urls 相同，但只有 urls 会被写入 PKGBUILD
        return ParsedPackage(version=version, urls=urls, download_urls=dict(urls))

    async def _fetch_release(
        self, github: GithubSourceConfig
    ) -> dict[str, Any] | None:
        """带有限退避重试的 release 请求；成功返回 JSON 对象，否则 None。"""
        url: str = self._release_url(github)
        max_attempts: int = 3
        for attempt in range(1, max_attempts + 1):
            try:
                response = await self._fetcher.client.get(
                    url, headers=self._headers()
                )
            except HTTPError as e:
                logger.warning(
                    "  GitHub 回退请求异常（%d/%d）: %s", attempt, max_attempts, e
                )
            else:
                if response.status_code == 200:
                    try:
                        data: Any = response.json()
                    except json.JSONDecodeError:
                        logger.error("  GitHub 回退: release 响应不是合法 JSON")
                        return None
                    return data if isinstance(data, dict) else None
                if response.status_code not in _RETRYABLE_STATUS:
                    if response.status_code == 403:
                        # 主限流/权限不足：配额按小时恢复，退避无意义
                        logger.error(
                            "  GitHub 回退: HTTP 403（限流或无权访问），检查 GITHUB_TOKEN"
                        )
                    else:
                        logger.error(
                            "  GitHub 回退: HTTP %d（不可重试）", response.status_code
                        )
                    return None
                logger.warning(
                    "  GitHub 回退: HTTP %d（%d/%d）",
                    response.status_code,
                    attempt,
                    max_attempts,
                )
            if attempt < max_attempts:
                await asyncio.sleep(float(2 ** (attempt - 1)))
        logger.error("  GitHub 回退: %s 请求 %d 次均失败", url, max_attempts)
        return None


def _extract_version(release: dict[str, Any], rules: list[VersionRule]) -> str | None:
    """按规则链提取版本：首个命中即返回，全部未命中返回 None。"""
    for rule in rules:
        raw: Any = release.get(rule.source)
        if not isinstance(raw, str):
            continue
        match = re.search(rule.regex, raw)
        if match is None:
            continue
        if rule.template is not None:
            try:
                value: str = rule.template.format(*match.groups())
            except (IndexError, KeyError):
                logger.warning("  version.template 引用组未命中: %s", rule.template)
                continue
        else:
            value = match.group(rule.group)
        if value:
            return value
    return None


def _extract_asset_urls(
    release: dict[str, Any], assets: dict[str, str]
) -> dict[str, str]:
    """按架构把 asset 规则映射到 ``browser_download_url``。

    规则以 ``*`` 开头为后缀匹配，否则精确匹配文件名；同一架构只取首个命中。
    """
    raw_assets: Any = release.get("assets")
    if not isinstance(raw_assets, list):
        return {}
    names: dict[str, str] = {}
    for asset in raw_assets:
        if not isinstance(asset, dict):
            continue
        name: Any = asset.get("name")
        url: Any = asset.get("browser_download_url")
        if isinstance(name, str) and isinstance(url, str):
            names[name] = url

    urls: dict[str, str] = {}
    for arch, pattern in assets.items():
        for name, url in names.items():
            hit: bool = name.endswith(pattern[1:]) if pattern.startswith("*") else name == pattern
            if hit:
                urls[arch] = url
                break
    return urls
