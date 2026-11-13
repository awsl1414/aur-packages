"""Tortoise ORM 模型：定时采集结果库。

字段与 ``db/schema.sql`` 对齐——schema.sql 是结构的事实来源，
本模块仅作为 ORM 访问层；建表/视图/约束以 schema.sql 为准。
"""

from tortoise import Model, fields


class Package(Model):
    """包采集配置（与 registry.py 的 PackageEntry 对应，由 DB 持久化）"""

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, unique=True)
    parser_type = fields.CharField(max_length=50)
    fetch_url = fields.CharField(max_length=2048)
    archs = fields.TextField()  # JSON 数组字符串，如 ["x86_64","aarch64"]
    # parser 构造参数 JSON（可空），如 {"region":"sg"} / {"urls":{"x86_64":"..."}}
    parser_config = fields.TextField(null=True)
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
    """版本快照：版本变化或采集失败时新增行；版本未变则复用现有行只刷新 urls/fetched_at"""

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
