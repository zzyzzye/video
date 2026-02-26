import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'video.settings')

app = Celery('video')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

# Celery Beat 定时任务配置
app.conf.beat_schedule = {
    # 任务1：每天凌晨 3 点自动清理已标记为“删除”的视频文件和记录
    'cleanup-deleted-videos-daily': {
        'task': 'videos.tasks.cleanup_deleted_videos',
        'schedule': crontab(hour=3, minute=0),  
    },
    # 任务2：每隔 1 分钟检查一次数据库，发布到达预约时间的视频
    'publish-scheduled-videos': {
        'task': 'videos.tasks.publish_scheduled_videos',
        'schedule': crontab(minute='*/1'), 
    },
    # 任务3：每 10 秒采集一次服务器 CPU/内存等监控数据，用于后台实时仪表盘显示
    'collect-system-monitoring-data': {
        'task': 'users.tasks.collect_system_monitoring_data',
        'schedule': 10.0,
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
