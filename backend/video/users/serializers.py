from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Subscription, VerificationCode, UserNotification, NotificationSetting

User = get_user_model()




class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    subscribers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'last_name', 'email', 'avatar', 'bio', 'website',
                  'gender', 'birthday', 'is_verified', 'date_joined', 'subscribers_count', 'following_count')
        read_only_fields = ('id', 'date_joined', 'is_verified')

    def get_subscribers_count(self, obj):
        return obj.subscribers.count()

    def get_following_count(self, obj):
        return obj.subscriptions.count()
    
    def get_avatar(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


class UserDetailSerializer(UserSerializer):
    """详细用户信息序列化器"""
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('phone', 'gender', 'birthday', 'enable_notifications', 'created_at', 'updated_at', 'role', 'is_vip')


class UserCreateSerializer(serializers.ModelSerializer):
    """用户创建序列化器"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'last_name', 'email', 'password', 'password2', 'avatar', 'bio', 'phone', 'gender', 'birthday')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "两次密码不一致"})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """用户更新序列化器 - 所有字段都是可选的"""
    avatar = serializers.ImageField(required=False, allow_null=True)
    last_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    bio = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    website = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    gender = serializers.ChoiceField(choices=[('male', '男'), ('female', '女'), ('other', '保密')], required=False, allow_null=True)
    birthday = serializers.DateField(required=False, allow_null=True)
    enable_notifications = serializers.BooleanField(required=False)
    
    class Meta:
        model = User
        fields = ('avatar', 'last_name', 'bio', 'website', 'phone', 'gender', 'birthday', 'enable_notifications')
    
    def update(self, instance, validated_data):
        print("更新用户数据:", validated_data)
        
        # 只更新提供的字段
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        print("用户保存后:", instance.last_name, instance.bio, instance.website, instance.gender, instance.birthday)
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """修改密码序列化器"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "两次密码不一致"})
        return attrs


class SubscriptionSerializer(serializers.ModelSerializer):
    """订阅序列化器"""
    subscriber = UserSerializer(read_only=True)
    target = UserSerializer(read_only=True)
    
    class Meta:
        model = Subscription
        fields = ('id', 'subscriber', 'target', 'created_at')
        read_only_fields = ('id', 'created_at')


class SendVerificationCodeSerializer(serializers.Serializer):
    """发送验证码序列化器"""
    code_type = serializers.ChoiceField(choices=VerificationCode.CODE_TYPES)
    email = serializers.EmailField(required=False)  # 仅在修改邮箱时需要


class VerifyEmailSerializer(serializers.Serializer):
    """邮箱验证序列化器"""
    code = serializers.CharField(required=True, min_length=6, max_length=6)


class ChangePasswordWithCodeSerializer(serializers.Serializer):
    """使用验证码修改密码序列化器"""
    code = serializers.CharField(required=True, min_length=6, max_length=6)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "两次密码不一致"})
        return attrs


class ChangeEmailWithCodeSerializer(serializers.Serializer):
    """使用验证码修改邮箱序列化器"""
    code = serializers.CharField(required=True, min_length=6, max_length=6)
    email = serializers.EmailField(required=True) 


class UserNotificationSerializer(serializers.ModelSerializer):
    """用户消息通知序列化器"""
    sender_info = serializers.SerializerMethodField()
    
    class Meta:
        model = UserNotification
        fields = ('id', 'title', 'content', 'type', 'read', 'created_at', 
                  'sender_info', 'source_id', 'source_type')
        read_only_fields = ('id', 'created_at')
    
    def get_sender_info(self, obj):
        if obj.sender:
            return {
                'id': obj.sender.id,
                'username': obj.sender.username,
                'avatar': self.context['request'].build_absolute_uri(obj.sender.avatar.url) if obj.sender.avatar else None
            }
        return None


class NotificationSettingSerializer(serializers.ModelSerializer):
    """用户通知设置序列化器"""
    class Meta:
        model = NotificationSetting
        fields = ('id', 'system', 'interaction', 'private', 'email')
        read_only_fields = ('id',)


class UserManagementSerializer(serializers.ModelSerializer):
    """用户管理序列化器 - 管理员专用"""
    avatar = serializers.SerializerMethodField()
    vip_status = serializers.SerializerMethodField()
    role_display = serializers.SerializerMethodField()
    vip_level_display = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'last_name', 'email', 'avatar', 'role', 'role_display',
                 'is_vip', 'vip_status', 'vip_level', 'vip_level_display', 'vip_expire_time',
                 'is_verified', 'is_active', 'created_at', 'last_login')

    def get_avatar(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
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

    def get_vip_level_display(self, obj):
        return obj.get_vip_level_display() 