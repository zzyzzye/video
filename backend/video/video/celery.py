import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'video.settings')

app = Celery('video')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'cleanup-deleted-videos-daily': {
        'task': 'videos.tasks.cleanup_deleted_videos',
        'schedule': crontab(hour=3, minute=0),  
    },
    'publish-scheduled-videos': {
        'task': 'videos.tasks.publish_scheduled_videos',
        'schedule': crontab(minute='*/1'), 
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
