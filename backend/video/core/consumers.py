import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import logging

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket Consumer 用于实时推送通知
    """
    
    async def connect(self):
        """建立 WebSocket 连接"""
        self.user = self.scope.get("user")
        
        if not self.user or not self.user.is_authenticated:
            logger.warning("WebSocket 连接被拒绝：用户未认证")
            await self.close()
            return
        
        # 用户专属的通知组
        self.group_name = f"user_{self.user.id}"
        
        # 加入用户组
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"用户 {self.user.id} 的 WebSocket 连接已建立")
        
        # 发送未读消息数量
        unread_count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': unread_count
        }))
    
    async def disconnect(self, close_code):
        """断开 WebSocket 连接"""
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(f"用户 {self.user.id} 的 WebSocket 连接已断开")
    
    async def receive(self, text_data):
        """接收客户端消息"""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'get_unread_count':
                unread_count = await self.get_unread_count()
                await self.send(text_data=json.dumps({
                    'type': 'unread_count',
                    'count': unread_count
                }))
        except json.JSONDecodeError:
            logger.error("无效的 JSON 数据")
    
    async def notification(self, event):
        """
        处理通知事件（从 channel layer 接收）
        这个方法名对应 group_send 中的 type
        """
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': event['data']
        }))
    
    async def unread_count_update(self, event):
        """
        更新未读消息数量
        """
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': event['count']
        }))
    
    async def video_status_update(self, event):
        """
        视频状态更新推送
        """
        await self.send(text_data=json.dumps({
            'type': 'video_status_update',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def get_unread_count(self):
        """获取未读消息数量"""
        from users.models import UserNotification
        return UserNotification.objects.filter(
            user=self.user,
            read=False
        ).count()
