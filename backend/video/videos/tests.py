from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import Mock, patch, MagicMock
from rest_framework.test import APIClient
from .models import Video
import os

User = get_user_model()


# 注意：字幕检测相关的测试已移至 ai_service/tests.py
# 避免跨app调用，保持各app职责独立


class TriggerTranscodeAPITest(TestCase):
    """转码触发API测试"""
    
    def setUp(self):
        """设置测试数据"""
        # 使用 APIClient 而不是默认的 Client
        self.client = APIClient()
        
        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # 创建另一个用户（用于测试权限）
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        # 创建测试视频（pending_subtitle_edit 状态）
        self.video = Video.objects.create(
            title='测试视频',
            description='测试描述',
            user=self.user,
            video_file='test_video.mp4',
            status='pending_subtitle_edit'
        )
    
    @patch('videos.views.process_video')
    def test_trigger_transcode_success(self, mock_process_video):
        """测试：成功触发转码"""
        # 使用 force_authenticate 进行认证
        self.client.force_authenticate(user=self.user)
        
        # 调用API
        response = self.client.post(f'/api/videos/{self.video.id}/trigger-transcode/')
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], '转码已启动')
        self.assertEqual(response.json()['video_id'], self.video.id)
        self.assertEqual(response.json()['status'], 'transcoding')
        
        # 验证视频状态已更新
        self.video.refresh_from_db()
        self.assertEqual(self.video.status, 'transcoding')
        
        # 验证转码任务被触发
        mock_process_video.delay.assert_called_once_with(self.video.id)
    
    def test_trigger_transcode_wrong_status(self):
        """测试：视频状态不正确时返回错误"""
        # 修改视频状态为 processing
        self.video.status = 'processing'
        self.video.save()
        
        # 使用 force_authenticate 进行认证
        self.client.force_authenticate(user=self.user)
        
        # 调用API
        response = self.client.post(f'/api/videos/{self.video.id}/trigger-transcode/')
        
        # 验证响应
        self.assertEqual(response.status_code, 400)
        self.assertIn('无法触发转码', response.json()['error'])
    
    def test_trigger_transcode_no_permission(self):
        """测试：非视频所有者无权触发转码"""
        # 使用 force_authenticate 认证为其他用户
        self.client.force_authenticate(user=self.other_user)
        
        # 调用API
        response = self.client.post(f'/api/videos/{self.video.id}/trigger-transcode/')
        
        # 验证响应
        self.assertEqual(response.status_code, 404)
        self.assertIn('视频不存在或无权限', response.json()['error'])
    
    def test_trigger_transcode_not_authenticated(self):
        """测试：未登录用户无法触发转码"""
        # 不进行认证，直接调用API
        response = self.client.post(f'/api/videos/{self.video.id}/trigger-transcode/')
        
        # 验证响应（应该返回401或403）
        self.assertIn(response.status_code, [401, 403])
    
    def test_trigger_transcode_video_not_found(self):
        """测试：视频不存在时返回404"""
        # 使用 force_authenticate 进行认证
        self.client.force_authenticate(user=self.user)
        
        # 调用API（使用不存在的视频ID）
        response = self.client.post('/api/videos/99999/trigger-transcode/')
        
        # 验证响应
        self.assertEqual(response.status_code, 404)
        self.assertIn('视频不存在或无权限', response.json()['error'])
