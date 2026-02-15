from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    自定义权限类：只允许对象的创建者修改它
    """
    
    def has_object_permission(self, request, view, obj):
        # 读取权限允许任何请求
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # 写入权限只允许对象的所有者
        return obj.user == request.user


class IsAdminUserOrReadOnly(permissions.BasePermission):
    """
    自定义权限类：只允许管理员修改，其他用户只能查看
    """
    
    def has_permission(self, request, view):
        # 读取权限允许任何请求
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # 写入权限只允许管理员
        return request.user and request.user.is_staff


class IsSuperAdmin(permissions.BasePermission):
    """
    自定义权限类：只允许超级管理员访问
    """
    
    def has_permission(self, request, view):
        import logging
        logger = logging.getLogger(__name__)
        
        if not request.user:
            logger.warning("IsSuperAdmin: No user in request")
            return False
            
        if not request.user.is_authenticated:
            logger.warning(f"IsSuperAdmin: User {request.user} is not authenticated")
            return False
        
        user_role = getattr(request.user, 'role', None)
        logger.info(f"IsSuperAdmin: User {request.user.username}, role={user_role}, is_superuser={request.user.is_superuser}")
        
        # 检查是否为超级管理员或 Django 超级用户
        is_super = user_role == 'superadmin' or request.user.is_superuser
        
        if not is_super:
            logger.warning(f"IsSuperAdmin: User {request.user.username} is not superadmin (role={user_role})")
        
        return is_super 