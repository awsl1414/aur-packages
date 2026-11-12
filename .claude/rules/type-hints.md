# 类型注解规范

项目严格使用类型注解，所有函数和方法必须包含完整的类型注解。

## 基本规则

1. **所有函数必须有返回类型注解**
   ```python
   # ✓ 正确
   def get_version(url: str) -> str | None:
       ...

   # ✗ 错误（缺少返回类型）
   def get_version(url: str):
       ...
   ```

2. **所有参数必须有类型注解**
   ```python
   # ✓ 正确
   async def download_file(url: str, path: Path, retries: int = 3) -> bool:
       ...

   # ✗ 错误（缺少参数类型）
   async def download_file(url, path, retries = 3):
       ...
   ```

3. **使用 Python 3.13+ 的现代类型注解语法**
   ```python
   # ✓ 使用 | 联合类型（Python 3.10+）
   def parse_version(data: str | None) -> str | None:
       ...

   # ✓ 使用 list/dict 泛型（Python 3.9+）
   def get_urls(arch: str) -> list[str]:
       return []

   def get_config() -> dict[str, str]:
       return {}

   # ✗ 避免（旧式语法）
   from typing import List, Dict, Optional, Union
   def parse_version(data: Union[str, None]) -> Optional[str]:
       ...
   ```

4. **类属性和方法注解**
   ```python
   class PackageUpdater:
       parsers: dict[str, BaseParser]  # 类属性类型注解

       def __init__(self) -> None:  # __init__ 返回 None
           self.config: ConfigLoader = ConfigLoader.load_from_yaml()

       def update_package(self, name: str, config: PackageConfig) -> bool:
           ...
   ```

5. **异步函数类型注解**
   ```python
   async def fetch_text(url: str) -> str | None:
       ...

   async def download_all(urls: dict[str, str]) -> dict[str, bool]:
       ...
   ```

6. **复杂类型使用 typing 模块**
   ```python
   from typing import Callable, Any

   def process_data(
       data: dict[str, Any],
       callback: Callable[[str], bool] | None = None
   ) -> bool:
       ...
   ```

## 类型检查

项目使用 **ty**（Astral 开发的快速 Python 类型检查器）进行静态类型检查：

```bash
uv run ty check scripts/       # 运行类型检查（源码位于 scripts/）
uv run ty check scripts/core/  # 检查特定目录
uv run ty check -v             # 详细输出
```

## 类型存根

对于第三方库缺少类型注解的情况，使用类型存根：

```bash
uv add --dev types-requests types-pyyaml
```
