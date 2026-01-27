from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Subscription


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_verified', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_verified', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'phone')
    readonly_fields = ('date_joined', 'last_login', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('个人信息'), {'fields': ('email', 'phone', 'avatar', 'bio', 'website')}),
        (_('权限'), {
            'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('设置'), {'fields': ('enable_notifications',)}),
        (_('重要日期'), {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('subscriber', 'target', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('subscriber__username', 'target__username')
    ordering = ('-created_at',)
    raw_id_fields = ('subscriber', 'target')


admin.site.register(User, CustomUserAdmin)
