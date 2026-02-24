# Django ORM 进阶笔记：Q 对象与 F 对象

## 1. Q 对象 (django.db.models.Q)
**核心用途**：构建复杂的查询逻辑，支持 `OR`、`NOT` 和嵌套查询。

### 基础语法
- **OR (或)**: `Q(condition1) | Q(condition2)`
- **AND (与)**: `Q(condition1) & Q(condition2)` (等同于逗号分隔)
- **NOT (非)**: `~Q(condition)`

> **💡 语法解析：`title__icontains`**
> - **`title`**: 数据库表中的**字段名** (Field)。
> - **`__`**: 双下划线，Django 的语法分隔符。
> - **`icontains`**: **查询谓词** (Lookup)，表示忽略大小写的包含查询。
> - **Q 对象**只是将这些字段查询封装起来，以便进行 `|` (或) 等逻辑运算。

### 实战案例
```python
from django.db.models import Q

# 1. 搜索：标题包含关键词 OR 描述包含关键词
Video.objects.filter(Q(title__icontains='vue') | Q(description__icontains='vue'))

# 2. 排除：获取状态不是 'pending' 且 (点击量 > 100 或 收藏量 > 10) 的视频
Video.objects.filter(
    ~Q(status='pending') & (Q(views_count__gt=100) | Q(favorites_count__gt=10))
)

# 3. 动态构建查询条件
query = Q()
if search_text:
    query |= Q(title__icontains=search_text)
if category_id:
    query &= Q(category_id=category_id)
queryset = Video.objects.filter(query)
```

## 2. 字段查询谓词 (Field Lookups)
**核心用途**：定义 `WHERE` 子句的具体比较逻辑（如：大于、包含、在范围内等）。

### 常用比较符
| 谓词 | 说明 | 示例 (SQL 对应) |
| :--- | :--- | :--- |
| **`__exact`** | 精确匹配 (默认) | `id__exact=1` (`id = 1`) |
| **`__iexact`** | 忽略大小写的精确匹配 | `name__iexact='django'` |
| **`__contains`** | 包含 (区分大小写) | `title__contains='vue'` (`LIKE '%vue%'`) |
| **`__icontains`** | 包含 (忽略大小写) | `title__icontains='vue'` |
| **`__gt`** | 大于 (Greater Than) | `count__gt=10` (`count > 10`) |
| **`__gte`** | 大于等于 (Greater Than or Equal) | `count__gte=10` (`count >= 10`) |
| **`__lt`** | 小于 (Less Than) | `count__lt=10` (`count < 10`) |
| **`__lte`** | 小于等于 (Less Than or Equal) | `count__lte=10` (`count <= 10`) |
| **`__in`** | 在列表/查询集中 | `id__in=[1, 2, 3]` (`id IN (1, 2, 3)`) |
| **`__range`** | 在范围内 (闭区间) | `date__range=(start, end)` (`BETWEEN ... AND ...`) |
| **`__startswith`** | 以...开头 | `name__startswith='Django'` |
| **`__endswith`** | 以...结尾 | `name__endswith='py'` |
| **`__isnull`** | 是否为空 | `desc__isnull=True` (`IS NULL`) |

---

## 3. F 对象 (django.db.models.F)
**核心用途**：在数据库层面引用字段值，实现**字段比较**和**原子性更新**。

### 核心优势
- **性能**：直接在数据库内部处理，减少数据往返内存的开销。
- **并发安全**：避免 "读-改-写" (Read-Modify-Write) 导致的竞态条件。

### 实战案例
```python
from django.db.models import F

# 1. 字段间比较：获取点赞数超过收藏数的视频
Video.objects.filter(likes_count__gt=F('favorites_count'))

# 2. 原子性自增：视频播放量 +1 (推荐用法)
# 即使有 100 个并发请求，数据库也能保证最终结果增加 100
Video.objects.filter(id=video_id).update(views_count=F('views_count') + 1)

# 3. 字符串拼接 (需要配合 Value 和 Concat)
from django.db.models.functions import Concat
from django.db.models import Value
Video.objects.update(title=Concat(F('title'), Value(' (已审核)')))
```

### 注意事项
- **内存刷新**：使用 `F` 更新后，Python 内存中的对象值不会改变，需执行 `obj.refresh_from_db()`。
- **表达式支持**：支持算术运算，如 `F('price') * 0.8`。

---

## 4. 总结对比

| 特性 | 字段查询谓词 | Q 对象 | F 对象 |
| :--- | :--- | :--- | :--- |
| **解决什么** | 基础比较逻辑 | 逻辑组合 (或/非/与) | 值引用、原子操作 |
| **常用标识** | `__gt`, `__icontains` | `|`, `&`, `~` | `F()`, `+`, `-`, `*`, `/` |
| **SQL 对应** | `WHERE col > 10` | `WHERE ... OR/AND/NOT ...` | `SET field = field + 1` |
| **主要位置** | `filter()`, `exclude()` | `filter()`, `get()`, `exclude()` | `filter()`, `update()`, `annotate()` |
