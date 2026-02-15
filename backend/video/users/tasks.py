import psutil
import time
from celery import shared_task
from django.core.cache import cache
from django.utils import timezone
from .models_monitoring import SystemMonitoringLog
import logging

logger = logging.getLogger(__name__)


@shared_task
def collect_system_monitoring_data():
    """收集系统监控数据并保存到数据库"""
    try:
        # CPU 使用率（减少采样时间到 0.1 秒，降低延迟）
        cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
        cpu_avg = sum(cpu_percent) / len(cpu_percent)
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        
        # 磁盘 I/O（计算增量）
        disk_io = psutil.disk_io_counters()
        disk_read_bytes = disk_io.read_bytes
        disk_write_bytes = disk_io.write_bytes
        
        cache_key_read = 'system_disk_read_bytes_task'
        cache_key_write = 'system_disk_write_bytes_task'
        last_read = cache.get(cache_key_read, disk_read_bytes)
        last_write = cache.get(cache_key_write, disk_write_bytes)
        
        disk_read_delta = max(0, (disk_read_bytes - last_read) / (1024**2))
        disk_write_delta = max(0, (disk_write_bytes - last_write) / (1024**2))
        
        cache.set(cache_key_read, disk_read_bytes, 3600)
        cache.set(cache_key_write, disk_write_bytes, 3600)
        
        # 网络 I/O（计算增量）
        net_io = psutil.net_io_counters()
        net_sent_bytes = net_io.bytes_sent
        net_recv_bytes = net_io.bytes_recv
        
        cache_key_sent = 'system_net_sent_bytes_task'
        cache_key_recv = 'system_net_recv_bytes_task'
        last_sent = cache.get(cache_key_sent, net_sent_bytes)
        last_recv = cache.get(cache_key_recv, net_recv_bytes)
        
        net_sent_delta = max(0, (net_sent_bytes - last_sent) / (1024**2))
        net_recv_delta = max(0, (net_recv_bytes - last_recv) / (1024**2))
        
        cache.set(cache_key_sent, net_sent_bytes, 3600)
        cache.set(cache_key_recv, net_recv_bytes, 3600)
        
        # 进程数
        process_count = len(psutil.pids())
        
        # 保存到数据库
        SystemMonitoringLog.objects.create(
            cpu_percent=round(cpu_avg, 2),
            cpu_count=len(cpu_percent),
            memory_percent=round(memory.percent, 2),
            memory_used_gb=round(memory.used / (1024**3), 2),
            memory_available_gb=round(memory.available / (1024**3), 2),
            disk_read_mb=round(disk_read_delta, 2),
            disk_write_mb=round(disk_write_delta, 2),
            net_sent_mb=round(net_sent_delta, 2),
            net_recv_mb=round(net_recv_delta, 2),
            process_count=process_count
        )
        
        # 定期清理旧数据（每小时检查一次，避免频繁查询）
        last_cleanup_key = 'system_monitoring_last_cleanup'
        last_cleanup = cache.get(last_cleanup_key, 0)
        current_time = time.time()
        
        if current_time - last_cleanup > 3600:  # 1 小时
            seven_days_ago = timezone.now() - timezone.timedelta(days=7)
            deleted_count = SystemMonitoringLog.objects.filter(created_at__lt=seven_days_ago).delete()[0]
            
            if deleted_count > 0:
                logger.info(f'清理了 {deleted_count} 条过期监控数据')
            
            cache.set(last_cleanup_key, current_time, 7200)  # 缓存 2 小时
        
        logger.info('系统监控数据收集成功')
        return True
        
    except Exception as e:
        logger.error(f'收集系统监控数据失败: {str(e)}')
        return False
