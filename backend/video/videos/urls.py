from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, 
    TagViewSet, 
    VideoViewSet, 
    CommentViewSet,
    ChunkUploadView,
    CheckFileView,
    MergeChunksView,
    VideoViewViewSet,
    VideoCollectionViewSet,
    DanmakuViewSet
)
from .subtitle_views import translate_subtitles, optimize_subtitles

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'tags', TagViewSet)
router.register(r'videos', VideoViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'views', VideoViewViewSet, basename='videoview')
router.register(r'collections', VideoCollectionViewSet, basename='videocollection')
router.register(r'danmaku', DanmakuViewSet, basename='danmaku')

urlpatterns = [
    path('', include(router.urls)),
    
    # 分片上传相关路径
    path('upload/check/', CheckFileView.as_view(), name='check-file'),
    path('upload/chunk/', ChunkUploadView.as_view(), name='upload-chunk'),
    path('upload/merge/', MergeChunksView.as_view(), name='merge-chunks'),
    
    # 字幕相关路径
    path('videos/<int:video_id>/subtitles/translate/', translate_subtitles, name='translate-subtitles'),
    path('videos/<int:video_id>/subtitles/optimize/', optimize_subtitles, name='optimize-subtitles'),
] 