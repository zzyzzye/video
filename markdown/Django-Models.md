# Django Models 核心笔记：从基础到高级配置

**Models** 是 Django 的灵魂，它定义了数据库的结构。Django 通过 ORM（对象关系映射）将 Python 类映射为数据库表。

---

## 1. 基础结构
每个模型都是 `django.db.models.Model` 的子类。

```python
from django.db import models

class Video(models.Model):
    title = models.CharField(max_length=100, verbose_name="标题")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'videos'      # 自定义数据库表名
        ordering = ['-created_at'] # 默认排序
```

---

## 2. 常用字段类型 (Field Types)

| 类型 | 说明 | 关键参数 |
| :--- | :--- | :--- |
| **`CharField`** | 短文本 | `max_length` (必须) |
| **`TextField`** | 长文本 | 适合描述、内容 |
| **`IntegerField`** | 整数 | `default=0` |
| **`BooleanField`** | 布尔值 | `default=True` |
| **`DateTimeField`** | 日期时间 | `auto_now_add` (创建时), `auto_now` (更新时) |
| **`ForeignKey`** | 外键 (多对一) | `to`, `on_delete`, `related_name` |
| **`ManyToManyField`**| 多对多 | `to`, `through` (自定义中间表) |
| **`FileField`** | 文件上传 | `upload_to='path/'` |
| **`ImageField`** | 图片上传 | 需安装 `Pillow` |

---

## 3. 字段核心参数 (Field Options)

*   **`null=True`**：数据库级别，允许该字段在数据库中存储 `NULL`。
*   **`blank=True`**：表单验证级别，允许用户在提交表单/管理后台时留空。
*   **`default`**：设置默认值。
*   **`choices`**：提供预设选项。
    ```python
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('published', '已发布'),
    ]
    status = models.CharField(choices=STATUS_CHOICES, default='draft')
    ```
*   **`verbose_name`**：字段的人类可读名称（后台显示）。
*   **`related_name`**：反向查询名称。例如 `user.videos.all()`。

---

## 4. 关系配置 (Relationships)

### 4.1 ForeignKey (一对多)
最常用的关系，必须设置 `on_delete`。
*   **`CASCADE`**：级联删除。主表删了，从表跟着删。
*   **`SET_NULL`**：主表删了，从表对应字段设为 `NULL` (需配合 `null=True`)。
*   **`PROTECT`**：保护模式。如果有关联数据，禁止删除主表。

### 4.2 ManyToManyField (多对多)
*   **`symmetrical=False`**：在 `self` 关联（如好友关系）中非对称。
*   **`through`**：当你需要存储额外的关联信息（如：关注时间）时，使用自定义中间表。

---

## 5. Meta 配置 (元数据)
定义模型在数据库层面的非字段属性。

```python
class Meta:
    db_table = 'my_video_table'      # 数据库表名
    ordering = ['-created_at']       # 默认排序规则
    verbose_name = '视频'            # 后台单数显示
    verbose_name_plural = '视频列表'  # 后台复数显示
    unique_together = ['user', 'video'] # 联合唯一索引
    constraints = [                 # 复杂约束（Django 2.2+ 推荐）
        models.UniqueConstraint(fields=['user', 'video'], name='unique_like')
    ]
```

---

## 6. 虚拟属性 (`@property`)
**核心用途**：将方法伪装成属性，用于封装复杂的逻辑判断或动态计算值。它们**不在数据库中存储**。

```python
class User(models.Model):
    is_vip = models.BooleanField(default=False)
    vip_expire_time = models.DateTimeField(null=True, blank=True)

    @property
    def is_vip_active(self):
        """动态判断 VIP 是否有效"""
        if not self.is_vip or not self.vip_expire_time:
            return False
        return self.vip_expire_time > timezone.now()
```
*   **优点**：调用简单（`user.is_vip_active`），代码清晰。
*   **注意**：无法直接在 `filter()` 中使用，因为数据库里没有这一列。

---

## 7. 标准模型定义模板 (最佳实践)
一个标准的模型建议遵循以下结构顺序：

```python
class StandardModel(models.Model):
    # 1. 字段定义 (Fields)
    title = models.CharField(max_length=100)
    
    # 2. 自定义管理器 (Managers - 可选)
    # objects = CustomManager()
    
    # 3. Meta 配置 (元数据)
    class Meta:
        verbose_name = "标准模型"
        ordering = ['-id']

    # 4. __str__ 方法
    def __str__(self):
        return self.title

    # 5. 常用方法 (如 get_absolute_url)
    
    # 6. 重写的保存/删除方法 (Hooks)
    def save(self, *args, **kwargs):
        # 逻辑处理
        super().save(*args, **kwargs)

    # 7. 虚拟属性 (Properties)
    @property
    def summary(self):
        return self.title[:20]
```

---

## 8. 进阶技巧：生命周期钩子
*   **`save()`**：适合处理简单的字段逻辑更新。
*   **Signals (信号)**：适合跨模型解耦（如：用户注册后自动发送欢迎邮件）。

---

## 9. 数据迁移指令
1.  **`python manage.py makemigrations`**：将代码变更生成迁移脚本。
2.  **`python manage.py migrate`**：将脚本同步到数据库。
3.  **`python manage.py showmigrations`**：查看迁移状态。
