from django.db import models
from django.utils import timezone


class SystemMonitoringLog(models.Model):
    """系统监控日志模型"""
    
    # CPU 信息
    cpu_percent = models.FloatField(verbose_name='CPU 使用率(%)')
    cpu_count = models.IntegerField(verbose_name='CPU 核心数', null=True, blank=True)
    
    # 内存信息
    memory_percent = models.FloatField(verbose_name='内存使用率(%)')
    memory_used_gb = models.FloatField(verbose_name='已用内存(GB)')
    memory_available_gb = models.FloatField(verbose_name='可用内存(GB)')
    
    # 磁盘 I/O
    disk_read_mb = models.FloatField(verbose_name='磁盘读取(MB)', default=0)
    disk_write_mb = models.FloatField(verbose_name='磁盘写入(MB)', default=0)
    
    # 网络 I/O
    net_sent_mb = models.FloatField(verbose_name='网络发送(MB)', default=0)
    net_recv_mb = models.FloatField(verbose_name='网络接收(MB)', default=0)
    
    # 进程信息
    process_count = models.IntegerField(verbose_name='进程数', default=0)
    
    # 时间戳
    created_at = models.DateTimeField(verbose_name='记录时间', default=timezone.now, db_index=True)
    
    class Meta:
        verbose_name = '系统监控日志'
        verbose_name_plural = '系统监控日志'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f'监控记录 - {self.created_at.strftime("%Y-%m-%d %H:%M:%S")}'
