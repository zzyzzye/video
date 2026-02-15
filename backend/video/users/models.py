from django.db import models
from django.contrib.auth.models import AbstractUser, Permission
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import random
import string

from .models_monitoring import SystemMonitoringLog


class UserRole(models.Model):
    """用户角色模型"""
    ROLE_CHOICES = [
        ('user', _('普通用户')),
        ('vip', _('VIP用户')),
        ('admin', _('管理员')),
        ('superadmin', _('超级管理员')),
    ]
    
    name = models.CharField(_('角色名称'), max_length=20, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(_('角色描述'), blank=True)
    permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('权限'),
        blank=True,
    )
    
    class Meta:
        verbose_name = _('用户角色')
        verbose_name_plural = _('用户角色')
    
    def __str__(self):
        return self.get_name_display()


class User(AbstractUser):
    """自定义用户模型"""
    avatar = models.ImageField(_('头像'), upload_to='avatars/', null=True, blank=True)
    phone = models.CharField(_('手机号'), max_length=20, unique=True, null=True, blank=True)
    bio = models.TextField(_('个人简介'), max_length=500, blank=True)
    
    # 使用last_name作为nickname
    # 添加性别字段
    GENDER_CHOICES = [
        ('male', _('男')),
        ('female', _('女')),
        ('other', _('保密')),
    ]
    gender = models.CharField(_('性别'), max_length=10, choices=GENDER_CHOICES, default='other')
    
    # 添加生日字段
    birthday = models.DateField(_('生日'), null=True, blank=True)
    
    # 社交媒体链接
    website = models.URLField(_('个人网站'), max_length=200, blank=True)
    
    # 用户状态
    is_verified = models.BooleanField(_('邮箱已验证'), default=False)
    
    # 用户角色
    role = models.CharField(
        _('用户角色'), 
        max_length=20, 
        choices=UserRole.ROLE_CHOICES,
        default='user'
    )
    
    # VIP 相关字段
    is_vip = models.BooleanField(_('是否VIP用户'), default=False)
    vip_expire_time = models.DateTimeField(_('VIP到期时间'), null=True, blank=True)
    vip_level = models.IntegerField(_('VIP等级'), default=0, choices=[
        (0, _('非VIP')),
        (1, _('青铜VIP')),
        (2, _('白银VIP')),
        (3, _('黄金VIP')),
    ])
    
    # 用户设置
    enable_notifications = models.BooleanField(_('启用通知'), default=True)
    
    # 追踪字段
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('用户')
        verbose_name_plural = _('用户')
        permissions = [
            ("can_upload_video", "可以上传视频"),
            ("can_review_video", "可以审核视频"),
            ("can_manage_users", "可以管理用户"),
            ("can_access_vip_content", "可以访问VIP内容"),
        ]
    
    def __str__(self):
        return self.username
    
    def save(self, *args, **kwargs):
        """重写保存方法，确保角色与VIP状态一致"""
        # 如果用户是VIP，确保角色至少为VIP
        if self.is_vip and self.is_vip_active and self.role == 'user':
            self.role = 'vip'
        
        # 如果用户不再是VIP，但角色是VIP，则降级为普通用户
        if (not self.is_vip or not self.is_vip_active) and self.role == 'vip':
            self.role = 'user'
        
        # 如果是超级用户，确保角色为超级管理员
        if self.is_superuser and self.role != 'superadmin':
            self.role = 'superadmin'
        
        super().save(*args, **kwargs)
    
    @property
    def is_vip_active(self):
        """检查VIP是否有效"""
        if not self.is_vip:
            return False
        if not self.vip_expire_time:
            return False
        return self.vip_expire_time > timezone.now()
    
    @property
    def is_admin(self):
        """检查是否为管理员"""
        return self.role in ['admin', 'superadmin'] or self.is_staff
    
    @property
    def role_display(self):
        """获取角色显示名称"""
        return dict(UserRole.ROLE_CHOICES).get(self.role, '普通用户')
    
    def set_vip(self, level, months=1):
        """设置用户为VIP"""
        self.is_vip = True
        self.vip_level = level
        
        # 如果已经是VIP，则在当前到期时间基础上延长
        if self.vip_expire_time and self.vip_expire_time > timezone.now():
            self.vip_expire_time = self.vip_expire_time + timezone.timedelta(days=30*months)
        else:
            # 否则从当前时间开始计算
            self.vip_expire_time = timezone.now() + timezone.timedelta(days=30*months)
        
        # 更新角色
        if self.role == 'user':
            self.role = 'vip'
        
        self.save()
    
    def cancel_vip(self):
        """取消VIP"""
        self.is_vip = False
        self.vip_level = 0
        self.vip_expire_time = None
        
        # 如果是VIP角色，降级为普通用户
        if self.role == 'vip':
            self.role = 'user'
        
        self.save()
    
    def set_role(self, role):
        """设置用户角色"""
        if role not in dict(UserRole.ROLE_CHOICES):
            raise ValueError(f"无效的角色: {role}")
        
        # 如果设置为VIP角色，确保VIP状态一致
        if role == 'vip' and not self.is_vip:
            self.set_vip(1)  # 默认设为青铜VIP
        
        # 如果设置为管理员角色，确保staff状态一致
        if role in ['admin', 'superadmin'] and not self.is_staff:
            self.is_staff = True
        
        # 如果设置为超级管理员，确保superuser状态一致
        if role == 'superadmin' and not self.is_superuser:
            self.is_superuser = True
        
        self.role = role
        self.save()
    
    def can_review_videos(self):
        """检查用户是否可以审核视频"""
        return self.role in ['admin', 'superadmin'] or self.has_perm('users.can_review_video')


