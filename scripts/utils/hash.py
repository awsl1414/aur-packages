import hashlib
from pathlib import Path
from typing import Dict, Optional, Union

from constants import HashAlgorithmEnum


def calculate_file_hash(
    file_path: Union[str, Path], hash_algorithm: str = HashAlgorithmEnum.SHA512.value
) -> str:
    """
    计算文件的哈希值

    Args:
        file_path: 文件路径
        hash_algorithm: 哈希算法，支持 'sha256', 'sha512'

    Returns:
        文件的哈希值字符串

    Raises:
        FileNotFoundError: 如果文件不存在
        ValueError: 如果不支持指定的哈希算法
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    # 支持的哈希算法
    supported_algorithms = {
        HashAlgorithmEnum.SHA256.value: hashlib.sha256,
        HashAlgorithmEnum.SHA512.value: hashlib.sha512,
    }

    if hash_algorithm.lower() not in supported_algorithms:
        raise ValueError(
            f"不支持的哈希算法: {hash_algorithm}，支持的算法: {list(supported_algorithms.keys())}"
        )

    # 计算哈希值
    hash_func = supported_algorithms[hash_algorithm.lower()]()

    with open(file_path, "rb") as f:
        # 分块读取文件，避免大文件占用过多内存
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)

    return hash_func.hexdigest()


def calculate_sha512(file_path: Union[str, Path]) -> str:
    """
    计算文件的SHA512哈希值

    Args:
        file_path: 文件路径

    Returns:
        文件的SHA512哈希值字符串
    """
    return calculate_file_hash(file_path, HashAlgorithmEnum.SHA512.value)


def calculate_sha256(file_path: Union[str, Path]) -> str:
    """
    计算文件的SHA256哈希值

    Args:
        file_path: 文件路径

    Returns:
        文件的SHA256哈希值字符串
    """
    return calculate_file_hash(file_path, HashAlgorithmEnum.SHA256.value)


def calculate_multiple_hashes(
    file_path: Union[str, Path], algorithms: Optional[list] = None
) -> Dict[str, str]:
    """
    一次性计算文件的多种哈希值

    Args:
        file_path: 文件路径
        algorithms: 要计算的哈希算法列表，默认为 ['sha256', 'sha512']

    Returns:
        包含各种哈希值的字典，键为算法名，值为哈希值
    """
    if algorithms is None:
        algorithms = [HashAlgorithmEnum.SHA256.value, HashAlgorithmEnum.SHA512.value]

    results = {}
    for algorithm in algorithms:
        results[algorithm] = calculate_file_hash(file_path, algorithm)

    return results


def verify_file_hash(
    file_path: Union[str, Path],
    expected_hash: str,
    hash_algorithm: str = HashAlgorithmEnum.SHA512.value,
) -> bool:
    """
    验证文件的哈希值是否匹配预期值

    Args:
        file_path: 文件路径
        expected_hash: 预期的哈希值
        hash_algorithm: 哈希算法，默认为 'sha512'

    Returns:
        如果哈希值匹配返回True，否则返回False
    """
    try:
        actual_hash = calculate_file_hash(file_path, hash_algorithm)
        return actual_hash.lower() == expected_hash.lower()
    except (FileNotFoundError, ValueError):
        return False


def download_and_verify(
    url: str,
    destination: Union[str, Path],
    expected_hash: str,
    hash_algorithm: str = HashAlgorithmEnum.SHA512.value,
) -> bool:
    """
    下载文件并验证其哈希值

    Args:
        url: 下载URL
        destination: 保存路径
        expected_hash: 预期的哈希值
        hash_algorithm: 哈希算法，默认为 'sha512'

    Returns:
        如果下载成功且哈希值匹配返回True，否则返回False
    """
    import httpx

    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        # 下载文件
        with httpx.stream("GET", url) as response:
            response.raise_for_status()
            with open(destination, "wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)

        # 验证哈希值
        return verify_file_hash(destination, expected_hash, hash_algorithm)
    except Exception:
        # 如果下载或验证失败，删除可能已部分下载的文件
        if destination.exists():
            destination.unlink()
        return False


def format_checksum_for_pkgbuild(checksum: str, arch: Optional[str] = None) -> str:
    """
    格式化校验和以用于PKGBUILD文件

    Args:
        checksum: 校验和字符串
        arch: 架构名称，如果为None则返回通用格式

    Returns:
        格式化后的校验和字符串，适用于PKGBUILD文件
    """
    if arch:
        return f"{HashAlgorithmEnum.SHA512.value}sums_{arch}=('{checksum}')"
    else:
        return f"{HashAlgorithmEnum.SHA512.value}sums=('{checksum}')"


def format_multiple_checksums_for_pkgbuild(
    checksums: Dict[str, str], generic_checksum: Optional[str] = None
) -> Dict[str, str]:
    """
    格式化多个校验和以用于PKGBUILD文件

    Args:
        checksums: 各架构的校验和，键为架构名，值为校验和
        generic_checksum: 通用校验和

    Returns:
        格式化后的校验和字典，适用于PKGBUILD文件
    """
    result = {}

    # 添加各架构的校验和
    for arch, checksum in checksums.items():
        result[f"sha512sums_{arch}"] = f"('{checksum}')"

    # 添加通用校验和
    if generic_checksum:
        result["sha512sums"] = f"('{generic_checksum}')"

    return result
