from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.dashboard_views import DashboardViewSet
from .views.notification_views import UserNotificationViewSet, NotificationSettingViewSet
from .views.comment_views import UserCommentViewSet
from .views.user_views import UserProfileView, UserViewSet
from .views.admin_user_views import UserManagementViewSet
from .views.statistics_views import StatisticsViewSet

# 创建一个主路由器
router = DefaultRouter()
# 先注册具体路径的视图集
router.register(r'notifications', UserNotificationViewSet, basename='notifications')
router.register(r'notification-settings', NotificationSettingViewSet, basename='notification-settings')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'comments', UserCommentViewSet, basename='comments')
router.register(r'admin-users', UserManagementViewSet, basename='admin-users')
router.register(r'statistics', StatisticsViewSet, basename='statistics')
# 最后注册空路径的视图集，避免拦截其他路由
router.register(r'', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('me/', UserProfileView.as_view(), name='user-profile'),
] 