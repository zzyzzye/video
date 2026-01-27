from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)


def send_notification_to_user(user_id, notification_data):
    """
    通过 WebSocket 向指定用户发送通知
    
    Args:
        user_id: 用户 ID
        notification_data: 通知数据字典，包含 id, title, content, source_type, source_id 等
    """
    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            logger.warning("Channel layer 未配置")
            return False
        
        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}",
            {
                "type": "notification",
                "data": notification_data
            }
        )
        logger.info(f"已向用户 {user_id} 发送 WebSocket 通知")
        return True
    except Exception as e:
        logger.error(f"发送 WebSocket 通知失败: {e}")
        return False


def send_video_status_update(user_id, video_data):
    """
    通过 WebSocket 向指定用户发送视频状态更新
    
    Args:
        user_id: 用户 ID
        video_data: 视频数据字典，包含 id, status, title 等
    """
    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            logger.warning("Channel layer 未配置")
            return False
        
        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}",
            {
                "type": "video_status_update",
                "data": video_data
            }
        )
        logger.info(f"已向用户 {user_id} 发送视频状态更新: {video_data.get('status')}")
        return True
    except Exception as e:
        logger.error(f"发送视频状态更新失败: {e}")
        return False


def update_unread_count(user_id, count):
    """
    更新用户的未读消息数量
    
    Args:
        user_id: 用户 ID
        count: 未读消息数量
    """
    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            logger.warning("Channel layer 未配置")
            return False
        
        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}",
            {
                "type": "unread_count_update",
                "count": count
            }
        )
        return True
    except Exception as e:
        logger.error(f"更新未读数量失败: {e}")
        return False
