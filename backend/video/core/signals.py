from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from videos.models import Video, Comment, VideoLike


# 用于追踪视频状态变化
_video_previous_status = {}


@receiver(pre_save, sender=Video)
def video_pre_save(sender, instance, **kwargs):
    """
    视频保存前的信号处理
    - 记录之前的状态，用于检测状态变化
    """
    if instance.pk:
        try:
            old_instance = Video.objects.get(pk=instance.pk)
            _video_previous_status[instance.pk] = old_instance.status
        except Video.DoesNotExist:
            pass


@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    """
    视频保存后的信号处理
    - 检测审核状态变化并发送通知
    - 推送视频状态更新到前端（仅用户关心的状态）
    """
    if created:
        return
    
    # 获取之前的状态
    previous_status = _video_previous_status.pop(instance.pk, None)
    
    if previous_status and previous_status != instance.status:
        # 定义用户关心的状态（需要推送的状态）
        # 不包括中间状态：uploading, pending_subtitle_edit
        user_visible_statuses = [
            'processing',      # 处理中
            'pending',         # 待审核
            'approved',        # 已通过
            'rejected',        # 已拒绝
            'published',       # 已发布
            'failed',          # 失败
        ]
        
        # 只推送用户关心的状态变化
        if instance.status in user_visible_statuses:
            try:
                from core.websocket import send_video_status_update
                send_video_status_update(
                    user_id=instance.user.id,
                    video_data={
                        'id': instance.id,
                        'status': instance.status,
                        'title': instance.title,
                        'previous_status': previous_status,
                    }
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"推送视频状态更新失败: {e}")
        
        # 检查是否需要发送通知
        from users.models import UserNotification
        
        notification_data = None
        
        # 审核通过
        if instance.status == 'approved' and previous_status == 'pending':
            notification_data = {
                'title': '视频审核通过',
                'content': f'恭喜！您的视频《{instance.title}》已通过审核，现已发布。'
            }
        
        # 审核拒绝
        elif instance.status == 'rejected' and previous_status == 'pending':
            reason = instance.review_remark or '未提供具体原因'
            notification_data = {
                'title': '视频审核未通过',
                'content': f'很抱歉，您的视频《{instance.title}》未通过审核。原因：{reason}'
            }
        
        # 处理失败
        elif instance.status == 'failed' and previous_status in ['uploading', 'processing']:
            notification_data = {
                'title': '视频处理失败',
                'content': f'很抱歉，您的视频《{instance.title}》处理失败，请重新上传。'
            }
        
        # 处理完成，进入待审核
        elif instance.status == 'pending' and previous_status == 'processing':
            notification_data = {
                'title': '视频处理完成',
                'content': f'您的视频《{instance.title}》已处理完成，正在等待审核。'
            }
        
        # 发送通知
        if notification_data:
            try:
                notification = UserNotification.objects.create(
                    user=instance.user,
                    type='system',
                    title=notification_data['title'],
                    content=notification_data['content'],
                    source_id=instance.id,
                    source_type='video'
                )
                
                # WebSocket 实时推送
                try:
                    from core.websocket import send_notification_to_user
                    send_notification_to_user(
                        user_id=instance.user.id,
                        notification_data={
                            'id': notification.id,
                            'title': notification_data['title'],
                            'content': notification_data['content'],
                            'source_type': 'video',
                            'source_id': instance.id,
                            'created_at': notification.created_at.isoformat(),
                        }
                    )
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"WebSocket 推送失败: {e}")
                    
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"发送视频状态通知失败: {e}")


@receiver(post_delete, sender=VideoLike)
def video_like_post_delete(sender, instance, **kwargs):
    """
    视频点赞删除后的信号处理
    - 删除点赞时减少视频点赞数
    """
    # 这里视图中已经处理，这里是防止其他地方直接删除点赞记录
    video = instance.video
    if video.likes_count > 0:
        video.likes_count -= 1
        video.save(update_fields=['likes_count'])


@receiver(post_delete, sender=Comment)
def comment_post_delete(sender, instance, **kwargs):
    """
    评论删除后的信号处理
    - 删除评论时减少视频评论数
    """
    video = instance.video
    if video.comments_count > 0:
        video.comments_count -= 1
        video.save(update_fields=['comments_count']) 