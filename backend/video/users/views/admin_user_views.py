from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.utils import timezone
from ..serializers import UserManagementSerializer

User = get_user_model()


class UserManagementViewSet(viewsets.ReadOnlyModelViewSet):
    """用户管理视图集 - 只读操作"""
    serializer_class = UserManagementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """管理员只能查看普通用户和VIP用户"""
        if not self.request.user.is_admin:
            return User.objects.none()

        # 只返回普通用户和VIP用户，排除管理员和超级管理员
        return User.objects.filter(role__in=['user', 'vip']).order_by('-created_at')

    def list(self, request):
        """管理员获取用户列表"""
        if not request.user.is_admin:
            return Response(
                {"detail": "权限不足，只有管理员可以查看"},
                status=status.HTTP_403_FORBIDDEN
            )

        # 获取查询参数
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 10)
        search = request.query_params.get('search', '')
        role_filter = request.query_params.get('role', '')
        vip_status = request.query_params.get('vip_status', '')

        # 构建查询
        queryset = User.objects.filter(role__in=['user', 'vip'])

        # 搜索功能
        if search:
            queryset = queryset.filter(
                username__icontains=search
            ) | queryset.filter(
                last_name__icontains=search
            ) | queryset.filter(
                email__icontains=search
            )

        # 角色筛选
        if role_filter and role_filter in ['user', 'vip']:
            queryset = queryset.filter(role=role_filter)

        # VIP状态筛选
        if vip_status:
            if vip_status == 'active':
                queryset = queryset.filter(is_vip=True, vip_expire_time__gt=timezone.now())
            elif vip_status == 'expired':
                queryset = queryset.filter(is_vip=True, vip_expire_time__lte=timezone.now())
            elif vip_status == 'none':
                queryset = queryset.filter(is_vip=False)

        # 分页
        paginator = Paginator(queryset.order_by('-created_at'), page_size)

        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        # 序列化数据
        serializer = UserManagementSerializer(page_obj, many=True, context={'request': request})

        return Response({
            'results': serializer.data,
            'total': paginator.count,
            'page': page_obj.number,
            'page_size': int(page_size),
            'total_pages': paginator.num_pages
        })

    @action(detail=True, methods=['post'], url_path='set-vip')
    def set_vip(self, request, pk=None):
        """设置用户VIP状态"""
        if not request.user.is_admin:
            return Response(
                {"detail": "权限不足，只有管理员可以操作"},
                status=status.HTTP_403_FORBIDDEN
            )

        user = self.get_object()

        # 检查目标用户是否为普通用户或VIP用户
        if user.role not in ['user', 'vip']:
            return Response(
                {"detail": "只能对普通用户和VIP用户进行VIP操作"},
                status=status.HTTP_400_BAD_REQUEST
            )

        vip_level = request.data.get('vip_level', 1)
        months = request.data.get('months', 1)

        if vip_level not in [1, 2, 3]:
            return Response(
                {"detail": "VIP等级必须是1、2或3"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if months < 1 or months > 12:
            return Response(
                {"detail": "月份必须在1-12之间"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 设置VIP
        user.set_vip(vip_level, months)

        return Response({
            "detail": f"已成功设置用户 {user.username} 为 {user.get_vip_level_display()} VIP，有效期至 {user.vip_expire_time.strftime('%Y-%m-%d %H:%M:%S')}"
        })

    @action(detail=True, methods=['post'], url_path='cancel-vip')
    def cancel_vip(self, request, pk=None):
        """取消用户VIP状态"""
        if not request.user.is_admin:
            return Response(
                {"detail": "权限不足，只有管理员可以操作"},
                status=status.HTTP_403_FORBIDDEN
            )

        user = self.get_object()

        # 检查目标用户是否为VIP用户
        if not user.is_vip:
            return Response(
                {"detail": "该用户不是VIP用户"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 取消VIP
        user.cancel_vip()

        return Response({
            "detail": f"已成功取消用户 {user.username} 的VIP状态"
        })

    @action(detail=True, methods=['post'], url_path='toggle-active')
    def toggle_active(self, request, pk=None):
        """启用/禁用用户账户"""
        if not request.user.is_admin:
            return Response(
                {"detail": "权限不足，只有管理员可以操作"},
                status=status.HTTP_403_FORBIDDEN
            )

        user = self.get_object()

        # 切换激活状态
        user.is_active = not user.is_active
        user.save()

        action_text = "启用" if user.is_active else "禁用"
        return Response({
            "detail": f"已成功{action_text}用户 {user.username} 的账户"
        })

