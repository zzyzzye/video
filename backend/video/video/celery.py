import os
from celery import Celery
from celery.schedules import crontab

# 设置Django环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'video.settings')

# 创建Celery实例
app = Celery('video')

# 使用Django的settings.py中的设置
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现任务
app.autodiscover_tasks()

# 配置定时任务
app.conf.beat_schedule = {
    'cleanup-deleted-videos-daily': {
        'task': 'videos.tasks.cleanup_deleted_videos',
        'schedule': crontab(hour=3, minute=0),  # 每天凌晨3点执行
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
