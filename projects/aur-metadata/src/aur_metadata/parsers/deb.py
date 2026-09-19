"""deb 包统一版本解析器。

版本号取自 deb 文件头部 control 段的 ``Version`` 字段（dpkg 权威值），不依赖
文件名正则。两部分能力：

- ``DebControlVersionMixin``：deb 头部解析能力，任何安装包为 deb 的 parser
  （QQ、DebParser）混入即接入统一提取机制；
- ``DebParser``：通用 parser_type ``"deb"``，安装包 URL 由 ``parser_config.urls``
  静态注入（arch→URL 映射，接受 deb 架构别名如 ``amd64``），版本域无需版本源
  响应（``packages.fetch_url`` 仅作占位）。
"""

import logging

from aur_metadata.config import AppConfig
from aur_metadata.constants import ArchEnum
from aur_metadata.utils.deb import (
    DebParseError,
    normalize_deb_version,
    parse_deb_control_version,
)

from .base import PackageFileVersionParser

logger = logging.getLogger(__name__)

# deb 架构名 → 本服务 ArchEnum 值（parser_config.urls 键两套命名均接受）
_DEB_ARCH_ALIASES: dict[str, str] = {
    "amd64": ArchEnum.X86_64.value,
    "x64": ArchEnum.X86_64.value,
    "arm64": ArchEnum.AARCH64.value,
    "loongarch64": ArchEnum.LOONG64.value,
}


class DebControlVersionMixin(PackageFileVersionParser):
    """deb 头部版本提取 mixin：head 字节 → control Version → 归一化版本号"""

    def version_from_package_head(self, head: bytes) -> str | None:
        """从 deb 头部字节提取 ``[epoch:]upstream[-revision]`` 并归一化。

        归一化规则（下游 pkgver 不接受 ``:``/``-``）：去 epoch，revision 与
        upstream 以 ``_`` 连接，如 ``3.14.0-7681`` → ``3.14.0_7681``。
        """
        try:
            raw_version: str = parse_deb_control_version(head)
        except DebParseError as e:
            # 上游更换打包格式（如 control 段迁移/压缩方式变更）属结构变更
            self._log_structure_change(str(e), head)
            return None
        return normalize_deb_version(raw_version)


class DebParser(DebControlVersionMixin):
    """通用 deb 包解析器：URL 静态配置，版本取自 control 段"""

    def __init__(self, app_config: AppConfig, urls: dict[str, str] | None = None) -> None:
        super().__init__(app_config)
        self._urls: dict[str, str] = {
            _DEB_ARCH_ALIASES.get(key, key): url for key, url in (urls or {}).items()
        }

    def package_download_urls(self) -> dict[str, str]:
        """返回配置注入的各架构安装包 URL（静态，版本域无需版本源响应）"""
        return dict(self._urls)

    def parse_url(self, arch: ArchEnum | str, response_data: str) -> str | None:
        """从配置映射取指定架构链接（与响应无关）；缺架构属配置错误走普通日志。

        服务层静态路径直接消费 ``package_download_urls``，本方法不经过，
        仅为保持 ``parse_url`` 契约完整而保留。
        """
        arch_value: str = self._arch_value(arch)
        url: str | None = self._urls.get(arch_value)
        if not url:
            logger.warning("DebParser: parser_config.urls 中无 %s 架构链接", arch_value)
        return url
