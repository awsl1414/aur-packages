"""通用 HTTP / 网络常量（从 config.toml 加载）"""

from app.config import config

# 模拟桌面 Chrome UA；部分上游 CDN/防爬会对非浏览器 UA 返回 403
USER_AGENT: str = config.http.user_agent

# 通用 HTTP 超时（秒）
DEFAULT_TIMEOUT: float = config.http.default_timeout

# 流式下载 / 文件读取的分块大小（字节）
CHUNK_SIZE: int = config.http.chunk_size

# 并发下载 / 签名的最大并发数
MAX_CONCURRENT_DOWNLOADS: int = config.http.max_concurrent_downloads
