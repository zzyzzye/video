# ModelViewSet 核心机制（一）：action 与序列化器动态选择

## 目录
1. [什么是 action](#什么是-action)
2. [action 的工作原理](#action-的工作原理)
3. [get_serializer_class() 动态选择序列化器](#get_serializer_class-动态选择序列化器)
4. [完整的请求流程](#完整的请求流程)
5. [实战示例](#实战示例)
6. [常见问题](#常见问题)

---

## 什么是 action

`action` 是 Django REST Framework (DRF) 中 ViewSet 的核心概念，表示**当前请求要执行的操作类型**。

### 标准 action（ModelViewSet 自带）

```python
# ModelViewSet 提供的标准 CRUD 操作
- list            # 获取列表
- create          # 创建对象
- retrieve        # 获取单个对象详情
- update          # 完整更新对象
- partial_update  # 部分更新对象
- destroy         # 删除对象
```

### 自定义 action（使用 @action 装饰器）

```python
from rest_framework.decorators import action

class UserViewSet(viewsets.ModelViewSet):
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """自定义 action: 获取当前用户"""
        pass
    
    @action(detail=True, methods=['post'])
    def subscribe(self, request, pk=None):
        """自定义 action: 订阅用户"""
        pass
```

---

## action 的工作原理

### 核心：URL + HTTP 方法 → action

**不是单看 HTTP 方法，而是 URL 模式 + HTTP 方法 的组合！**

```python
# 1. 集合 URL（没有 ID）
POST   /api/users/          → action = 'create'
GET    /api/users/          → action = 'list'

# 2. 单个资源 URL（有 ID）
GET    /api/users/1/        → action = 'retrieve'
PUT    /api/users/1/        → action = 'update'
PATCH  /api/users/1/        → action = 'partial_update'
DELETE /api/users/1/        → action = 'destroy'

# 3. 自定义 action URL
GET    /api/users/me/           → action = 'me'
POST   /api/users/1/subscribe/  → action = 'subscribe'
```

### 前后端协作流程（重点）

**URL 相同时，如何区分不同操作？答案：HTTP 方法**

```
前端发送请求
    ↓
axios.put('/api/users/1/', data)  ← 指定 HTTP 方法（PUT）和 URL
    ↓
后端接收请求
    ↓
Django urls.py 根据 URL 路径匹配到对应的 ViewSet
    ↓
Router 根据 HTTP 方法（PUT）决定调用哪个 action
    ↓
执行对应的处理函数（update）
```

**关键理解：**
- 前端通过 axios 指定 HTTP 方法（GET/POST/PUT/DELETE）和 URL
- Django urls.py 根据 URL 路径匹配到对应的 ViewSet
- Router 根据 HTTP 方法决定调用 ViewSet 的哪个 action
- ViewSet 执行对应的处理函数

**示例：同一个 URL，不同的 HTTP 方法**

```javascript
// 前端调用
axios.get('/api/users/1/')      // → retrieve (获取用户)
axios.put('/api/users/1/', data) // → update (更新用户)
axios.delete('/api/users/1/')    // → destroy (删除用户)
```

```python
# 后端处理
class UserViewSet(viewsets.ModelViewSet):
    # 同一个 URL：/api/users/1/
    
    def retrieve(self, request, pk=None):
        """处理 GET /api/users/1/"""
        pass
    
    def update(self, request, pk=None):
        """处理 PUT /api/users/1/"""
        pass
    
    def destroy(self, request, pk=None):
        """处理 DELETE /api/users/1/"""
        pass
```

### Router 的映射规则

```python
# rest_framework/routers.py (简化版)

class DefaultRouter:
    def get_routes(self, viewset):
        return [
            # 集合路由（没有 {pk}）
            Route(
                url=r'^{prefix}/$',
                mapping={
                    'get': 'list',      # GET /users/
                    'post': 'create',   # POST /users/
                },
            ),
            
            # 详情路由（有 {pk}）
            Route(
                url=r'^{prefix}/{pk}/$',
                mapping={
                    'get': 'retrieve',          # GET /users/1/
                    'put': 'update',            # PUT /users/1/
                    'patch': 'partial_update',  # PATCH /users/1/
                    'delete': 'destroy',        # DELETE /users/1/
                },
            ),
        ]
```

### action 的设置时机

```python
# ViewSetMixin.initialize_request() 方法中设置

class ViewSetMixin:
    def initialize_request(self, request, *args, **kwargs):
        """在请求初始化时设置 action"""
        request = super().initialize_request(request, *args, **kwargs)
        
        # 从路由映射中获取 action
        self.action = self.action_map.get(request.method.lower())
        
        return request
```

---

## get_serializer_class() 动态选择序列化器

### 为什么需要动态选择？

不同的操作需要不同的字段和验证规则：

| 操作 | 需求 | 序列化器 |
|------|------|---------|
| 创建用户 | 需要密码字段、密码确认 | `UserCreateSerializer` |
| 更新用户 | 不需要密码，只更新资料 | `UserUpdateSerializer` |
| 查看详情 | 需要更多字段（订阅数等） | `UserDetailSerializer` |
| 列表展示 | 只需要基本字段 | `UserSerializer` |

### 实现方式

```python
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    
    def get_serializer_class(self):
        """根据 action 动态返回序列化器"""
        
        if self.action == 'create':
            return UserCreateSerializer
        
        elif self.action == 'update' or self.action == 'partial_update':
            return UserUpdateSerializer
        
        elif self.action == 'retrieve':
            return UserDetailSerializer
        
        # 默认情况（list 等）
        return UserSerializer
```

### 各序列化器的职责

```python
# 1. UserCreateSerializer - 创建用户
class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise ValidationError("两次密码不一致")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


# 2. UserUpdateSerializer - 更新用户资料
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['last_name', 'bio', 'avatar', 'website', 'gender', 'birthday']
        # 注意：不包含 username、email、password 等敏感字段


# 3. UserDetailSerializer - 查看用户详情
class UserDetailSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    subscribers_count = serializers.IntegerField(read_only=True)
    subscriptions_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'last_name', 'avatar', 
                  'bio', 'subscribers_count', 'subscriptions_count', 
                  'created_at']
        read_only_fields = ['id', 'username', 'email', 'created_at']
    
    def get_avatar(self, obj):
        if obj.avatar:
            return self.context['request'].build_absolute_uri(obj.avatar.url)
        return None


# 4. UserSerializer - 列表展示
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'last_name', 'avatar']
```

---

## 完整的请求流程

### 示例：创建用户

```python
# 1. 前端发送请求
POST /api/users/
Content-Type: application/json

{
    "username": "newuser",
    "email": "user@example.com",
    "password": "SecurePass123",
    "password_confirm": "SecurePass123"
}

# 2. Django URL 路由匹配
# urls.py 中的 router 匹配到 UserViewSet

# 3. Router 确定 action
# URL: /api/users/ (集合 URL)
# HTTP Method: POST
# → action = 'create'

# 4. ViewSetMixin 设置 self.action
self.action = 'create'

# 5. DRF 调用 get_serializer_class()
def get_serializer_class(self):
    if self.action == 'create':  # ← self.action 已经是 'create'
        return UserCreateSerializer  # 返回创建用户的序列化器

# 6. DRF 调用 CreateModelMixin.create()
def create(self, request, *args, **kwargs):
    # 使用 UserCreateSerializer 进行数据验证
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    self.perform_create(serializer)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

# 7. 返回响应
HTTP 201 Created
{
    "id": 1,
    "username": "newuser",
    "email": "user@example.com"
}
```

### 时间线图

```
请求到达
    ↓
URL 路由匹配
    ↓
Router 确定 action 名称 (根据 URL + HTTP 方法)
    ↓
self.action 被设置 (在 initialize_request 中)
    ↓
get_serializer_class() 被调用 (根据 self.action 返回序列化器)
    ↓
对应的 action 方法被调用 (如 create、update 等)
    ↓
返回响应
```

---

## 实战示例

### 完整的 UserViewSet

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """用户视图集"""
    queryset = User.objects.all()
    
    def get_serializer_class(self):
        """根据 action 动态选择序列化器"""
        
        # 打印调试信息（开发时使用）
        print(f"当前 action: {self.action}")
        
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        
        return UserSerializer
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        获取当前用户信息
        GET /api/users/me/
        action = 'me'
        """
        serializer = UserDetailSerializer(request.user, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def subscribe(self, request, pk=None):
        """
        订阅用户
        POST /api/users/1/subscribe/
        action = 'subscribe'
        """
        user = self.get_object()
        if user == request.user:
            return Response(
                {"detail": "不能订阅自己"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 订阅逻辑...
        return Response({"detail": f"成功订阅 {user.username}"})
    
    @action(detail=False, methods=['put', 'patch'], url_path='update-profile')
    def update_profile(self, request):
        """
        更新个人资料
        PUT /api/users/update-profile/
        PATCH /api/users/update-profile/
        action = 'update_profile'
        """
        user = request.user
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

### URL 配置

```python
# backend/video/users/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]

# Router 自动生成的 URL：
# GET    /api/users/              → list
# POST   /api/users/              → create
# GET    /api/users/1/            → retrieve
# PUT    /api/users/1/            → update
# PATCH  /api/users/1/            → partial_update
# DELETE /api/users/1/            → destroy
# GET    /api/users/me/           → me (自定义)
# POST   /api/users/1/subscribe/  → subscribe (自定义)
# PUT    /api/users/update-profile/ → update_profile (自定义)
```

### 前端调用示例

```javascript
// 1. 创建用户 (action = 'create')
const response = await fetch('/api/users/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        username: 'newuser',
        email: 'user@example.com',
        password: 'SecurePass123',
        password_confirm: 'SecurePass123'
    })
});

// 2. 获取用户详情 (action = 'retrieve')
const user = await fetch('/api/users/1/').then(r => r.json());

// 3. 更新用户资料 (action = 'partial_update')
await fetch('/api/users/1/', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        last_name: '新昵称',
        bio: '这是我的个人简介'
    })
});

// 4. 获取当前用户 (action = 'me')
const currentUser = await fetch('/api/users/me/').then(r => r.json());

// 5. 订阅用户 (action = 'subscribe')
await fetch('/api/users/1/subscribe/', {
    method: 'POST'
});
```

---

## 常见问题

### Q1: 为什么 POST 可以区分 create 和其他操作？

**A:** 不是单看 HTTP 方法，而是 **URL + HTTP 方法** 的组合：

```python
POST /api/users/              → action = 'create' (集合 URL)
POST /api/users/1/subscribe/  → action = 'subscribe' (自定义 URL)
POST /api/users/1/set-vip/    → action = 'set_vip' (自定义 URL)
```

### Q2: self.action 是在哪里设置的？

**A:** 在 `ViewSetMixin.initialize_request()` 方法中，根据 Router 的映射规则设置。

```python
# 请求流程
1. 请求到达
2. Router 根据 URL + HTTP 方法确定 action 名称
3. ViewSetMixin.initialize_request() 设置 self.action
4. get_serializer_class() 等方法可以使用 self.action
```

### Q3: 可以在 action 方法中修改 self.action 吗？

**A:** 技术上可以，但**不推荐**。self.action 应该由框架管理，手动修改可能导致不可预期的行为。

### Q4: 如何为自定义 action 指定序列化器？

**A:** 在 `get_serializer_class()` 中添加判断：

```python
def get_serializer_class(self):
    if self.action == 'create':
        return UserCreateSerializer
    elif self.action == 'subscribe':
        return SubscribeSerializer  # 自定义 action 的序列化器
    elif self.action == 'me':
        return UserDetailSerializer
    
    return UserSerializer
```

### Q5: 可以不使用 get_serializer_class() 吗？

**A:** 可以，但不推荐。你可以在每个方法中手动指定序列化器：

```python
@action(detail=False, methods=['get'])
def me(self, request):
    # 手动指定序列化器
    serializer = UserDetailSerializer(request.user, context={'request': request})
    return Response(serializer.data)
```

但使用 `get_serializer_class()` 更加统一和优雅。

