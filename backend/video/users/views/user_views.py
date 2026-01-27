from rest_framework import viewsets, status, permissions, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from django.db import models
from ..models import Subscription, VerificationCode
from ..serializers import (
    UserSerializer,
    UserDetailSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    SubscriptionSerializer,
    SendVerificationCodeSerializer,
    VerifyEmailSerializer,
    ChangePasswordWithCodeSerializer,
    ChangeEmailWithCodeSerializer,
    UserManagementSerializer
)
from core.email import send_verification_email, send_test_email
from django.utils import timezone
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """用户视图集"""
    queryset = User.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return UserUpdateSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        elif self.action in ['update', 'partial_update', 'change_password', 'update_profile', 'upload_avatar']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """获取当前用户信息"""
        serializer = UserDetailSerializer(request.user, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'], url_path='update-profile')
    def update_profile(self, request):
        """更新个人资料"""
        user = request.user
        data = request.data.copy()
        
        print("接收到的原始数据:", data)
        
        serializer = UserUpdateSerializer(user, data=data, partial=True)
        
        if serializer.is_valid():
            print("数据验证成功，validated_data:", serializer.validated_data)
            user_updated = serializer.save()
            print("保存后的用户对象:", user_updated.last_name, user_updated.bio, user_updated.website)
            
            # 强制从数据库重新获取用户对象
            user.refresh_from_db()
            print("刷新后的用户对象:", user.last_name, user.bio, user.website)
            
            # 使用自定义序列化器返回数据
            return_serializer = UserDetailSerializer(user, context={'request': request})
            return Response(return_serializer.data)
        else:
            print("数据验证失败，错误:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='upload-avatar', parser_classes=[MultiPartParser, FormParser])
    def upload_avatar(self, request):
        """上传头像"""
        user = request.user
        
        if 'avatar' not in request.FILES:
            return Response({"detail": "没有提供头像文件"}, status=status.HTTP_400_BAD_REQUEST)
        
        avatar_file = request.FILES['avatar']
        # 检查文件类型
        if not avatar_file.content_type.startswith('image/'):
            return Response({"detail": "只能上传图片文件"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 检查文件大小 (2MB)
        if avatar_file.size > 2 * 1024 * 1024:
            return Response({"detail": "头像文件不能超过2MB"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 保存头像
        user.avatar = avatar_file
        user.save()
        
        # 返回完整的头像URL
        avatar_url = request.build_absolute_uri(user.avatar.url) if user.avatar else None
        
        return Response({
            "detail": "头像上传成功",
            "avatar_url": avatar_url
        })
    
    @action(detail=True, methods=['post'])
    def subscribe(self, request, pk=None):
        """订阅用户"""
        user = self.get_object()
        if user == request.user:
            return Response(
                {"detail": "不能订阅自己"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        subscription, created = Subscription.objects.get_or_create(
            subscriber=request.user,
            target=user
        )
        
        if created:
            return Response(
                {"detail": f"成功订阅 {user.username}"}, 
                status=status.HTTP_201_CREATED
            )
        return Response(
            {"detail": f"已经订阅过 {user.username}"}, 
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def unsubscribe(self, request, pk=None):
        """取消订阅用户"""
        user = self.get_object()
        try:
            subscription = Subscription.objects.get(
                subscriber=request.user,
                target=user
            )
            subscription.delete()
            return Response(
                {"detail": f"成功取消订阅 {user.username}"}, 
                status=status.HTTP_200_OK
            )
        except Subscription.DoesNotExist:
            return Response(
                {"detail": f"没有订阅 {user.username}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def my_subscriptions(self, request):
        """获取我的订阅列表"""
        subscriptions = Subscription.objects.filter(subscriber=request.user)
        serializer = SubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_subscribers(self, request):
        """获取我的订阅者列表"""
        subscribers = Subscription.objects.filter(target=request.user)
        serializer = SubscriptionSerializer(subscribers, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def subscription_status(self, request, pk=None):
        """检查对指定用户的订阅状态"""
        user = self.get_object()
        is_subscribed = Subscription.objects.filter(
            subscriber=request.user,
            target=user
        ).exists()

        return Response({
            'is_subscribed': is_subscribed
        })
    
    @action(detail=False, methods=['put'], url_path='change-password')
    def change_password(self, request):
        """修改密码"""
        user = request.user
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            # 检查旧密码
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {"old_password": ["旧密码不正确"]}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 设置新密码
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(
                {"detail": "密码修改成功"}, 
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='send-verification-code')
    def send_verification_code(self, request):
        """发送验证码"""
        user = request.user
        serializer = SendVerificationCodeSerializer(data=request.data)
        
        if serializer.is_valid():
            code_type = serializer.validated_data['code_type']
            email = serializer.validated_data.get('email')
            
            # 检查是否已经有未过期的验证码
            now = timezone.now()
            existing_codes = VerificationCode.objects.filter(
                user=user,
                code_type=code_type,
                expires_at__gt=now,
                is_used=False
            )
            
            # 如果是修改邮箱，还需要检查指定的新邮箱
            if code_type == 'email_change' and email:
                existing_codes = existing_codes.filter(email=email)
            
            # 生成新的验证码
            if code_type == 'email_change' and email:
                # 检查新邮箱是否已被使用
                if User.objects.filter(email=email).exists():
                    return Response(
                        {"email": ["该邮箱已被使用"]}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                verification_code = VerificationCode.generate_code(user, code_type, email)
                # 发送到新邮箱
                send_verification_email(user, verification_code.code, code_type)
                return Response({"detail": "验证码已发送到新邮箱"})
            else:
                verification_code = VerificationCode.generate_code(user, code_type)
                # 发送到当前邮箱
                send_verification_email(user, verification_code.code, code_type)
                return Response({"detail": "验证码已发送到您的邮箱"})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='verify-email')
    def verify_email(self, request):
        """验证邮箱"""
        user = request.user
        serializer = VerifyEmailSerializer(data=request.data)
        
        if serializer.is_valid():
            code = serializer.validated_data['code']
            
            # 查找有效的验证码
            try:
                verification_code = VerificationCode.objects.get(
                    user=user,
                    code=code,
                    code_type='email_verify',
                    expires_at__gt=timezone.now(),
                    is_used=False
                )
                
                # 标记验证码为已使用
                verification_code.use()
                
                # 更新用户的邮箱验证状态
                user.is_verified = True
                user.save()
                
                return Response({"detail": "邮箱验证成功"})
                
            except VerificationCode.DoesNotExist:
                return Response(
                    {"detail": "验证码无效或已过期"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='change-password-with-code')
    def change_password_with_code(self, request):
        """使用验证码修改密码"""
        user = request.user
        serializer = ChangePasswordWithCodeSerializer(data=request.data)
        
        if serializer.is_valid():
            code = serializer.validated_data['code']
            new_password = serializer.validated_data['new_password']
            
            # 查找有效的验证码
            try:
                verification_code = VerificationCode.objects.get(
                    user=user,
                    code=code,
                    code_type='password_reset',
                    expires_at__gt=timezone.now(),
                    is_used=False
                )
                
                # 标记验证码为已使用
                verification_code.use()
                
                # 更新用户密码
                user.set_password(new_password)
                user.save()
                
                return Response({"detail": "密码修改成功"})
                
            except VerificationCode.DoesNotExist:
                return Response(
                    {"detail": "验证码无效或已过期"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='change-email-with-code')
    def change_email_with_code(self, request):
        """使用验证码修改邮箱"""
        user = request.user
        serializer = ChangeEmailWithCodeSerializer(data=request.data)
        
        if serializer.is_valid():
            code = serializer.validated_data['code']
            new_email = serializer.validated_data['email']
            
            # 检查新邮箱是否已被使用
            if User.objects.filter(email=new_email).exists():
                return Response(
                    {"email": ["该邮箱已被使用"]}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 查找有效的验证码
            try:
                verification_code = VerificationCode.objects.get(
                    user=user,
                    code=code,
                    code_type='email_change',
                    email=new_email,
                    expires_at__gt=timezone.now(),
                    is_used=False
                )
                
                # 标记验证码为已使用
                verification_code.use()
                
                # 更新用户邮箱
                user.email = new_email
                user.is_verified = True  # 新邮箱自动验证
                user.save()
                
                return Response({"detail": "邮箱修改成功"})
                
            except VerificationCode.DoesNotExist:
                return Response(
                    {"detail": "验证码无效或已过期"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='test-email')
    def test_email(self, request):
        """测试邮件发送功能"""
        email = request.data.get('email')
        if not email:
            return Response({"detail": "请提供邮箱地址"}, status=status.HTTP_400_BAD_REQUEST)

        success = send_test_email(email)
        if success:
            return Response({"detail": "测试邮件已发送，请检查收件箱"})
        else:
            return Response({"detail": "测试邮件发送失败，请检查服务器日志"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='admin/management')
    def admin_management(self, request):
        """管理员用户管理接口 - 只返回普通用户和VIP用户"""
        if not request.user.is_admin:
            return Response(
                {"detail": "权限不足，只有管理员可以访问此接口"},
                status=status.HTTP_403_FORBIDDEN
            )

        # 只获取普通用户和VIP用户
        queryset = User.objects.filter(role__in=['user', 'vip']).order_by('-created_at')

        # 搜索功能
        search = request.query_params.get('search', '')
        if search:
            queryset = queryset.filter(
                models.Q(username__icontains=search) |
                models.Q(last_name__icontains=search) |
                models.Q(email__icontains=search)
            )

        # 角色筛选
        role = request.query_params.get('role', '')
        if role:
            queryset = queryset.filter(role=role)

        # VIP状态筛选
        is_vip = request.query_params.get('is_vip', '')
        if is_vip:
            if is_vip == 'true':
                queryset = queryset.filter(is_vip=True)
            elif is_vip == 'false':
                queryset = queryset.filter(is_vip=False)

        # 分页
        from django.core.paginator import Paginator
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 20)

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        # 序列化数据
        from rest_framework import serializers

        class UserManagementSerializer(serializers.ModelSerializer):
            avatar = serializers.SerializerMethodField()
            vip_status = serializers.SerializerMethodField()
            role_display = serializers.SerializerMethodField()

            class Meta:
                model = User
                fields = ('id', 'username', 'last_name', 'email', 'avatar', 'role', 'role_display',
                         'is_vip', 'vip_status', 'vip_level', 'vip_expire_time', 'is_verified',
                         'is_active', 'created_at', 'last_login')

            def get_avatar(self, obj):
                if obj.avatar:
                    return request.build_absolute_uri(obj.avatar.url)
                return None

            def get_vip_status(self, obj):
                if obj.is_vip_active:
                    return 'active'
                elif obj.is_vip:
                    return 'expired'
                else:
                    return 'none'

            def get_role_display(self, obj):
                return obj.role_display

        serializer = UserManagementSerializer(page_obj, many=True)

        return Response({
            'results': serializer.data,
            'total': paginator.count,
            'page': page_obj.number,
            'page_size': page_size,
            'total_pages': paginator.num_pages
        })

    @action(detail=True, methods=['post'], url_path='admin/set-vip')
    def admin_set_vip(self, request, pk=None):
        """管理员设置用户VIP状态"""
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

    @action(detail=True, methods=['post'], url_path='admin/cancel-vip')
    def admin_cancel_vip(self, request, pk=None):
        """管理员取消用户VIP状态"""
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

        if not user.is_vip:
            return Response(
                {"detail": "该用户当前不是VIP用户"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 取消VIP
        user.cancel_vip()

        return Response({
            "detail": f"已成功取消用户 {user.username} 的VIP状态"
        })

    @action(detail=True, methods=['post'], url_path='admin/toggle-status')
    def admin_toggle_status(self, request, pk=None):
        """管理员启用/禁用用户账号"""
        if not request.user.is_admin:
            return Response(
                {"detail": "权限不足，只有管理员可以操作"},
                status=status.HTTP_403_FORBIDDEN
            )

        user = self.get_object()

        # 检查目标用户是否为普通用户或VIP用户
        if user.role not in ['user', 'vip']:
            return Response(
                {"detail": "只能对普通用户和VIP用户进行状态操作"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 切换状态
        user.is_active = not user.is_active
        user.save()

        action = "启用" if user.is_active else "禁用"
        return Response({
            "detail": f"已成功{action}用户 {user.username} 的账号",
            "is_active": user.is_active
        })

    @action(detail=True, methods=['delete'], url_path='admin/delete')
    def admin_delete_user(self, request, pk=None):
        """管理员删除用户"""
        if not request.user.is_admin:
            return Response(
                {"detail": "权限不足，只有管理员可以操作"},
                status=status.HTTP_403_FORBIDDEN
            )

        user = self.get_object()

        # 检查目标用户是否为普通用户或VIP用户
        if user.role not in ['user', 'vip']:
            return Response(
                {"detail": "只能删除普通用户和VIP用户"},
                status=status.HTTP_400_BAD_REQUEST
            )

        username = user.username
        user.delete()

        return Response({
            "detail": f"已成功删除用户 {username}"
        }) 

class UserProfileSerializer(generics.RetrieveAPIView):
    """用户个人资料序列化器"""
    from rest_framework import serializers
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'nickname', 'avatar', 'bio', 'gender', 'birthday', 'website', 'role', 'is_vip')
        read_only_fields = ('id', 'username', 'email', 'role', 'is_vip')

class UserProfileView(APIView):
    """
    获取当前用户信息
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        from rest_framework import serializers
        
        class UserSerializer(serializers.ModelSerializer):
            avatar = serializers.SerializerMethodField()
            
            class Meta:
                model = User
                fields = ('id', 'username', 'email', 'last_name', 'avatar', 'bio', 
                          'gender', 'birthday', 'website', 'role', 'is_vip')
                
            def get_avatar(self, obj):
                if obj.avatar and hasattr(obj.avatar, 'url'):
                    return request.build_absolute_uri(obj.avatar.url)
                return None
        
        serializer = UserSerializer(user)
        return Response(serializer.data) 