# 系统设置视图
import os
import sys
import platform
import psutil
import django
import logging
from django.conf import settings
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsSuperAdmin
from users.models_monitoring import SystemMonitoringLog
import redis

logger = logging.getLogger(__name__)


class SystemSettingsViewSet(viewsets.ViewSet):
    """系统设置视图集 - 仅超级管理员可访问"""
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    @action(detail=False, methods=['get'])
    def info(self, request):
        """获取系统信息"""
        try:
            # 系统基本信息
            system_info = {
                'os': platform.system(),
                'os_version': platform.version(),
                'os_release': platform.release(),
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'python_version': sys.version,
                'django_version': django.get_version(),
            }
            
            # CPU 信息
            cpu_info = {
                'cpu_count': psutil.cpu_count(logical=False),
                'cpu_count_logical': psutil.cpu_count(logical=True),
                'cpu_percent': psutil.cpu_percent(interval=1, percpu=True),
                'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            }
            
            # GPU 信息
            gpu_info = []
            try:
                import pynvml
                
                pynvml.nvmlInit()
                device_count = pynvml.nvmlDeviceGetCount()
                
                for i in range(device_count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    
                    # 基本信息
                    name = pynvml.nvmlDeviceGetName(handle)
                    if isinstance(name, bytes):
                        name = name.decode('utf-8')
                    
                    # UUID
                    try:
                        uuid = pynvml.nvmlDeviceGetUUID(handle)
                        if isinstance(uuid, bytes):
                            uuid = uuid.decode('utf-8')
                    except:
                        uuid = 'N/A'
                    
                    # 利用率
                    try:
                        utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                        gpu_util = utilization.gpu
                        memory_util = utilization.memory
                    except:
                        gpu_util = 0
                        memory_util = 0
                    
                    # 显存信息
                    memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    memory_total = memory_info.total / (1024**2)
                    memory_used = memory_info.used / (1024**2)
                    memory_free = memory_info.free / (1024**2)
                    memory_percent = (memory_used / memory_total) * 100 if memory_total > 0 else 0
                    
                    # 温度
                    try:
                        temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                    except:
                        temperature = 0
                    
                    # 风扇转速
                    try:
                        fan_speed = pynvml.nvmlDeviceGetFanSpeed(handle)
                    except:
                        fan_speed = None
                    
                    # 功耗
                    try:
                        power_usage = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000  # 转换为瓦特
                        power_limit = pynvml.nvmlDeviceGetPowerManagementLimit(handle) / 1000
                    except:
                        power_usage = None
                        power_limit = None
                    
                    # 时钟频率
                    try:
                        graphics_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
                        sm_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_SM)
                        memory_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM)
                    except:
                        graphics_clock = None
                        sm_clock = None
                        memory_clock = None
                    
                    # 最大时钟频率
                    try:
                        max_graphics_clock = pynvml.nvmlDeviceGetMaxClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
                        max_sm_clock = pynvml.nvmlDeviceGetMaxClockInfo(handle, pynvml.NVML_CLOCK_SM)
                        max_memory_clock = pynvml.nvmlDeviceGetMaxClockInfo(handle, pynvml.NVML_CLOCK_MEM)
                    except:
                        max_graphics_clock = None
                        max_sm_clock = None
                        max_memory_clock = None
                    
                    # PCIe 信息
                    try:
                        pcie_gen = pynvml.nvmlDeviceGetCurrPcieLinkGeneration(handle)
                        pcie_width = pynvml.nvmlDeviceGetCurrPcieLinkWidth(handle)
                        max_pcie_gen = pynvml.nvmlDeviceGetMaxPcieLinkGeneration(handle)
                        max_pcie_width = pynvml.nvmlDeviceGetMaxPcieLinkWidth(handle)
                    except:
                        pcie_gen = None
                        pcie_width = None
                        max_pcie_gen = None
                        max_pcie_width = None
                    
                    # 计算能力
                    try:
                        compute_capability = pynvml.nvmlDeviceGetCudaComputeCapability(handle)
                        compute_capability_str = f"{compute_capability[0]}.{compute_capability[1]}"
                    except:
                        compute_capability_str = None
                    
                    # 驱动版本
                    try:
                        driver_version = pynvml.nvmlSystemGetDriverVersion()
                        if isinstance(driver_version, bytes):
                            driver_version = driver_version.decode('utf-8')
                    except:
                        driver_version = 'Unknown'
                    
                    # CUDA 版本
                    try:
                        cuda_version = pynvml.nvmlSystemGetCudaDriverVersion()
                        cuda_version_str = f"{cuda_version // 1000}.{(cuda_version % 1000) // 10}"
                    except:
                        cuda_version_str = None
                    
                    # 性能状态
                    try:
                        performance_state = pynvml.nvmlDeviceGetPerformanceState(handle)
                        performance_state_str = f"P{performance_state}"
                    except:
                        performance_state_str = None
                    
                    gpu_info.append({
                        'id': i,
                        'name': name,
                        'uuid': uuid,
                        'load': round(gpu_util, 2),
                        'memory_util': round(memory_util, 2),
                        'memory_total': round(memory_total, 2),
                        'memory_used': round(memory_used, 2),
                        'memory_free': round(memory_free, 2),
                        'memory_percent': round(memory_percent, 2),
                        'temperature': temperature,
                        'fan_speed': fan_speed,
                        'power_usage': round(power_usage, 2) if power_usage else None,
                        'power_limit': round(power_limit, 2) if power_limit else None,
                        'graphics_clock': graphics_clock,
                        'sm_clock': sm_clock,
                        'memory_clock': memory_clock,
                        'max_graphics_clock': max_graphics_clock,
                        'max_sm_clock': max_sm_clock,
                        'max_memory_clock': max_memory_clock,
                        'pcie_gen': pcie_gen,
                        'pcie_width': pcie_width,
                        'max_pcie_gen': max_pcie_gen,
                        'max_pcie_width': max_pcie_width,
                        'compute_capability': compute_capability_str,
                        'driver': driver_version,
                        'cuda_version': cuda_version_str,
                        'performance_state': performance_state_str,
                    })
                
                pynvml.nvmlShutdown()
                
                if not gpu_info:
                    gpu_info = None
                    
            except Exception as e:
                logger.error(f'获取 GPU 信息失败: {str(e)}')
                gpu_info = None
            
            # 内存信息
            memory = psutil.virtual_memory()
            memory_info = {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percent': memory.percent,
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
            }
            
            # 磁盘信息
            disk = psutil.disk_usage('/')
            disk_info = {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent,
                'total_gb': round(disk.total / (1024**3), 2),
                'used_gb': round(disk.used / (1024**3), 2),
                'free_gb': round(disk.free / (1024**3), 2),
            }
            
            # 数据库信息
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                db_version = cursor.fetchone()[0]
                
                cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
                db_connections = cursor.fetchone()[1]
                
                cursor.execute("SELECT table_schema, SUM(data_length + index_length) / 1024 / 1024 AS size_mb FROM information_schema.tables WHERE table_schema = %s GROUP BY table_schema", [settings.DATABASES['default']['NAME']])
                db_size_result = cursor.fetchone()
                db_size = round(float(db_size_result[1]), 2) if db_size_result else 0
            
            database_info = {
                'engine': settings.DATABASES['default']['ENGINE'],
                'name': settings.DATABASES['default']['NAME'],
                'host': settings.DATABASES['default']['HOST'],
                'port': settings.DATABASES['default']['PORT'],
                'version': db_version,
                'connections': db_connections,
                'size_mb': db_size,
            }
            
            # Redis 信息
            try:
                redis_client = redis.Redis.from_url(settings.CELERY_BROKER_URL)
                redis_info_raw = redis_client.info()
                redis_info = {
                    'version': redis_info_raw.get('redis_version'),
                    'used_memory': redis_info_raw.get('used_memory'),
                    'used_memory_human': redis_info_raw.get('used_memory_human'),
                    'connected_clients': redis_info_raw.get('connected_clients'),
                    'uptime_in_days': redis_info_raw.get('uptime_in_days'),
                    'status': 'connected',
                }
            except Exception as e:
                redis_info = {
                    'status': 'disconnected',
                    'error': str(e),
                }
            
            # 媒体存储信息
            media_root = settings.MEDIA_ROOT
            media_size = 0
            video_count = 0
            
            if os.path.exists(media_root):
                for dirpath, dirnames, filenames in os.walk(media_root):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        if os.path.exists(filepath):
                            media_size += os.path.getsize(filepath)
                            if filepath.endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv')):
                                video_count += 1
            
            media_info = {
                'media_root': media_root,
                'total_size': media_size,
                'total_size_gb': round(media_size / (1024**3), 2),
                'video_count': video_count,
            }
            
            # Django 配置信息
            django_config = {
                'debug': settings.DEBUG,
                'secret_key_length': len(settings.SECRET_KEY),
                'allowed_hosts': settings.ALLOWED_HOSTS,
                'installed_apps_count': len(settings.INSTALLED_APPS),
                'middleware_count': len(settings.MIDDLEWARE),
                'language_code': settings.LANGUAGE_CODE,
                'time_zone': settings.TIME_ZONE,
                'static_url': settings.STATIC_URL,
                'media_url': settings.MEDIA_URL,
            }
            
            # Celery 配置信息
            celery_config = {
                'broker_url': settings.CELERY_BROKER_URL,
                'result_backend': settings.CELERY_RESULT_BACKEND,
                'timezone': settings.CELERY_TIMEZONE,
                'max_tasks_per_child': settings.CELERY_WORKER_MAX_TASKS_PER_CHILD,
                'max_memory_per_child_mb': settings.CELERY_WORKER_MAX_MEMORY_PER_CHILD / 1024,
            }
            
            return Response({
                'system': system_info,
                'cpu': cpu_info,
                'gpu': gpu_info,
                'memory': memory_info,
                'disk': disk_info,
                'database': database_info,
                'redis': redis_info,
                'media': media_info,
                'django': django_config,
                'celery': celery_config,
            })
            
        except Exception as e:
            return Response(
                {'error': f'获取系统信息失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def performance(self, request):
        """获取系统性能实时数据"""
        try:
            # CPU 使用率（每个核心）
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            
            # 磁盘 I/O（获取增量）
            disk_io = psutil.disk_io_counters()
            disk_read_bytes = disk_io.read_bytes
            disk_write_bytes = disk_io.write_bytes
            
            # 从缓存中获取上次的值
            cache_key_read = 'system_disk_read_bytes'
            cache_key_write = 'system_disk_write_bytes'
            last_read = cache.get(cache_key_read, disk_read_bytes)
            last_write = cache.get(cache_key_write, disk_write_bytes)
            
            # 计算增量（MB/s）
            disk_read_delta = max(0, (disk_read_bytes - last_read) / (1024**2))
            disk_write_delta = max(0, (disk_write_bytes - last_write) / (1024**2))
            
            # 保存当前值到缓存
            cache.set(cache_key_read, disk_read_bytes, 60)
            cache.set(cache_key_write, disk_write_bytes, 60)
            
            # 网络 I/O（获取增量）
            net_io = psutil.net_io_counters()
            net_sent_bytes = net_io.bytes_sent
            net_recv_bytes = net_io.bytes_recv
            
            # 从缓存中获取上次的值
            cache_key_sent = 'system_net_sent_bytes'
            cache_key_recv = 'system_net_recv_bytes'
            last_sent = cache.get(cache_key_sent, net_sent_bytes)
            last_recv = cache.get(cache_key_recv, net_recv_bytes)
            
            # 计算增量（MB/s）
            net_sent_delta = max(0, (net_sent_bytes - last_sent) / (1024**2))
            net_recv_delta = max(0, (net_recv_bytes - last_recv) / (1024**2))
            
            # 保存当前值到缓存
            cache.set(cache_key_sent, net_sent_bytes, 60)
            cache.set(cache_key_recv, net_recv_bytes, 60)
            
            # 进程信息
            process_count = len(psutil.pids())
            
            return Response({
                'cpu_percent': cpu_percent,
                'cpu_avg': sum(cpu_percent) / len(cpu_percent),
                'memory_percent': memory.percent,
                'memory_used_gb': round(memory.used / (1024**3), 2),
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'disk_read_mb': round(disk_read_delta, 2),
                'disk_write_mb': round(disk_write_delta, 2),
                'net_sent_mb': round(net_sent_delta, 2),
                'net_recv_mb': round(net_recv_delta, 2),
                'process_count': process_count,
                'timestamp': psutil.boot_time(),
            })
            
        except Exception as e:
            return Response(
                {'error': f'获取性能数据失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def config(self, request):
        """获取系统配置（可编辑的配置项）"""
        try:
            config_data = {
                'site': {
                    'name': getattr(settings, 'SITE_NAME', '视频网站'),
                    'debug': settings.DEBUG,
                    'allowed_hosts': settings.ALLOWED_HOSTS,
                },
                'database': {
                    'engine': settings.DATABASES['default']['ENGINE'],
                    'name': settings.DATABASES['default']['NAME'],
                    'host': settings.DATABASES['default']['HOST'],
                    'port': settings.DATABASES['default']['PORT'],
                },
                'cache': {
                    'backend': settings.CACHES['default']['BACKEND'],
                    'location': settings.CACHES['default']['LOCATION'],
                    'timeout': settings.CACHES['default']['TIMEOUT'],
                },
                'email': {
                    'backend': settings.EMAIL_BACKEND,
                    'host': settings.EMAIL_HOST,
                    'port': settings.EMAIL_PORT,
                    'use_ssl': settings.EMAIL_USE_SSL,
                    'from_email': settings.DEFAULT_FROM_EMAIL,
                },
                'celery': {
                    'broker_url': settings.CELERY_BROKER_URL,
                    'result_backend': settings.CELERY_RESULT_BACKEND,
                    'max_tasks_per_child': settings.CELERY_WORKER_MAX_TASKS_PER_CHILD,
                    'max_memory_per_child_mb': settings.CELERY_WORKER_MAX_MEMORY_PER_CHILD / 1024,
                },
                'media': {
                    'media_url': settings.MEDIA_URL,
                    'media_root': settings.MEDIA_ROOT,
                    'video_upload_path': settings.VIDEO_UPLOAD_PATH,
                    'video_processed_path': settings.VIDEO_PROCESSED_PATH,
                    'video_thumbnail_path': settings.VIDEO_THUMBNAIL_PATH,
                },
                'jwt': {
                    'access_token_lifetime_days': settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].days,
                    'refresh_token_lifetime_days': settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].days,
                },
            }
            
            return Response(config_data)
            
        except Exception as e:
            return Response(
                {'error': f'获取配置信息失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """获取历史监控数据"""
        try:
            # 获取查询参数
            minutes = int(request.query_params.get('minutes', 60))  # 默认最近 60 分钟
            
            # 计算时间范围
            end_time = timezone.now()
            start_time = end_time - timezone.timedelta(minutes=minutes)
            
            # 查询数据
            logs = SystemMonitoringLog.objects.filter(
                created_at__gte=start_time,
                created_at__lte=end_time
            ).order_by('created_at')
            
            # 格式化数据
            data = {
                'time_labels': [],
                'cpu_data': [],
                'memory_data': [],
                'disk_read_data': [],
                'disk_write_data': [],
                'net_sent_data': [],
                'net_recv_data': [],
            }
            
            for log in logs:
                time_str = log.created_at.strftime('%H:%M:%S')
                data['time_labels'].append(time_str)
                data['cpu_data'].append(log.cpu_percent)
                data['memory_data'].append(log.memory_percent)
                data['disk_read_data'].append(log.disk_read_mb)
                data['disk_write_data'].append(log.disk_write_mb)
                data['net_sent_data'].append(log.net_sent_mb)
                data['net_recv_data'].append(log.net_recv_mb)
            
            return Response(data)
            
        except Exception as e:
            return Response(
                {'error': f'获取历史数据失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
