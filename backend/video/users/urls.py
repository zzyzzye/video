from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.dashboard_views import DashboardViewSet
from .views.notification_views import UserNotificationViewSet, NotificationSettingViewSet
from .views.comment_views import UserCommentViewSet
from .views.user_views import UserProfileView, UserViewSet
from .views.admin_user_views import UserManagementViewSet
from .views.statistics_views import StatisticsViewSet
from .views.system_views import SystemSettingsViewSet
from .views.admin_management_views import AdminManagementViewSet
from .views.log_views import SystemOperationLogViewSet
from .views.database_views import DatabaseManagementViewSet
from .views.permission_views import PermissionViewSet, RoleViewSet, UserPermissionViewSet


router = DefaultRouter()

router.register(r'notifications', UserNotificationViewSet, basename='notifications')
router.register(r'notification-settings', NotificationSettingViewSet, basename='notification-settings')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'comments', UserCommentViewSet, basename='comments')
router.register(r'admin-users', UserManagementViewSet, basename='admin-users')
router.register(r'admins', AdminManagementViewSet, basename='admins')
router.register(r'statistics', StatisticsViewSet, basename='statistics')
router.register(r'system', SystemSettingsViewSet, basename='system')
router.register(r'logs', SystemOperationLogViewSet, basename='logs')
router.register(r'database', DatabaseManagementViewSet, basename='database')
router.register(r'permissions', PermissionViewSet, basename='permissions')
router.register(r'roles', RoleViewSet, basename='roles')
router.register(r'user-permissions', UserPermissionViewSet, basename='user-permissions')

router.register(r'', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('me/', UserProfileView.as_view(), name='user-profile'),
] 