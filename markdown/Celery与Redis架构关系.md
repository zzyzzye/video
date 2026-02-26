# Celery、Redis 与 Django Cache 的关系

## 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         Redis 服务器                              │
│                    (localhost:6379)                              │
├─────────────────────────────────────────────────────────────────┤
│  DB 0: Celery Broker & Result Backend                           │
│  │                                                               │
│  ├─ celery (队列)：存储待执行的任务                               │
│  ├─ celery-task-meta-xxx：存储任务执行结果                        │
│  └─ _kombu.binding.xxx：Celery 内部元数据                        │
├─────────────────────────────────────────────────────────────────┤
│  DB 1: Django Cache                                              │
│  │                                                               │
│  ├─ video_web:1:video_processing_lock:123：视频处理锁             │
│  ├─ video_web:1:system_disk_read_bytes_task：监控数据缓存         │
│  └─ video_web:1:system_monitoring_last_cleanup：清理时间戳        │
├─────────────────────────────────────────────────────────────────┤
│  DB 2: Channels (WebSocket)                                      │
│  │                                                               │
│  ├─ asgi:group:user_123：WebSocket 组成员                        │
│  └─ asgi:specific.abc123：WebSocket 消息队列                     │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Django     │         │   Celery     │         │   Daphne     │
│   (Web)      │         │   Worker     │         │  (WebSocket) │
└──────────────┘         └──────────────┘         └──────────────┘
      │                         │                         │
      │                         │                         │
      ├─────────────────────────┼─────────────────────────┤
      │                         │                         │
      ▼                         ▼                         ▼
  访问 DB 1                 访问 DB 0 & DB 1          访问 DB 2
  (Django Cache)           (Celery + Cache)         (Channels)
```

## 三个组件的职责

### 1. 核心组件与 Redis 数据库分区

项目通过 Redis 的逻辑数据库（DB）实现不同组件的数据隔离：

| 数据库 | 组件 | 数据结构 | 业务职责 |
| :--- | :--- | :--- | :--- |
| **DB 0** | **Celery Broker** | List (Queue) | 任务消息中转。存储待处理的异步任务（Task Message）。 |
| **DB 1** | **Django Cache** | String | 业务状态控制。存储分布式锁（SETNX）及系统监控临时数据。 |
| **DB 2** | **Channels Layer** | Pub/Sub | 实时通信。管理 WebSocket 组及消息分发。 |

---

## 2. 异步处理流程详解

### A. 任务分发阶段 (Django API)
1. **指令调用**：API 视图执行 `process_video.delay(video_id)`。
2. **Redis 操作**：Celery 客户端向 **DB 0** 执行 `LPUSH` 指令，将任务元数据存入 `celery` 列表。
3. **响应机制**：API 不触发转码逻辑，完成消息入队后立即返回 HTTP 响应。

### B. 任务获取阶段 (Celery Worker)
1. **阻塞监听**：Worker 进程通过 `BRPOP` 指令持续监听 **DB 0**。
2. **任务提取**：获取消息后进行反序列化，进入 `process_video` 函数体执行。

---

## 3. 并发控制与转码实现 (核心环节)

### 步骤 1：分布式锁校验
Worker 在调用外部处理工具前，必须通过 **DB 1** 进行并发准入校验：
*   **指令执行**：`cache.add(lock_key, "locked", timeout=7200)`。
*   **原子逻辑**：利用 Redis `SETNX` (Set if Not Exists) 特性。
    *   **返回 True**：DB 1 写入成功，当前 Worker 获得该 `video_id` 的唯一处理权限。
    *   **返回 False**：Key 已存在，说明其他进程正在处理或任务冲突，当前 Worker 立即终止任务。

### 步骤 2：视频解码处理
*   **环境隔离**：Worker 启动 `FFmpeg` 子进程进行 HLS 切片及缩略图生成。
*   **资源消耗**：计算密集型操作在后台 Worker 进程运行，不占用 Django Web 服务的系统资源。

### 步骤 3：数据持久化与锁释放
*   **数据库同步**：Worker 通过 Django ORM 更新视频状态及文件路径。
*   **清理操作**：调用 `cache.delete(lock_key)` 删除 **DB 1** 中的键值，允许该视频后续再次进入处理流程。
*   **状态复位**：Worker 结束当前函数调用，重新回到 **DB 0** 监听新任务。

---

## 4. 技术选型逻辑

*   **DB 隔离原因**：
    *   **故障隔离**：Cache (DB 1) 的清理或溢出不会影响任务队列 (DB 0) 的稳定性。
    *   **监控便利**：可通过 `redis-cli -n [index] KEYS *` 分类检索不同组件的状态。
*   **原子锁必要性**：
    *   **防重复处理**：在高并发或任务重试场景下，确保同一 `video_id` 不会被多个 Worker 同时操作，避免文件损坏及 CPU 资源浪费。
*   **异步化价值**：
    *   **解耦处理**：将长耗时的视频 IO/计算操作从 HTTP 请求链路中剥离，提升系统整体响应吞吐量。

## 完整流程示例：视频转码

### 流程图

```
1. 用户上传视频
   │
   ▼
