"""基于 aria2c 的异步文件下载器模块"""

import asyncio
import logging
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DownloadResult:
    """下载结果"""

    arch: str
    success: bool
    file_path: Path | None = None
    error: str | None = None


class Downloader:
    """
    基于 aria2c 的异步下载器

    特性：
    - 多连接分片下载（aria2c -x/-s）
    - 断点续传（aria2c -c）
    - 内置重试与指数退避（aria2c --max-tries / --retry-wait）
    - 单实例批量下载（--input-file），进度输出整洁
    """

    def __init__(
        self,
        *,
        max_retries: int = 3,
        retry_wait: int = 1,
        timeout: int = 60,
        connections: int = 16,
        file_allocation: str = "none",
        show_progress: bool = True,
        check_certificate: bool = True,
    ) -> None:
        if not shutil.which("aria2c"):
            raise FileNotFoundError("aria2c not found. Please install aria2 first.")

        if not check_certificate:
            logger.warning(
                "已禁用 aria2c SSL 证书校验（--check-certificate=false），仅建议在受控环境使用"
            )

        self.max_retries = max_retries
        self.retry_wait = retry_wait
        self.timeout = timeout
        self.connections = connections
        self.file_allocation = file_allocation
        self.show_progress = show_progress
        self.check_certificate = check_certificate

    def _build_base_args(self) -> list[str]:
        return [
            "aria2c",
            f"--max-tries={self.max_retries}",
            f"--retry-wait={self.retry_wait}",
            f"--timeout={self.timeout}",
            f"--max-connection-per-server={self.connections}",
            f"--split={self.connections}",
            f"--file-allocation={self.file_allocation}",
            f"--check-certificate={'true' if self.check_certificate else 'false'}",
            "--allow-overwrite=true",
            "--auto-file-renaming=false",
            f"--console-log-level={'notice' if self.show_progress else 'error'}",
            "--summary-interval=0",
            "-c",
        ]

    async def download_all(
        self,
        downloads: dict[str, tuple[str, Path]],
        package_name: str = "package",
    ) -> dict[str, DownloadResult]:
        """
        使用单个 aria2c 实例批量下载多个文件

        Args:
            downloads: {arch: (url, file_path)} 字典
            package_name: 包名称（用于日志标识）

        Returns:
            {arch: DownloadResult} 字典
        """
        if not downloads:
            return {}

        for _arch, (url, file_path) in downloads.items():
            file_path.parent.mkdir(parents=True, exist_ok=True)

        # 写入 aria2c input file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            for _arch, (url, file_path) in downloads.items():
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
            stdout, stderr = await proc.communicate()

            results: dict[str, DownloadResult] = {}
            for arch, (url, file_path) in downloads.items():
                if file_path.exists():
                    results[arch] = DownloadResult(
                        arch=arch,
                        success=True,
                        file_path=file_path,
                    )
                else:
                    # 清理 .aria2 控制文件
                    control_file = Path(f"{file_path}.aria2")
                    if control_file.exists():
                        control_file.unlink()

                    results[arch] = DownloadResult(
                        arch=arch,
                        success=False,
                        error=f"{url} -> download failed",
                    )

            return results

        finally:
            Path(input_file).unlink(missing_ok=True)
