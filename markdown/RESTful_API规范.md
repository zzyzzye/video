# RESTful API 规范

## URL 设计规则

### 基本原则
- URL 表示资源，使用名词而非动词
- 使用复数形式表示资源集合
- 使用小写字母，单词间用连字符 `-` 分隔
- 避免在 URL 中使用动词，动作由 HTTP 方法表示

### URL 结构示例
```
# 资源集合
GET /api/videos/              # 获取视频列表
POST /api/videos/             # 创建新视频

# 单个资源
GET /api/videos/123/          # 获取 ID 为 123 的视频
PUT /api/videos/123/          # 完整更新视频 123
PATCH /api/videos/123/        # 部分更新视频 123
DELETE /api/videos/123/       # 删除视频 123

# 嵌套资源
GET /api/videos/123/comments/     # 获取视频 123 的评论列表
POST /api/videos/123/comments/    # 为视频 123 创建评论
GET /api/videos/123/comments/456/ # 获取视频 123 的评论 456

# 过滤、排序、分页（通过查询参数）
GET /api/videos/?category=tech&page=2&ordering=-created_at
```

## HTTP 方法

### GET - 获取资源
- 用于查询数据，不修改服务器状态
- 幂等操作（多次请求结果相同）
- 可以被缓存
```python
# Django REST Framework 示例
class VideoViewSet(viewsets.ModelViewSet):
    def list(self, request):
        """获取视频列表"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """获取单个视频详情"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
```

### POST - 创建资源
- 用于创建新资源
- 非幂等操作（多次请求会创建多个资源）
- 请求体包含新资源的数据
```python
def create(self, request):
    """创建新视频"""
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)
```

### PUT - 完整更新资源
- 用于完整替换资源
- 幂等操作
- 需要提供资源的所有字段
```python
def update(self, request, pk=None):
    """完整更新视频"""
    instance = self.get_object()
    serializer = self.get_serializer(instance, data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)
```

### PATCH - 部分更新资源
- 用于部分更新资源
- 幂等操作
- 只需提供需要修改的字段
```python
def partial_update(self, request, pk=None):
    """部分更新视频"""
    instance = self.get_object()
    serializer = self.get_serializer(instance, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)
```

### DELETE - 删除资源
- 用于删除资源
- 幂等操作
```python
def destroy(self, request, pk=None):
    """删除视频"""
    instance = self.get_object()
    instance.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
```

## HTTP 状态码

### 2xx 成功
- `200 OK` - 请求成功，返回数据（GET、PUT、PATCH）
- `201 Created` - 资源创建成功（POST）
- `204 No Content` - 请求成功，无返回内容（DELETE）

### 3xx 重定向
- `301 Moved Permanently` - 资源永久移动
- `302 Found` - 资源临时移动
- `304 Not Modified` - 资源未修改，使用缓存

### 4xx 客户端错误
- `400 Bad Request` - 请求参数错误
- `401 Unauthorized` - 未认证，需要登录
- `403 Forbidden` - 已认证但无权限
- `404 Not Found` - 资源不存在
- `405 Method Not Allowed` - HTTP 方法不允许
- `409 Conflict` - 资源冲突（如重复创建）
- `422 Unprocessable Entity` - 请求格式正确但语义错误（验证失败）
- `429 Too Many Requests` - 请求过于频繁

### 5xx 服务器错误
- `500 Internal Server Error` - 服务器内部错误
- `502 Bad Gateway` - 网关错误
- `503 Service Unavailable` - 服务不可用
- `504 Gateway Timeout` - 网关超时

## Django REST Framework 实践

### 标准 ViewSet 响应
```python
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    
    # 自定义 action
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """发布视频"""
        video = self.get_object()
        if video.status != 'draft':
            return Response(
                {'error': '只能发布草稿状态的视频'},
                status=status.HTTP_400_BAD_REQUEST
            )
        video.status = 'published'
        video.save()
        return Response({'message': '发布成功'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """获取热门视频"""
        videos = self.queryset.filter(status='published').order_by('-views')[:10]
        serializer = self.get_serializer(videos, many=True)
        return Response(serializer.data)
```

### 错误响应格式
```python
# 统一错误响应格式
{
    "error": "错误信息",
    "detail": "详细描述",
    "code": "ERROR_CODE"
}

# 验证错误响应
{
    "title": ["此字段不能为空"],
    "duration": ["请输入有效的数字"]
}
```

### 成功响应格式
```python
# 列表响应（带分页）
{
    "count": 100,
    "next": "http://api.example.com/videos/?page=3",
    "previous": "http://api.example.com/videos/?page=1",
    "results": [
        {
            "id": 1,
            "title": "视频标题",
            "duration": 120
        }
    ]
}

# 单个资源响应
{
    "id": 1,
    "title": "视频标题",
    "description": "视频描述",
    "created_at": "2026-02-21T10:00:00Z"
}
```

## 查询参数规范

### 过滤
```
GET /api/videos/?category=tech&status=published
```

### 排序
```
GET /api/videos/?ordering=-created_at    # 降序
GET /api/videos/?ordering=title          # 升序
```

### 分页
```
GET /api/videos/?page=2&page_size=20
```

### 搜索
```
GET /api/videos/?search=关键词
```

### 字段选择
```
GET /api/videos/?fields=id,title,thumbnail
```

## URL 路由配置示例

```python
# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VideoViewSet, CommentViewSet

router = DefaultRouter()
router.register(r'videos', VideoViewSet, basename='video')
router.register(r'comments', CommentViewSet, basename='comment')

urlpatterns = [
    path('api/', include(router.urls)),
]

# 生成的 URL 路由：
# GET    /api/videos/              -> list
# POST   /api/videos/              -> create
# GET    /api/videos/{pk}/         -> retrieve
# PUT    /api/videos/{pk}/         -> update
# PATCH  /api/videos/{pk}/         -> partial_update
# DELETE /api/videos/{pk}/         -> destroy
# GET    /api/videos/trending/     -> trending (自定义 action)
# POST   /api/videos/{pk}/publish/ -> publish (自定义 action)
```

## 版本控制

### URL 路径版本
```
/api/v1/videos/
/api/v2/videos/
```

### 请求头版本
```
Accept: application/json; version=1.0
```

### 查询参数版本
```
/api/videos/?version=1
```

## 认证和权限

### 请求头
```
Authorization: Bearer <token>
Authorization: Token <token>
```

### 响应示例
```python
# 401 未认证
{
    "detail": "身份认证信息未提供"
}

# 403 无权限
{
    "detail": "您没有执行该操作的权限"
}
```