class Subscription(models.Model):
    """用户订阅模型"""
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    target = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscribers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('subscriber', 'target')
        verbose_name = _('订阅')
        verbose_name_plural = _('订阅')
    
    def __str__(self):
        return f"{self.subscriber.username} -> {self.target.username}"


class VerificationCode(models.Model):
    """验证码模型"""
    CODE_TYPES = [
        ('email_verify', _('邮箱验证')),
        ('password_reset', _('密码重置')),
        ('email_change', _('修改邮箱')),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_codes')
    code = models.CharField(_('验证码'), max_length=6)
    code_type = models.CharField(_('验证码类型'), max_length=20, choices=CODE_TYPES)
    email = models.EmailField(_('邮箱'), blank=True, null=True)  # 用于修改邮箱时存储新邮箱
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    expires_at = models.DateTimeField(_('过期时间'))
    is_used = models.BooleanField(_('是否已使用'), default=False)
    
    class Meta:
        verbose_name = _('验证码')
        verbose_name_plural = _('验证码')
        
    def __str__(self):
        return f"{self.user.username} - {self.code_type} - {self.code}"
    
    @classmethod
    def generate_code(cls, user, code_type, email=None, expiry_minutes=30):
        """生成新的验证码"""
        # 生成6位随机数字验证码
        code = ''.join(random.choices(string.digits, k=6))
        
        # 设置过期时间
        expires_at = timezone.now() + timezone.timedelta(minutes=expiry_minutes)
        
        # 创建验证码记录
        verification_code = cls.objects.create(
            user=user,
            code=code,
            code_type=code_type,
            email=email,
            expires_at=expires_at
        )
        
        return verification_code
    
    def is_valid(self):
        """检查验证码是否有效"""
        return not self.is_used and self.expires_at > timezone.now()
    
    def use(self):
        """标记验证码为已使用"""
        self.is_used = True
        self.save()


class VIPOrder(models.Model):
    """VIP订单记录"""
    ORDER_STATUS = (
        ('pending', _('待支付')),
        ('paid', _('已支付')),
        ('cancelled', _('已取消')),
        ('refunded', _('已退款')),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vip_orders')
    order_id = models.CharField(_('订单号'), max_length=64, unique=True)
    vip_level = models.IntegerField(_('VIP等级'), choices=User.vip_level.field.choices)
    months = models.IntegerField(_('购买月数'), default=1)
    amount = models.DecimalField(_('支付金额'), max_digits=10, decimal_places=2)
    status = models.CharField(_('订单状态'), max_length=20, choices=ORDER_STATUS, default='pending')
    payment_method = models.CharField(_('支付方式'), max_length=20, blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    paid_at = models.DateTimeField(_('支付时间'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('VIP订单')
        verbose_name_plural = _('VIP订单')
    
    def __str__(self):
        return f"{self.user.username} - {self.order_id}"
    
    def complete_payment(self):
        """完成支付"""
        self.status = 'paid'
        self.paid_at = timezone.now()
        self.save()
        
        # 更新用户VIP状态
        self.user.set_vip(self.vip_level, self.months)


class UserNotification(models.Model):
    """用户消息通知模型"""
    NOTIFICATION_TYPES = [
        ('system', _('系统通知')),
        ('interaction', _('互动消息')),
        ('private', _('私信')),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='sent_notifications')
    type = models.CharField(_('通知类型'), max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(_('通知标题'), max_length=200)
    content = models.TextField(_('通知内容'))
    read = models.BooleanField(_('是否已读'), default=False)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    
    # 相关资源信息，用于跳转
    source_id = models.IntegerField(_('资源ID'), null=True, blank=True)
    source_type = models.CharField(_('资源类型'), max_length=30, blank=True)
    
    class Meta:
        verbose_name = _('用户通知')
        verbose_name_plural = _('用户通知')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        """标记为已读"""
        self.read = True
        self.save(update_fields=['read'])


class NotificationSetting(models.Model):
    """用户通知设置模型"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_settings')
    system = models.BooleanField(_('系统通知'), default=True)
    interaction = models.BooleanField(_('互动通知'), default=True)
    private = models.BooleanField(_('私信通知'), default=True)
    email = models.BooleanField(_('邮件通知'), default=False)
    
    class Meta:
        verbose_name = _('通知设置')
        verbose_name_plural = _('通知设置')
    
    def __str__(self):
        return f"{self.user.username}的通知设置"