2. Django 视图接收请求
   │
   ▼
3. 保存视频到数据库
   │
   ▼
4. 触发 Celery 任务
   process_video.delay(video_id)
   │
   ├─→ Celery 将任务放入 Redis DB 0 的队列
   │
   ▼
5. Celery Worker 从队列取出任务
   │
   ▼
6. Worker 尝试获取锁（Django Cache）
   acquire_video_lock(video_id)
   │
   ├─→ 访问 Redis DB 1
   ├─→ cache.add('video_processing_lock:123', 'locked', 7200)
   │
   ▼
7. 如果获取锁成功
   │
   ├─→ 执行转码（FFmpeg）
   │
   ├─→ 保存结果到数据库
   │
   ├─→ 释放锁（Django Cache）
   │   └─→ cache.delete('video_processing_lock:123')
   │
   ├─→ 发送 WebSocket 通知
   │   └─→ 访问 Redis DB 2
   │
   └─→ 任务完成，结果存入 Redis DB 0
```

### 详细代码流程

#### 步骤 1-4：Django 视图触发任务

```python
# videos/views.py
from .tasks import process_video

class VideoViewSet(viewsets.ModelViewSet):
    
    def create(self, request):
        # 1. 接收上传的视频
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 2. 保存到数据库
        video = serializer.save(user=request.user)
        
        # 3. 触发 Celery 任务
        task = process_video.delay(video.id)
        #      ↓
        #      这一步发生了什么？
        #      ├─ Celery 序列化任务参数：{'video_id': 123}
        #      ├─ 生成任务 ID：'abc-123-def-456'
        #      ├─ 将任务放入 Redis DB 0 的队列
        #      └─ 立即返回，不等待任务完成
        
        return Response({
            'video': serializer.data,
            'task_id': task.id  # 返回任务 ID
        })
```

**此时 Redis DB 0 的状态**：

```redis
# 队列中的任务
LPUSH celery '{"task": "videos.tasks.process_video", "args": [123], "kwargs": {}, "id": "abc-123-def-456"}'
```

#### 步骤 5：Celery Worker 取出任务

```python
# Celery Worker 进程（后台运行）

# Worker 不断从 Redis DB 0 的队列中取任务
while True:
    task_data = redis_db0.brpop('celery', timeout=1)
    #           ↓
    #           阻塞式右侧弹出（BRPOP）
    #           如果队列为空，等待 1 秒
    
    if task_data:
        # 解析任务
        task_name = task_data['task']  # 'videos.tasks.process_video'
        task_args = task_data['args']  # [123]
        task_id = task_data['id']      # 'abc-123-def-456'
        
        # 执行任务
        result = execute_task(task_name, task_args)
        
        # 保存结果到 Redis DB 0
        redis_db0.set(f'celery-task-meta-{task_id}', result)
```

#### 步骤 6-7：任务执行（使用 Django Cache）

```python
# videos/tasks.py
from django.core.cache import cache

@shared_task
def process_video(video_id):
    # 6. 尝试获取锁
    lock_key = f"video_processing_lock:{video_id}"
    success = cache.add(lock_key, "locked", timeout=7200)
    #         ↓
    #         这一步发生了什么？
    #         ├─ Django Cache 连接到 Redis DB 1
    #         ├─ 执行：SET video_web:1:video_processing_lock:123 "locked" NX EX 7200
    #         ├─ Redis 返回：OK（成功）或 nil（失败）
    #         └─ Django 转换为：True 或 False
    
    if not success:
        # 锁已被占用，跳过
        return {"status": "skipped"}
    
    try:
        # 7. 执行转码
        video = Video.objects.get(id=video_id)
        
        # 转码逻辑...
        ffmpeg_command = [...]
        subprocess.run(ffmpeg_command)
        
        # 更新数据库
        video.status = 'pending'
        video.save()
        
        # 发送 WebSocket 通知（访问 Redis DB 2）
        send_notification_to_user(video.user_id, {...})
        
        return {"status": "success"}
        
    finally:
        # 释放锁
        cache.delete(lock_key)
        #     ↓
        #     Django Cache 连接到 Redis DB 1
        #     执行：DEL video_web:1:video_processing_lock:123
