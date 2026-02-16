from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.db.models import Q

from core.permissions import IsSuperAdmin

User = get_user_model()


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """权限视图集"""
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    queryset = Permission.objects.all()
    
    def list(self, request):
        """获取所有权限列表"""
        permissions = Permission.objects.select_related('content_type').all()
        
        # 按应用分组
        grouped_permissions = {}
        for perm in permissions:
            app_label = perm.content_type.app_label
            if app_label not in grouped_permissions:
                grouped_permissions[app_label] = []
            
            grouped_permissions[app_label].append({
                'id': perm.id,
                'name': perm.name,
                'codename': perm.codename,
                'content_type': {
                    'id': perm.content_type.id,
                    'app_label': perm.content_type.app_label,
                    'model': perm.content_type.model
                }
            })
        
        return Response({
            'permissions': grouped_permissions,
            'total': permissions.count()
        })
    
    @action(detail=False, methods=['get'])
    def by_app(self, request):
        """按应用获取权限"""
        app_label = request.query_params.get('app')
        if not app_label:
            return Response({
                'error': '请指定应用名称'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        permissions = Permission.objects.filter(
            content_type__app_label=app_label
        ).select_related('content_type')
        
        result = []
        for perm in permissions:
            result.append({
                'id': perm.id,
                'name': perm.name,
                'codename': perm.codename,
                'content_type': perm.content_type.model
            })
        
        return Response({'permissions': result})


class RoleViewSet(viewsets.ModelViewSet):
    """角色（用户组）视图集"""
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    queryset = Group.objects.all()
    
    def list(self, request):
        """获取所有角色"""
        roles = Group.objects.prefetch_related('permissions').all()
        
        result = []
        for role in roles:
            result.append({
                'id': role.id,
                'name': role.name,
                'permissions': [
                    {
                        'id': perm.id,
                        'name': perm.name,
                        'codename': perm.codename
                    }
                    for perm in role.permissions.all()
                ],
                'user_count': role.user_set.count()
            })
        
        return Response({
            'roles': result,
            'total': roles.count()
        })
    
    def create(self, request):
        """创建角色"""
        name = request.data.get('name')
        permission_ids = request.data.get('permissions', [])
        
        if not name:
            return Response({
                'error': '角色名称不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if Group.objects.filter(name=name).exists():
            return Response({
                'error': '角色名称已存在'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        role = Group.objects.create(name=name)
        
        if permission_ids:
            permissions = Permission.objects.filter(id__in=permission_ids)
            role.permissions.set(permissions)
        
        return Response({
            'message': '角色创建成功',
            'role': {
                'id': role.id,
                'name': role.name,
                'permissions': [p.id for p in role.permissions.all()]
            }
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request, pk=None):
        """更新角色"""
        try:
            role = Group.objects.get(pk=pk)
        except Group.DoesNotExist:
            return Response({
                'error': '角色不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        name = request.data.get('name')
        permission_ids = request.data.get('permissions')
        
        if name:
            if Group.objects.filter(name=name).exclude(id=role.id).exists():
                return Response({
                    'error': '角色名称已存在'
                }, status=status.HTTP_400_BAD_REQUEST)
            role.name = name
            role.save()
        
        if permission_ids is not None:
            permissions = Permission.objects.filter(id__in=permission_ids)
            role.permissions.set(permissions)
        
        return Response({
            'message': '角色更新成功',
            'role': {
                'id': role.id,
                'name': role.name,
                'permissions': [p.id for p in role.permissions.all()]
            }
        })
    
    def destroy(self, request, pk=None):
        """删除角色"""
        try:
            role = Group.objects.get(pk=pk)
        except Group.DoesNotExist:
            return Response({
                'error': '角色不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 检查是否有用户使用此角色
        if role.user_set.exists():
            return Response({
                'error': f'该角色下还有 {role.user_set.count()} 个用户，无法删除'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        role.delete()
        return Response({
            'message': '角色删除成功'
        })
    
    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """获取角色下的用户"""
        try:
            role = Group.objects.get(pk=pk)
        except Group.DoesNotExist:
            return Response({
                'error': '角色不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        users = role.user_set.all()
        result = []
        for user in users:
            result.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active
            })
        
        return Response({
            'users': result,
            'total': users.count()
        })


class UserPermissionViewSet(viewsets.ViewSet):
    """用户权限管理视图集"""
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    @action(detail=False, methods=['get'])
    def user_permissions(self, request):
        """获取用户的所有权限"""
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({
                'error': '请指定用户 ID'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'error': '用户不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 获取用户的所有权限（包括组权限）
        all_permissions = user.get_all_permissions()
        
        # 获取用户直接拥有的权限
        user_permissions = user.user_permissions.select_related('content_type').all()
        
        # 获取用户所属的组
        user_groups = user.groups.prefetch_related('permissions').all()
        
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            },
            'all_permissions': list(all_permissions),
            'direct_permissions': [
                {
                    'id': perm.id,
                    'name': perm.name,
                    'codename': perm.codename
                }
                for perm in user_permissions
            ],
            'groups': [
                {
                    'id': group.id,
                    'name': group.name,
                    'permissions': [
                        {
                            'id': perm.id,
                            'name': perm.name,
                            'codename': perm.codename
                        }
                        for perm in group.permissions.all()
                    ]
                }
                for group in user_groups
            ]
        })
    
    @action(detail=False, methods=['post'])
    def assign_permissions(self, request):
        """为用户分配权限"""
        user_id = request.data.get('user_id')
        permission_ids = request.data.get('permissions', [])
        
        if not user_id:
            return Response({
                'error': '请指定用户 ID'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'error': '用户不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        permissions = Permission.objects.filter(id__in=permission_ids)
        user.user_permissions.set(permissions)
        
        return Response({
            'message': '权限分配成功',
            'user_id': user.id,
            'permissions': [p.id for p in permissions]
        })
    
    @action(detail=False, methods=['post'])
    def assign_groups(self, request):
        """为用户分配角色组"""
        user_id = request.data.get('user_id')
        group_ids = request.data.get('groups', [])
        
        if not user_id:
            return Response({
                'error': '请指定用户 ID'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'error': '用户不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        groups = Group.objects.filter(id__in=group_ids)
        user.groups.set(groups)
        
        return Response({
            'message': '角色分配成功',
            'user_id': user.id,
            'groups': [g.id for g in groups]
        })
