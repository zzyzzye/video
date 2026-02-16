from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


class SystemOperationLog(models.Model):
    """系统操作日志模型"""
    
    LOG_TYPES = [
        ('login', '登录'),
        ('logout', '登出'),
        ('user_create', '创建用户'),
        ('user_update', '更新用户'),
        ('user_delete', '删除用户'),
        ('admin_create', '创建管理员'),
        ('admin_update', '更新管理员'),
        ('admin_delete', '删除管理员'),
        ('video_review', '视频审核'),
        ('video_delete', '删除视频'),
        ('comment_delete', '删除评论'),
        ('report_handle', '处理举报'),
        ('system_config', '系统配置'),
        ('permission_change', '权限变更'),
        ('other', '其他'),
    ]
    
    LEVELS = [
        ('info', '信息'),
        ('warning', '警告'),
        ('error', '错误'),
        ('critical', '严重'),
    ]
    
    operator = models.ForeignKey(
        'users.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='operation_logs',
        verbose_name='操作者'
    )
    operator_username = models.CharField(max_length=150, verbose_name='操作者用户名', db_index=True)
    operator_ip = models.GenericIPAddressField(verbose_name='操作 IP', null=True, blank=True)
    
    log_type = models.CharField(max_length=50, choices=LOG_TYPES, verbose_name='日志类型', db_index=True)
    level = models.CharField(max_length=20, choices=LEVELS, default='info', verbose_name='日志级别')
    
    module = models.CharField(max_length=100, verbose_name='模块', db_index=True)
    action = models.CharField(max_length=200, verbose_name='操作')
    description = models.TextField(verbose_name='描述', blank=True)
    
    target_type = models.CharField(max_length=50, verbose_name='目标类型', blank=True)
    target_id = models.IntegerField(verbose_name='目标 ID', null=True, blank=True)
    target_name = models.CharField(max_length=200, verbose_name='目标名称', blank=True)
    
    request_method = models.CharField(max_length=10, verbose_name='请求方法', blank=True)
    request_path = models.CharField(max_length=500, verbose_name='请求路径', blank=True)
    request_params = models.JSONField(verbose_name='请求参数', null=True, blank=True)
    
    response_code = models.IntegerField(verbose_name='响应代码', null=True, blank=True)
    response_message = models.TextField(verbose_name='响应消息', blank=True)
    
    duration = models.FloatField(verbose_name='执行时长(秒)', null=True, blank=True)
    
    user_agent = models.CharField(max_length=500, verbose_name='User Agent', blank=True)
    
    created_at = models.DateTimeField(verbose_name='创建时间', default=timezone.now, db_index=True)
    
    class Meta:
        verbose_name = '系统操作日志'
        verbose_name_plural = '系统操作日志'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['operator_username', '-created_at']),
            models.Index(fields=['log_type', '-created_at']),
            models.Index(fields=['level', '-created_at']),
        ]
    
    def __str__(self):
        return f'{self.operator_username} - {self.get_log_type_display()} - {self.created_at.strftime("%Y-%m-%d %H:%M:%S")}'