```

## Redis 三个数据库的详细说明

### DB 0：Celery Broker & Result Backend

**配置**：
```python
# settings.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

**存储内容**：

1. **任务队列**：
```redis
# 默认队列
celery = [
    '{"task": "videos.tasks.process_video", "args": [123], ...}',
    '{"task": "users.tasks.send_email", "args": ["user@example.com"], ...}'
]

# 优先级队列（如果配置了）
celery:priority:high = [...]
celery:priority:low = [...]
```

2. **任务结果**：
```redis
# 任务执行结果
celery-task-meta-abc-123-def-456 = {
    "status": "SUCCESS",
    "result": {"video_id": 123, "status": "success"},
    "traceback": null,
    "children": []
}
```

3. **任务状态**：
```redis
# 任务状态（如果使用了 update_state）
celery-task-meta-abc-123-def-456 = {
    "status": "PROGRESS",
    "result": {"current": 50, "total": 100}
}
```

**查看命令**：
```bash
redis-cli -n 0

# 查看队列长度
LLEN celery

# 查看队列内容（不弹出）
LRANGE celery 0 -1

# 查看任务结果
GET celery-task-meta-abc-123-def-456

# 查看所有任务相关的 key
KEYS celery*
```

### DB 1：Django Cache

**配置**：
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://localhost:6379/1',
        'KEY_PREFIX': 'video_web',
        'TIMEOUT': 3600,
    }
}
```

**存储内容**：

1. **视频处理锁**：
```redis
video_web:1:video_processing_lock:123 = "locked"  (TTL: 7200)
video_web:1:video_processing_lock:456 = "locked"  (TTL: 7200)
```

2. **监控数据缓存**：
```redis
video_web:1:system_disk_read_bytes_task = "1234567890"  (TTL: 3600)
video_web:1:system_disk_write_bytes_task = "9876543210"  (TTL: 3600)
video_web:1:system_net_sent_bytes_task = "5555555555"  (TTL: 3600)
video_web:1:system_net_recv_bytes_task = "6666666666"  (TTL: 3600)
```

3. **清理任务时间戳**：
```redis
video_web:1:system_monitoring_last_cleanup = "1709654321.123"  (TTL: 7200)
```

**查看命令**：
```bash
redis-cli -n 1

# 查看所有缓存 key
KEYS video_web:*

# 查看视频处理锁
KEYS video_web:1:video_processing_lock:*

# 查看某个锁的值和剩余时间
GET video_web:1:video_processing_lock:123
TTL video_web:1:video_processing_lock:123

# 查看监控缓存
KEYS video_web:1:system*
```

### DB 2：Channels (WebSocket)

**配置**：
```python
# settings.py
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379, 2)],
        },
    },
}
```

**存储内容**：

1. **WebSocket 组成员**：
```redis
# 用户 123 的 WebSocket 连接
asgi:group:user_123 = ["specific.abc123def456", "specific.xyz789ghi012"]
```

2. **WebSocket 消息队列**：
```redis
# 某个 channel 的消息队列
asgi:specific.abc123def456 = [
    '{"type": "notification_message", "data": {...}}',
    '{"type": "video_status_update", "data": {...}}'
]
```

**查看命令**：
```bash
redis-cli -n 2

# 查看所有 Channels 相关的 key
KEYS asgi:*

# 查看某个组的成员
SMEMBERS asgi:group:user_123

# 查看某个 channel 的消息
LRANGE asgi:specific.abc123def456 0 -1
```

## 数据流转时序图

```
时间轴：完整的视频转码流程

T0: 用户上传视频
    │
    ├─→ Django 接收请求
    │   └─→ 保存到 MySQL 数据库
    │
    ▼
T1: 触发 Celery 任务
    │
    ├─→ process_video.delay(123)
    │   └─→ 任务放入 Redis DB 0 队列
    │
    ▼
T2: Celery Worker 取出任务
    │
    ├─→ Worker 从 Redis DB 0 弹出任务
    │   └─→ 开始执行 process_video(123)
    │
    ▼
