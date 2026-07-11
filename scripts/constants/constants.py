"""常量定义模块"""

from enum import Enum

DOWNLOAD_DIR = "downloads"

# 通用 HTTP 请求头：QQ 签名、其它自定义 HTTP 客户端共用。
# 模拟 Chrome 150 on Linux；部分上游（CDN/防爬）会对非浏览器 UA 返回 403。
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
)

# 通用 HTTP 超时（秒）：用于 ``httpx.Client(timeout=...)`` 等自定义 HTTP 客户端。
# Fetcher 的超时由 config.yaml 的 settings.download.timeout 控制，不走这里。
DEFAULT_TIMEOUT: float = 30.0


class ArchEnum(Enum):
    """支持的 CPU 架构"""

    X86_64 = "x86_64"
    AARCH64 = "aarch64"
    LOONG64 = "loong64"
    MIPS64EL = "mips64el"
    ANY = "any"


class HashAlgorithmEnum(Enum):
    """哈希算法"""

    SHA256 = "sha256"
    SHA512 = "sha512"
    B2 = "b2"


class ParserEnum(Enum):
    """解析器名称"""

    QQ = "QQParser"
    NAVICAT_PREMIUM_CS = "NavicatPremiumCSParser"
    TRAE = "TraeParser"
    TRAE_SG = "TraeParser_SG"
    TRAE_US = "TraeParser_US"
    TRAE_CN = "TraeParser_CN"
    ZEN = "ZenParser"
    BT_DUALBOOT = "PyPIParser"
