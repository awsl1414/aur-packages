"""URL 解析工具模块"""

import re
from pathlib import Path
from urllib.parse import urlparse

# 文件名组件白名单：排除路径分隔符与控制字符等（version 等组件来自上游
# 响应，携带 ../ 即可穿越下载目录），不安全字符一律替换为下划线
_FILENAME_UNSAFE_RE = re.compile(r"[^A-Za-z0-9._+-]+")


def _sanitize_component(text: str) -> str:
    """文件名组件白名单清洗，防路径穿越"""
    return _FILENAME_UNSAFE_RE.sub("_", text)


def extract_filename_from_url(url: str) -> str:
    """
    从 URL 中提取文件名（包含扩展名）

    支持处理查询参数和片段标识符
    """
    parsed_url = urlparse(url)
    path = parsed_url.path

    filename = Path(path).name

    if not filename:
        return ""

    return filename


def extract_extension_from_url(url: str) -> str:
    """
    从 URL 中提取文件扩展名（包含点号）

    支持复合扩展名（如 .tar.gz）和普通扩展名
    """
    filename = extract_filename_from_url(url)

    compound_extensions = {".tar.gz", ".tar.bz2", ".tar.xz", ".tar.zst"}
    for compound_ext in compound_extensions:
        if filename.endswith(compound_ext):
            return compound_ext

    return Path(filename).suffix


def generate_download_filename(
    package_name: str,
    version: str,
    arch: str,
    url: str,
    default_extension: str = ".deb",
) -> str:
    """
    生成标准化的下载文件名

    格式: {package_name}_{version}_{arch}{extension}
    自动从 URL 提取扩展名，无扩展名时使用默认值；各组件经白名单清洗
    """
    extension = extract_extension_from_url(url) or default_extension
    name = f"{_sanitize_component(package_name)}_{_sanitize_component(version)}_{_sanitize_component(arch)}"
    return f"{name}{extension}"
