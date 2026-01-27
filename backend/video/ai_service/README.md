# AI Service 模块

视频平台的 AI 智能服务模块，提供视频内容审核、画面识别、视频摘要等功能。

## 功能模块

### 1. 视频内容审核 (Content Moderation)
- **NSFW 检测**: 识别色情、暴力等不适宜内容
- **敏感内容检测**: 识别政治敏感、血腥等内容
- **自动标记**: 自动标记问题视频帧
- **审核报告**: 生成详细的审核报告

### 2. 画面识别 (Frame Recognition)
- **物体检测**: 识别视频帧中的物体
- **场景分类**: 识别场景类型（室内/室外/城市/自然等）
- **文字识别**: OCR 提取画面中的文字
- **人脸检测**: 检测和定位人脸

### 3. 视频摘要 (Video Summary)
- **关键帧提取**: 自动提取视频关键帧
- **场景分析**: 分析场景切换
- **智能标签**: 自动生成视频标签
- **内容摘要**: 生成视频内容文字摘要

## API 接口

### 视频审核
```
POST /api/ai/moderate/video/{video_id}/
权限: 管理员
功能: 对指定视频进行 AI 内容审核
```

### 画面识别
```
POST /api/ai/recognize/frame/
权限: 已登录用户
参数: video_id, timestamp, frame_data(可选)
功能: 识别视频指定时间点的画面内容
```

### 视频摘要
```
POST /api/ai/summarize/video/{video_id}/
权限: 已登录用户
功能: 生成视频内容摘要
```

### 获取审核结果
```
GET /api/ai/moderation/result/{video_id}/
权限: 管理员
功能: 获取视频的审核结果
```

## 数据模型

### ModerationResult (审核结果)
- video: 关联的视频
- status: 审核状态 (pending/processing/completed/failed)
- result: 审核结果 (safe/unsafe/uncertain)
- confidence: 置信度
- nsfw_score: NSFW 内容得分
- violence_score: 暴力内容得分
- sensitive_score: 敏感内容得分
- flagged_frames: 问题帧列表

### FrameRecognition (画面识别)
- video: 关联的视频
- timestamp: 时间戳
- detected_objects: 识别到的物体
- scene: 场景分类
- text_content: OCR 文字
- faces: 人脸信息

### VideoSummary (视频摘要)
- video: 关联的视频
- summary: 摘要文本
- key_frames: 关键帧列表
- auto_tags: 自动标签
- scene_changes: 场景切换次数

## 异步任务

使用 Celery 处理耗时的 AI 推理任务：

- `moderate_video_task(video_id)`: 异步审核视频
- `summarize_video_task(video_id)`: 异步生成摘要
- `batch_moderate_videos(video_ids)`: 批量审核

## 技术栈

- **深度学习框架**: PyTorch 2.2.0 + CUDA 11.8
- **模型库**: 
  - NSFW 检测: yahoo/open_nsfw
  - 物体检测: YOLOv8
  - 场景分类: CLIP
  - OCR: PaddleOCR
- **异步任务**: Celery + Redis

## 开发计划

### Phase 1 - 基础功能 ✅
- [x] 创建 Django app
- [x] 定义数据模型
- [x] 创建 API 接口
- [x] 配置路由
- [ ] 实现 NSFW 检测
- [ ] 实现暴力内容检测

### Phase 2 - 增强功能
- [ ] 画面识别功能
- [ ] OCR 文字提取
- [ ] 敏感词过滤
- [ ] 审核结果可视化

### Phase 3 - 高级功能
- [ ] 视频摘要生成
- [ ] 智能标签推荐
- [ ] 相似视频检索
- [ ] 模型性能优化

## 使用示例

### Python 调用
```python
from ai_service.tasks import moderate_video_task

# 异步审核视频
task = moderate_video_task.delay(video_id=123)
result = task.get()
```

### 前端调用
```javascript
// 画面识别
const response = await fetch('/api/ai/recognize/frame/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    video_id: 123,
    timestamp: 30.5
  })
});
const result = await response.json();
```

## 注意事项

1. AI 推理任务耗时较长，建议使用异步任务
2. 需要 GPU 支持以获得更好的性能
3. 模型文件较大，需要预先下载
4. 审核结果仅供参考，重要内容需人工复核
