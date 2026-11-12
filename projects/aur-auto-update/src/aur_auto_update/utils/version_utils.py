"""版本比较工具模块"""

from re import split


def parse_version(version: str) -> list[str]:
    """
    解析版本号为可比较的组成部分

    Args:
        version: 版本字符串，如 "3.2.22_251203", "17.3.5"

    Returns:
        版本组成部分列表

    Examples:
        >>> parse_version("3.2.22_251203")
        ['3', '2', '22', '251203']
        >>> parse_version("17.3.5")
        ['17', '3', '5']
    """
    stripped_version: str = version.lstrip("vVrR")
    parts: list[str] = split(r"[.\-~_]", stripped_version)
    return [p for p in parts if p]


def compare_versions(version1: str, version2: str) -> int:
    """
    比较两个版本号

    Args:
        version1: 第一个版本号
        version2: 第二个版本号

    Returns:
        -1: version1 < version2
         0: version1 == version2
         1: version1 > version2

    Examples:
        >>> compare_versions("3.2.21", "3.2.22")
        -1
        >>> compare_versions("3.2.22", "3.2.22")
        0
        >>> compare_versions("3.2.23", "3.2.22")
        1
        >>> compare_versions("3.2.22_251203", "3.2.22")
        1
    """
    v1_parts: list[str] = parse_version(version1)
    v2_parts: list[str] = parse_version(version2)

    max_len: int = max(len(v1_parts), len(v2_parts))

    for i in range(max_len):
        v1_part: str = v1_parts[i] if i < len(v1_parts) else "0"
        v2_part: str = v2_parts[i] if i < len(v2_parts) else "0"

        try:
            v1_num: int = int(v1_part)
            v2_num: int = int(v2_part)

            if v1_num < v2_num:
                return -1
            elif v1_num > v2_num:
                return 1
        except ValueError:
            if v1_part < v2_part:
                return -1
            elif v1_part > v2_part:
                return 1

    return 0
