from django.urls import path
from .admin_views import AdminVideoViewSet

urlpatterns = [
    # 待审核视频列表
    path('videos/pending/', AdminVideoViewSet.as_view({'get': 'get_pending_videos'}), name='admin-pending-videos'),
    
    # 已审核视频列表
    path('videos/reviewed/', AdminVideoViewSet.as_view({'get': 'get_reviewed_videos'}), name='admin-reviewed-videos'),
    
    # 审核通过视频
    path('videos/<int:video_id>/approve/', AdminVideoViewSet.as_view({'post': 'approve_video'}), name='admin-approve-video'),
    
    # 拒绝视频
    path('videos/<int:video_id>/reject/', AdminVideoViewSet.as_view({'post': 'reject_video'}), name='admin-reject-video'),
] 