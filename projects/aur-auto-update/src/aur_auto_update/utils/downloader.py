"""基于 aria2c 的异步文件下载器模块"""

import asyncio
import logging
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# URL 控制字符：aria2c input file 以换行分隔指令，URL 携带 \n/\r 即可注入
# dir=/out= 等任意指令实现任意路径写文件，写入前必须拒绝
_URL_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")


@dataclass(frozen=True)
class DownloadResult:
    """下载结果"""

    success: bool
    file_path: Path | None = None
    error: str | None = None


class Downloader:
    """
    基于 aria2c 的异步下载器

    特性：
    - 多连接分片下载（aria2c -x/-s）
    - 断点续传（aria2c -c）
    - 内置重试（aria2c --max-tries / --retry-wait，固定间隔等待）
    - 单实例批量下载（--input-file）；show_progress=False 时静默执行（输出被丢弃）
    """

    def __init__(
        self,
        *,
        max_retries: int = 3,
        retry_wait: int = 1,
        timeout: int = 60,
        connections: int = 16,
        show_progress: bool = True,
        verify_ssl: bool = True,
    ) -> None:
        if not shutil.which("aria2c"):
            raise FileNotFoundError("未找到 aria2c，请先安装 aria2（sudo pacman -S aria2）")

        if not verify_ssl:
            logger.warning(
                "已禁用 aria2c SSL 证书校验（--check-certificate=false），仅建议在受控环境使用"
            )

        self.max_retries = max_retries
        self.retry_wait = retry_wait
        self.timeout = timeout
        self.connections = connections
        self.show_progress = show_progress
        self.verify_ssl = verify_ssl

    def _build_base_args(self) -> list[str]:
        return [
            "aria2c",
            f"--max-tries={self.max_retries}",
            f"--retry-wait={self.retry_wait}",
            f"--timeout={self.timeout}",
            f"--max-connection-per-server={self.connections}",
            f"--split={self.connections}",
            # none：跳过预分配，避免大文件写盘两次
            "--file-allocation=none",
            f"--check-certificate={'true' if self.verify_ssl else 'false'}",
            "--allow-overwrite=true",
            "--auto-file-renaming=false",
            f"--console-log-level={'notice' if self.show_progress else 'error'}",
            "--summary-interval=0",
            "-c",
        ]

    async def download_all(
        self, downloads: dict[str, tuple[str, Path]]
    ) -> dict[str, DownloadResult]:
        """
        使用单个 aria2c 实例批量下载多个文件

        Args:
            downloads: {arch: (url, file_path)} 字典

        Returns:
            {arch: DownloadResult} 字典
        """
        results: dict[str, DownloadResult] = {}
        safe_downloads: dict[str, tuple[str, Path]] = {}
        for arch, (url, file_path) in downloads.items():
            if _URL_CONTROL_CHARS_RE.search(url):
                results[arch] = DownloadResult(
                    success=False,
                    error=f"URL 含非法控制字符，已拒绝下载: {url!r}",
                )
            else:
                safe_downloads[arch] = (url, file_path)
        if not safe_downloads:
            return results

        for file_path in {p for _, p in safe_downloads.values()}:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        # 写入 aria2c input file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            for url, file_path in safe_downloads.values():
                f.write(f"{url}\n")
                f.write(f"  dir={file_path.parent}\n")
                f.write(f"  out={file_path.name}\n\n")
            input_file = f.name

        try:
            args = self._build_base_args() + [f"--input-file={input_file}"]

            pipe_output = not self.show_progress
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE if pipe_output else None,
                stderr=asyncio.subprocess.PIPE if pipe_output else None,
            )
            # 仅需等待进程退出并排空管道，输出本身不使用
            await proc.communicate()

            for arch, (url, file_path) in safe_downloads.items():
                if file_path.exists():
                    results[arch] = DownloadResult(
                        success=True,
                        file_path=file_path,
                    )
                else:
                    # 清理 .aria2 控制文件
                    control_file = Path(f"{file_path}.aria2")
                    if control_file.exists():
                        control_file.unlink()

                    results[arch] = DownloadResult(
                        success=False,
                        error=f"下载失败: {url}",
                    )

            return results

        finally:
            Path(input_file).unlink(missing_ok=True)
