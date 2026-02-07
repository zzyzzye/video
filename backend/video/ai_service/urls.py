"""
AI 服务路由
使用 ViewSet 路由器
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'ai_service'

# 创建路由器
router = DefaultRouter()

# 注册 ViewSet
router.register(r'moderation', views.ModerationViewSet, basename='moderation')
router.register(r'recognition', views.RecognitionViewSet, basename='recognition')
router.register(r'summary', views.SummaryViewSet, basename='summary')
router.register(r'subtitle', views.SubtitleViewSet, basename='subtitle')

urlpatterns = [
    # ViewSet 路由
    path('', include(router.urls)),
]
