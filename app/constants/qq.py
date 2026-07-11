"""QQ 解析器专属常量（从 config.toml 加载）"""

from app.config import config

# QQ 版本信息数据源（pcConfig.json）
QQ_FETCH_URL: str = config.qq.fetch_url

# im.qq.com 站点 origin（签名请求 Origin 头）
QQ_ORIGIN: str = config.qq.origin

# im.qq.com 签名服务相关 URL
QQ_COOKIE_URL: str = config.qq.cookie_url
QQ_SIGN_URL: str = config.qq.sign_url

# GetSign RPC 的 OIDB 协议参数：
# command 0x9b8e 为 URL 签名命令码，service_type 1 为服务类型
QQ_OIDB_COMMAND: str = config.qq.oidb_command
QQ_OIDB_SERVICE_TYPE: int = config.qq.oidb_service_type
