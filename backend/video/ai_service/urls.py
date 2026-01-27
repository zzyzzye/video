from django.urls import path
from . import views

app_name = 'ai_service'

urlpatterns = [
    # AI 视频审核
    path('moderate/video/<int:video_id>/', views.moderate_video, name='moderate_video'),
    
    # AI 画面识别
    path('recognize/frame/', views.recognize_frame, name='recognize_frame'),
    
    # AI 视频摘要
    path('summarize/video/<int:video_id>/', views.summarize_video, name='summarize_video'),
    
    # 获取审核结果
    path('moderation/result/<int:video_id>/', views.get_moderation_result, name='moderation_result'),
]