T3: 尝试获取锁
    │
    ├─→ cache.add('video_processing_lock:123', ...)
    │   └─→ 访问 Redis DB 1
    │       ├─→ 检查 key 是否存在
    │       └─→ 设置 key 和过期时间
    │
    ▼
T4: 执行转码
    │
    ├─→ FFmpeg 转码（本地操作，不涉及 Redis）
    │   └─→ 生成 HLS 文件
    │
    ▼
T5: 更新数据库
    │
    ├─→ video.status = 'pending'
    │   └─→ 保存到 MySQL 数据库
    │
    ▼
T6: 发送 WebSocket 通知
    │
    ├─→ send_notification_to_user(123, ...)
    │   └─→ 访问 Redis DB 2
    │       ├─→ 将消息放入组 'user_123'
    │       └─→ Daphne 接收并推送给前端
    │
    ▼
T7: 释放锁
    │
    ├─→ cache.delete('video_processing_lock:123')
    │   └─→ 访问 Redis DB 1
    │       └─→ 删除 key
    │
    ▼
T8: 任务完成
    │
    ├─→ 返回结果
    │   └─→ 保存到 Redis DB 0
    │       └─→ celery-task-meta-abc-123-def-456
    │
    ▼
T9: 前端查询任务状态（可选）
    │
    └─→ GET /api/tasks/abc-123-def-456/
        └─→ Celery 从 Redis DB 0 读取结果
            └─→ 返回给前端
```

## 为什么要分开使用三个数据库？

### 1. 避免 Key 冲突

如果都用 DB 0：
```redis
# Celery 的 key
celery = [...]

# 如果 Django Cache 也用 DB 0，可能会有：
celery = "locked"  # 冲突！覆盖了 Celery 的队列
```

### 2. 便于管理和监控

```bash
# 只查看 Celery 的数据
redis-cli -n 0 KEYS *

# 只查看 Cache 的数据
redis-cli -n 1 KEYS *

# 只查看 WebSocket 的数据
redis-cli -n 2 KEYS *
```

### 3. 便于清理和维护

```bash
# 清空 Cache，不影响 Celery
redis-cli -n 1 FLUSHDB

# 清空 WebSocket，不影响其他
redis-cli -n 2 FLUSHDB
```

### 4. 不同的过期策略

- DB 0（Celery）：任务结果可能需要保留较长时间
- DB 1（Cache）：缓存数据可以设置较短的过期时间
- DB 2（WebSocket）：消息队列需要快速消费

## 配置文件总览

```python
# settings.py

# ============ Celery 配置 ============
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# ============ Django Cache 配置 ============
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://localhost:6379/1',
        'KEY_PREFIX': 'video_web',
        'TIMEOUT': 3600,
    }
}

# ============ Channels 配置 ============
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379, 2)],
        },
    },
}
```

## 常用调试命令

### 查看整体状态

```bash
# 连接 Redis
redis-cli

# 查看所有数据库的 key 数量
INFO keyspace

# 输出：
# db0:keys=5,expires=2
# db1:keys=10,expires=8
# db2:keys=3,expires=0
```

### 监控实时操作

```bash
# 监控所有数据库的操作
redis-cli MONITOR

# 输出：
# 1709654321.123456 [0 127.0.0.1:12345] "LPUSH" "celery" "..."
# 1709654321.234567 [1 127.0.0.1:12346] "SET" "video_web:1:video_processing_lock:123" "locked" "NX" "EX" "7200"
# 1709654321.345678 [2 127.0.0.1:12347] "SADD" "asgi:group:user_123" "specific.abc123"
```

### 查看内存使用

```bash
redis-cli INFO memory

# 输出：
# used_memory:1048576
# used_memory_human:1.00M
# used_memory_rss:2097152
# used_memory_peak:3145728
```

## 总结

**Celery、Redis、Django Cache 的关系**：

1. **Celery** 是任务队列系统，负责异步执行任务
2. **Redis** 是数据存储，为 Celery 和 Django Cache 提供存储服务
3. **Django Cache** 是缓存系统，使用 Redis 存储缓存数据

**数据流转**：
- Django 视图 → Celery 任务 → Redis DB 0（队列）
- Celery Worker → Redis DB 0（取任务）
- Celery Worker → Redis DB 1（获取锁、缓存数据）
- Celery Worker → Redis DB 2（发送 WebSocket 消息）

**三个数据库的职责**：
- DB 0：Celery 的任务队列和结果存储
- DB 1：Django Cache 的缓存数据
- DB 2：Channels 的 WebSocket 消息队列

这样设计实现了职责分离、避免冲突、便于管理。
