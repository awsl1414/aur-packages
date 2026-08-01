"""Tortoise ORM 模型：定时采集结果库。

字段与 ``db/schema.sql`` 对齐——schema.sql 是结构的事实来源，
本模块仅作为 ORM 访问层；建表/视图/约束以 schema.sql 为准。
"""

from tortoise import Model, fields


class Package(Model):
    """包采集配置（与 app/registry.py 的 PackageEntry 对应，由 DB 持久化）"""

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, unique=True)
    parser_type = fields.CharField(max_length=50)
    fetch_url = fields.CharField(max_length=2048)
    archs = fields.TextField()  # JSON 数组字符串，如 ["x86_64","aarch64"]
    # parser 构造参数 JSON（可空），如 {"region":"sg"} / {"urls":{"x86_64":"..."}}
    parser_config = fields.TextField(null=True)
    hash_algorithm = fields.CharField(max_length=16, default="b2")
    enabled = fields.BooleanField(default=True)
    schedule_type = fields.CharField(max_length=20, default="interval")
    interval_seconds = fields.IntField(null=True)
    cron_expr = fields.CharField(max_length=64, null=True)
    description = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "packages"

    def __str__(self) -> str:
        return f"<Package {self.name}>"


class PackageVersion(Model):
    """版本快照：版本采集域，与 hash 采集解耦独立落库"""

    id = fields.IntField(pk=True)
    package: fields.ForeignKeyRelation[Package] = fields.ForeignKeyField(
        "models.Package", related_name="versions", on_delete=fields.CASCADE
    )
    version = fields.CharField(max_length=64, null=True)
    urls = fields.TextField(null=True)  # 各架构原始下载 URL JSON（arch→url）
    status = fields.CharField(max_length=16)  # success / failed（仅版本抓取结果）
    error = fields.TextField(null=True)
    fetched_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "package_versions"

    def __str__(self) -> str:
        return f"<PackageVersion {self.version} [{self.status}]>"


class PackageHash(Model):
    """文件 hash：版本快照下「架构 × 算法」粒度的记录，逐架构独立成败"""

    id = fields.IntField(pk=True)
    version: fields.ForeignKeyRelation[PackageVersion] = fields.ForeignKeyField(
        "models.PackageVersion", related_name="hashes", on_delete=fields.CASCADE
    )
    arch = fields.CharField(max_length=32)
    algorithm = fields.CharField(max_length=16)
    hash_value = fields.CharField(max_length=256, null=True)
    url = fields.CharField(max_length=2048, null=True)  # 原始下载 URL（parse_url 结果）
    status = fields.CharField(max_length=16)  # success / failed（下载+计算结果）
    error = fields.TextField(null=True)
    fetched_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "package_hashes"
        unique_together = (("version", "arch", "algorithm"),)

    def __str__(self) -> str:
        return f"<PackageHash {self.arch}/{self.algorithm}={self.hash_value}>"
