from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db.models import Q

from core.permissions import IsSuperAdmin
from users.serializers import AdminManagementSerializer

User = get_user_model()


class AdminManagementViewSet(viewsets.ModelViewSet):
    """管理员管理视图集"""
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = AdminManagementSerializer
    
    def get_queryset(self):
        """获取管理员列表"""
        queryset = User.objects.filter(
            Q(role='admin') | Q(role='superadmin')
        ).order_by('-date_joined')
        
        # 搜索
        search = self.request.query_params.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) | 
                Q(email__icontains=search)
            )
        
        # 角色筛选
        role = self.request.query_params.get('role', '')
        if role:
            queryset = queryset.filter(role=role)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """创建管理员"""
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        role = request.data.get('role', 'admin')
        is_active = request.data.get('is_active', True)
        
        # 验证
        if not username or not email or not password:
            return Response(
                {'detail': '用户名、邮箱和密码不能为空'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 检查用户名是否存在
        if User.objects.filter(username=username).exists():
            return Response(
                {'detail': '用户名已存在'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 检查邮箱是否存在
        if User.objects.filter(email=email).exists():
            return Response(
                {'detail': '邮箱已存在'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 只有超级管理员可以创建超级管理员
        if role == 'superadmin' and request.user.role != 'superadmin':
            return Response(
                {'detail': '无权创建超级管理员'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 创建用户
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            is_active=is_active
        )
        
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """更新管理员信息"""
        instance = self.get_object()
        
        # 不能修改超级管理员（除非自己是超级管理员）
        if instance.role == 'superadmin' and request.user.role != 'superadmin':
            return Response(
                {'detail': '无权修改超级管理员'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 更新字段
        email = request.data.get('email')
        role = request.data.get('role')
        is_active = request.data.get('is_active')
        
        if email:
            # 检查邮箱是否被其他用户使用
            if User.objects.filter(email=email).exclude(id=instance.id).exists():
                return Response(
                    {'detail': '邮箱已被使用'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            instance.email = email
        
        if role:
            # 只有超级管理员可以设置超级管理员角色
            if role == 'superadmin' and request.user.role != 'superadmin':
                return Response(
                    {'detail': '无权设置超级管理员角色'},
                    status=status.HTTP_403_FORBIDDEN
                )
            instance.role = role
        
        if is_active is not None:
            instance.is_active = is_active
        
        instance.save()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """删除管理员"""
        instance = self.get_object()
        
        # 不能删除超级管理员
        if instance.role == 'superadmin':
            return Response(
                {'detail': '不能删除超级管理员'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 不能删除自己
        if instance.id == request.user.id:
            return Response(
                {'detail': '不能删除自己'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """切换管理员状态"""
        instance = self.get_object()
        
        # 不能禁用超级管理员
        if instance.role == 'superadmin':
            return Response(
                {'detail': '不能禁用超级管理员'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 不能禁用自己
        if instance.id == request.user.id:
            return Response(
                {'detail': '不能禁用自己'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        instance.is_active = not instance.is_active
        instance.save()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
