"""
操作日志记录中间件
"""
import time
import json
from django.utils.deprecation import MiddlewareMixin
from users.models_logs import SystemOperationLog


def get_client_ip(request):
    """获取客户端 IP 地址"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class OperationLogMiddleware(MiddlewareMixin):
    """操作日志记录中间件"""
    
    # 需要记录的路径前缀
    LOG_PATHS = [
        '/api/users/',
        '/api/videos/',
        '/api/admin/',
    ]
    
    # 不记录的路径
    EXCLUDE_PATHS = [
        '/api/users/me/',
        '/api/users/notifications/',
        '/api/users/dashboard/',
    ]
    
    # 需要记录的方法
    LOG_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    
    def process_request(self, request):
        """记录请求开始时间"""
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """记录操作日志"""
        # 检查是否需要记录
        if not self._should_log(request):
            return response
        
        # 计算执行时长
        duration = None
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
        
        # 获取用户信息
        user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
        
        # 确定日志类型和级别
        log_type, level = self._determine_log_type(request, response)
        
        # 获取操作描述
        action, description = self._get_action_description(request, response)
        
        # 创建日志记录
        try:
            SystemOperationLog.objects.create(
                operator=user,
                operator_username=user.username if user else 'Anonymous',
                operator_ip=get_client_ip(request),
                log_type=log_type,
                level=level,
                module=self._get_module(request.path),
                action=action,
                description=description,
                request_method=request.method,
                request_path=request.path,
                response_code=response.status_code,
                duration=duration,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            )
        except Exception as e:
            # 日志记录失败不应影响正常请求
            print(f"记录操作日志失败: {e}")
        
        return response
    
    def _should_log(self, request):
        """判断是否需要记录日志"""
        # 只记录特定方法
        if request.method not in self.LOG_METHODS:
            return False
        
        # 检查路径是否在记录范围内
        path = request.path
        should_log = any(path.startswith(prefix) for prefix in self.LOG_PATHS)
        
        if not should_log:
            return False
        
        # 检查是否在排除列表中
        is_excluded = any(path.startswith(exclude) for exclude in self.EXCLUDE_PATHS)
        
        return not is_excluded
    
    def _determine_log_type(self, request, response):
        """确定日志类型和级别"""
        path = request.path
        method = request.method
        status_code = response.status_code
        
        # 根据响应状态码确定级别
        if status_code >= 500:
            level = 'error'
        elif status_code >= 400:
            level = 'warning'
        else:
            level = 'info'
        
        # 根据路径和方法确定日志类型
        if '/users/' in path:
            if method == 'POST':
                log_type = 'user_create'
            elif method in ['PUT', 'PATCH']:
                log_type = 'user_update'
            elif method == 'DELETE':
                log_type = 'user_delete'
            else:
                log_type = 'other'
        elif '/videos/' in path:
            if 'review' in path:
                log_type = 'video_review'
            elif method == 'DELETE':
                log_type = 'video_delete'
            else:
                log_type = 'other'
        elif '/comments/' in path and method == 'DELETE':
            log_type = 'comment_delete'
        elif '/reports/' in path:
            log_type = 'report_handle'
        elif '/admins/' in path:
            if method == 'POST':
                log_type = 'admin_create'
            elif method in ['PUT', 'PATCH']:
                log_type = 'admin_update'
            elif method == 'DELETE':
                log_type = 'admin_delete'
            else:
                log_type = 'other'
        elif '/system/' in path or '/settings/' in path:
            log_type = 'system_config'
        elif '/permissions/' in path or '/roles/' in path:
            log_type = 'permission_change'
        else:
            log_type = 'other'
        
        return log_type, level
    
    def _get_module(self, path):
        """从路径获取模块名称"""
        if '/users/' in path:
            return '用户管理'
        elif '/videos/' in path:
            return '视频管理'
        elif '/comments/' in path:
            return '评论管理'
        elif '/reports/' in path:
            return '举报管理'
        elif '/admins/' in path:
            return '管理员管理'
        elif '/system/' in path:
            return '系统设置'
        elif '/permissions/' in path:
            return '权限管理'
        else:
            return '其他'
    
    def _get_action_description(self, request, response):
        """获取操作和描述"""
        method = request.method
        path = request.path
        status_code = response.status_code
        
        # 基本操作描述
        method_map = {
            'POST': '创建',
            'PUT': '更新',
            'PATCH': '更新',
            'DELETE': '删除',
        }
        
        action = f"{method_map.get(method, method)} {self._get_module(request.path)}"
        
        # 详细描述
        if status_code >= 200 and status_code < 300:
            description = f"成功{method_map.get(method, '操作')}"
        elif status_code >= 400 and status_code < 500:
            description = f"操作失败 (客户端错误: {status_code})"
        elif status_code >= 500:
            description = f"操作失败 (服务器错误: {status_code})"
        else:
            description = f"操作完成 (状态码: {status_code})"
        
        return action, description
