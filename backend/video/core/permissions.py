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