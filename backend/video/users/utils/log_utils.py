"""
日志记录工具函数
用于在代码中手动记录重要操作
"""
from users.models_logs import SystemOperationLog


def log_operation(
    operator,
    log_type,
    action,
    description='',
    level='info',
    module='',
    target_type='',
    target_id=None,
    target_name='',
    request=None
):
    """
    记录操作日志
    
    Args:
        operator: 操作者用户对象
        log_type: 日志类型 (login, logout, user_create 等)
        action: 操作描述
        description: 详细描述
        level: 日志级别 (info, warning, error, critical)
        module: 模块名称
        target_type: 目标类型
        target_id: 目标 ID
        target_name: 目标名称
        request: Django request 对象 (可选)
    """
    try:
        log_data = {
            'operator': operator,
            'operator_username': operator.username if operator else 'System',
            'log_type': log_type,
            'level': level,
            'module': module,
            'action': action,
            'description': description,
            'target_type': target_type,
            'target_id': target_id,
            'target_name': target_name,
        }
        
        # 如果提供了 request 对象，添加请求信息
        if request:
            log_data.update({
                'operator_ip': get_client_ip(request),
                'request_method': request.method,
                'request_path': request.path,
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
            })
        
        SystemOperationLog.objects.create(**log_data)
    except Exception as e:
        # 日志记录失败不应影响业务逻辑
        print(f"记录操作日志失败: {e}")


def get_client_ip(request):
    """获取客户端 IP 地址"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_login(user, request, success=True):
    """记录登录日志"""
    log_operation(
        operator=user,
        log_type='login',
        action='用户登录',
        description='登录成功' if success else '登录失败',
        level='info' if success else 'warning',
        module='认证',
        request=request
    )


def log_logout(user, request):
    """记录登出日志"""
    log_operation(
        operator=user,
        log_type='logout',
        action='用户登出',
        description='用户主动登出',
        level='info',
        module='认证',
        request=request
    )


def log_user_create(operator, target_user, request=None):
    """记录创建用户日志"""
    log_operation(
        operator=operator,
        log_type='user_create',
        action='创建用户',
        description=f'创建用户: {target_user.username}',
        level='info',
        module='用户管理',
        target_type='user',
        target_id=target_user.id,
        target_name=target_user.username,
        request=request
    )


def log_user_update(operator, target_user, request=None):
    """记录更新用户日志"""
    log_operation(
        operator=operator,
        log_type='user_update',
        action='更新用户',
        description=f'更新用户信息: {target_user.username}',
        level='info',
        module='用户管理',
        target_type='user',
        target_id=target_user.id,
        target_name=target_user.username,
        request=request
    )


def log_user_delete(operator, target_user, request=None):
    """记录删除用户日志"""
    log_operation(
        operator=operator,
        log_type='user_delete',
        action='删除用户',
        description=f'删除用户: {target_user.username}',
        level='warning',
        module='用户管理',
        target_type='user',
        target_id=target_user.id,
        target_name=target_user.username,
        request=request
    )


def log_video_review(operator, video, status, request=None):
    """记录视频审核日志"""
    status_map = {
        'approved': '通过',
        'rejected': '拒绝',
        'pending': '待审核'
    }
    log_operation(
        operator=operator,
        log_type='video_review',
        action='视频审核',
        description=f'审核视频 "{video.title}": {status_map.get(status, status)}',
        level='info',
        module='视频管理',
        target_type='video',
        target_id=video.id,
        target_name=video.title,
        request=request
    )


def log_video_delete(operator, video, request=None):
    """记录删除视频日志"""
    log_operation(
        operator=operator,
        log_type='video_delete',
        action='删除视频',
        description=f'删除视频: {video.title}',
        level='warning',
        module='视频管理',
        target_type='video',
        target_id=video.id,
        target_name=video.title,
        request=request
    )


def log_admin_create(operator, target_admin, request=None):
    """记录创建管理员日志"""
    log_operation(
        operator=operator,
        log_type='admin_create',
        action='创建管理员',
        description=f'创建管理员: {target_admin.username}',
        level='info',
        module='管理员管理',
        target_type='admin',
        target_id=target_admin.id,
        target_name=target_admin.username,
        request=request
    )


def log_admin_update(operator, target_admin, request=None):
    """记录更新管理员日志"""
    log_operation(
        operator=operator,
        log_type='admin_update',
        action='更新管理员',
        description=f'更新管理员信息: {target_admin.username}',
        level='info',
        module='管理员管理',
        target_type='admin',
        target_id=target_admin.id,
        target_name=target_admin.username,
        request=request
    )


def log_admin_delete(operator, target_admin, request=None):
    """记录删除管理员日志"""
    log_operation(
        operator=operator,
        log_type='admin_delete',
        action='删除管理员',
        description=f'删除管理员: {target_admin.username}',
        level='warning',
        module='管理员管理',
        target_type='admin',
        target_id=target_admin.id,
        target_name=target_admin.username,
        request=request
    )


def log_system_config(operator, config_name, request=None):
    """记录系统配置日志"""
    log_operation(
        operator=operator,
        log_type='system_config',
        action='系统配置',
        description=f'修改系统配置: {config_name}',
        level='info',
        module='系统设置',
        request=request
    )


def log_permission_change(operator, target_user, permission_name, request=None):
    """记录权限变更日志"""
    log_operation(
        operator=operator,
        log_type='permission_change',
        action='权限变更',
        description=f'修改用户 {target_user.username} 的权限: {permission_name}',
        level='info',
        module='权限管理',
        target_type='user',
        target_id=target_user.id,
        target_name=target_user.username,
        request=request
    )
