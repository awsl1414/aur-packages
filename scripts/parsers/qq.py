from typing import Any
import re, json
from constants import ArchEnum
from .base_parser import Parser


class QQParser(Parser):
    def parse_version(self, response_data: str | Any) -> str | None:
        """
        解析QQ响应数据，提取版本号

        Args:
            response_data: API响应数据
        Returns:
            版本号字符串，如果解析失败则返回None
        """
        url = self.parse_deb_url(ArchEnum.X86_64, response_data)  # 默认使用x86_64架构
        if not url:
            return None
        pattern = r"QQ_([\d._]+)_amd64"
        matched = re.search(pattern, url)
        if matched:
            return matched.group(1)
        return None

    def parse_deb_url(
        self, arch: ArchEnum | str, response_data: str | Any
    ) -> str | None:
        """
        解析QQ响应数据，提取deb包URL

        Args:
            arch: 架构名称或枚举
            response_data: API响应数据
        Returns:
            deb包URL字符串，如果解析失败则返回None
        """
        # 如果传入的是枚举，获取其值
        arch_value = arch.value if isinstance(arch, ArchEnum) else arch

        pattern = r"var params\s*=\s*(\{.*?\});"
        matched = re.search(pattern, response_data, re.DOTALL)

        if matched:
            try:
                result: dict[str, dict[str, str]] = json.loads(matched.group(1))
                match arch_value:
                    case ArchEnum.X86_64.value:
                        return result.get("x64DownloadUrl", {}).get("deb")
                    case ArchEnum.AARCH64.value:
                        return result.get("armDownloadUrl", {}).get("deb")
                    case ArchEnum.LOONG64.value:
                        loongarch_url = result.get("loongarchDownloadUrl")
                        # loongarchDownloadUrl 可能是字符串或字典
                        if isinstance(loongarch_url, dict):
                            return loongarch_url.get("deb")
                        return loongarch_url
                    case ArchEnum.MIPS64EL.value:
                        mips_url = result.get("mipsDownloadUrl")
                        # mipsDownloadUrl 可能是字符串或字典
                        if isinstance(mips_url, dict):
                            return mips_url.get("deb")
                        return mips_url

            except json.JSONDecodeError:
                print(f"JSON解析失败: {matched.group(1)}")

        return None
