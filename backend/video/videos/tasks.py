import os
import time
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
import logging
import hashlib

logger = logging.getLogger(__name__)


def send_video_notification(user, video, notification_type, title, content):
    """
    发送视频相关通知
    
    Args:
        user: 接收通知的用户
        video: 相关视频对象
        notification_type: 通知类型标识
        title: 通知标题
        content: 通知内容
    """
    from users.models import UserNotification
    
    # 创建站内通知
    notification = UserNotification.objects.create(
        user=user,
        type='system',
        title=title,
        content=content,
        source_id=video.id,
        source_type='video'
    )
    
    # WebSocket 实时推送
    try:
        from core.websocket import send_notification_to_user
        send_notification_to_user(
            user_id=user.id,
            notification_data={
                'id': notification.id,
                'title': title,
                'content': content,
                'source_type': 'video',
                'source_id': video.id,
                'created_at': notification.created_at.isoformat(),
            }
        )
    except Exception as e:
        logger.warning(f"WebSocket 推送失败: {e}")
    
    return notification


def get_video_lock_key(video_id):
    """生成视频处理锁的key"""
    return f"video_processing_lock:{video_id}"


def acquire_video_lock(video_id, timeout=3600):
    """
    获取视频处理锁（使用 Redis）
    timeout: 锁的超时时间（秒），默认1小时
    返回: True 如果获取成功，False 如果已被锁定
    """
    lock_key = get_video_lock_key(video_id)
    # 使用 Redis 的 SETNX 原子操作
    # add() 只在 key 不存在时设置，返回 True；如果 key 已存在，返回 False
    return cache.add(lock_key, "locked", timeout)


def release_video_lock(video_id):
    """释放视频处理锁"""
    lock_key = get_video_lock_key(video_id)
    cache.delete(lock_key)


def is_video_locked(video_id):
    """检查视频是否正在被处理"""
    lock_key = get_video_lock_key(video_id)
    return cache.get(lock_key) is not None


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_video(self, video_id):
    """
    处理视频文件，生成HLS格式、缩略图等
    
    防重复机制：
    1. Redis 分布式锁 - 防止多个 worker 同时处理同一视频
    2. 数据库状态检查 - 双重保险
    3. 幂等性设计 - 即使重复执行也不会产生问题
    """
    from .models import Video
    
    task_id = self.request.id or 'unknown'
    logger.info(f"{'='*60}")
    logger.info(f"[Task {task_id}] 收到视频处理任务: video_id={video_id}")
    logger.info(f"[Task {task_id}] 重试次数: {self.request.retries}/{self.max_retries}")
    logger.info(f"{'='*60}")
    
    # 第一层防护：Redis 分布式锁
    if not acquire_video_lock(video_id, timeout=7200):  # 2小时超时
        logger.warning(f"[Task {task_id}] 视频 {video_id} 正在被其他任务处理（Redis锁），跳过")
        return {"status": "skipped", "reason": "already_processing"}
    
    try:
        # 第二层防护：数据库状态检查 + 原子更新
        # 只处理 uploading 或 processing 状态的视频
        # processing 状态是为了处理之前失败需要重试的情况
        updated = Video.objects.filter(
            id=video_id,
            status__in=['uploading', 'processing']
        ).exclude(
            # 排除已经有 HLS 文件的视频（说明已处理完成）
            hls_file__isnull=False
        ).update(status='processing')
        
        if updated == 0:
            video = Video.objects.filter(id=video_id).first()
            if video:
                if video.hls_file:
                    logger.info(f"[Task {task_id}] 视频 {video_id} 已处理完成，HLS文件存在，跳过")
                else:
                    logger.warning(f"[Task {task_id}] 视频 {video_id} 状态为 {video.status}，不符合处理条件，跳过")
            else:
                logger.error(f"[Task {task_id}] 视频 {video_id} 不存在")
            return {"status": "skipped", "reason": "invalid_state"}
        
        # 获取视频对象
        video = Video.objects.get(id=video_id)
        logger.info(f"[Task {task_id}] 开始处理视频 {video_id}，标题: {video.title}")
        
        # 获取视频文件路径
        video_file_path = os.path.join(settings.MEDIA_ROOT, video.video_file.name)
        if not os.path.exists(video_file_path):
            raise FileNotFoundError(f"视频文件不存在: {video_file_path}")
        
        # 提取文件标识符
        file_path, file_name = os.path.split(video_file_path)
        file_base_name, file_ext = os.path.splitext(file_name)
        
        if len(file_base_name) < 32:
            file_identifier = file_base_name
        else:
            file_identifier = file_base_name[:32]
        
        # 创建 HLS 输出目录
        hls_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'hls', file_identifier)
        
        # 幂等性检查：如果 HLS 目录已存在且有内容，检查是否完整
        master_m3u8_path = os.path.join(hls_dir, 'master.m3u8')
        if os.path.exists(master_m3u8_path):
            logger.info(f"[Task {task_id}] HLS 文件已存在，检查完整性...")
            
            # 读取 master.m3u8 获取所有分辨率
            try:
                with open(master_m3u8_path, 'r') as f:
                    content = f.read()
                    # 提取所有分辨率的 m3u8 文件路径
                    import re
                    resolution_files = re.findall(r'(\d+p)/index\.m3u8', content)
                    
                    # 检查每个分辨率的 index.m3u8 是否存在且有内容
                    all_complete = True
                    for res in resolution_files:
                        res_m3u8 = os.path.join(hls_dir, res, 'index.m3u8')
                        if not os.path.exists(res_m3u8):
                            logger.warning(f"[Task {task_id}] {res}/index.m3u8 不存在")
                            all_complete = False
                            break
                        
                        # 检查 m3u8 文件是否有内容（至少有一个 .ts 文件）
                        with open(res_m3u8, 'r') as rf:
                            m3u8_content = rf.read()
                            if '.ts' not in m3u8_content:
                                logger.warning(f"[Task {task_id}] {res}/index.m3u8 没有 ts 文件引用")
                                all_complete = False
                                break
                    
                    if all_complete:
                        # 所有分辨率都完整，直接更新状态
                        relative_hls_path = f'videos/hls/{file_identifier}/master.m3u8'
                        video.hls_file = relative_hls_path
                        video.status = 'pending'
                        video.save(update_fields=['hls_file', 'status'])
                        logger.info(f"[Task {task_id}] 视频 {video_id} HLS文件完整，直接更新状态")
                        return {"status": "success", "reason": "already_exists"}
                    else:
                        logger.warning(f"[Task {task_id}] HLS 文件不完整，将重新转码")
                        # 删除不完整的文件
                        if os.path.exists(hls_dir):
                            shutil.rmtree(hls_dir)
                            logger.info(f"[Task {task_id}] 已删除不完整的 HLS 目录")
                        
            except Exception as e:
                logger.warning(f"[Task {task_id}] 检查 HLS 完整性失败: {e}，将重新转码")
                # 删除可能损坏的文件
                if os.path.exists(hls_dir):
                    shutil.rmtree(hls_dir)
        
        os.makedirs(hls_dir, exist_ok=True)
        
        # 创建缩略图输出目录
        thumbnails_dir = os.path.join(
            settings.MEDIA_ROOT, 'videos', 'thumbnails',
            f"{timezone.now().year}",
            f"{timezone.now().month:02d}",
            f"{timezone.now().day:02d}"
        )
        os.makedirs(thumbnails_dir, exist_ok=True)
        
        # 获取视频信息
        probe_cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'stream=width,height,codec_name,codec_type,bit_rate,r_frame_rate,sample_rate,channels:format=duration,size,bit_rate',
            '-of', 'json',
            video_file_path
        ]
        
        probe_process = subprocess.run(
            probe_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        if probe_process.returncode != 0:
            logger.error(f"[Task {task_id}] 获取视频信息失败: {probe_process.stderr}")
            raise Exception(f"获取视频信息失败: {probe_process.stderr}")
        
        import json
        video_info = json.loads(probe_process.stdout)
        logger.info(f"[Task {task_id}] FFprobe 输出: {json.dumps(video_info, indent=2)}")
        
        # 获取视频时长
        duration = 0
        if 'format' in video_info and 'duration' in video_info['format']:
            try:
                duration = float(video_info['format']['duration'])
                logger.info(f"[Task {task_id}] 从 format.duration 获取时长: {duration}秒")
            except (ValueError, TypeError) as e:
                logger.warning(f"[Task {task_id}] 解析 format.duration 失败: {e}")
        
        if duration == 0:
            for stream in video_info.get('streams', []):
                if 'duration' in stream:
                    try:
                        duration = float(stream['duration'])
                        logger.info(f"[Task {task_id}] 从 stream.duration 获取时长: {duration}秒")
                        break
                    except (ValueError, TypeError):
                        pass
        
        if duration == 0:
            logger.warning(f"[Task {task_id}] 无法获取视频时长，使用默认值 0")
        
        # 获取视频分辨率
        width, height = 0, 0
        video_codec = ''
        audio_codec = ''
        video_bitrate = 0
        audio_bitrate = 0
        frame_rate = 0
        has_audio = False  # 标记是否有音频流
        
        for stream in video_info.get('streams', []):
            codec_type = stream.get('codec_type', '')
            
            if codec_type == 'video' or ('width' in stream and not video_codec):
                width = int(stream.get('width', 0))
                height = int(stream.get('height', 0))
                video_codec = stream.get('codec_name', '')
                
                # 解析码率
                if stream.get('bit_rate'):
                    try:
                        video_bitrate = int(int(stream['bit_rate']) / 1000)  # 转为 kbps
                    except (ValueError, TypeError):
                        pass
                
                # 解析帧率 (格式如 "30/1" 或 "30000/1001")
                r_frame_rate = stream.get('r_frame_rate', '0/1')
                try:
                    if '/' in r_frame_rate:
                        num, den = r_frame_rate.split('/')
                        frame_rate = round(float(num) / float(den), 2) if float(den) != 0 else 0
                    else:
                        frame_rate = float(r_frame_rate)
                except (ValueError, TypeError, ZeroDivisionError):
                    frame_rate = 0
                
                logger.info(f"[Task {task_id}] 检测到视频: {width}x{height}, 编码={video_codec}, 码率={video_bitrate}kbps, 帧率={frame_rate}fps")
            
            elif codec_type == 'audio':
                has_audio = True
                audio_codec = stream.get('codec_name', '')
                if stream.get('bit_rate'):
                    try:
                        audio_bitrate = int(int(stream['bit_rate']) / 1000)
                    except (ValueError, TypeError):
                        pass
                logger.info(f"[Task {task_id}] 检测到音频: 编码={audio_codec}, 码率={audio_bitrate}kbps")
        
        if not has_audio:
            logger.warning(f"[Task {task_id}] 视频没有音频流")
        
        # 获取文件大小和总码率
        file_size = 0
        total_bitrate = 0
        if 'format' in video_info:
            try:
                file_size = int(video_info['format'].get('size', 0))
            except (ValueError, TypeError):
                pass
            try:
                total_bitrate = int(int(video_info['format'].get('bit_rate', 0)) / 1000)
            except (ValueError, TypeError):
                pass
        
        # 计算宽高比
        aspect_ratio = ''
        if width > 0 and height > 0:
            from math import gcd
            divisor = gcd(width, height)
            ratio_w = width // divisor
            ratio_h = height // divisor
            # 常见比例映射
            common_ratios = {
                (16, 9): '16:9', (9, 16): '9:16',
                (4, 3): '4:3', (3, 4): '3:4',
                (21, 9): '21:9', (9, 21): '9:21',
                (1, 1): '1:1',
                (3, 2): '3:2', (2, 3): '2:3',
            }
            aspect_ratio = common_ratios.get((ratio_w, ratio_h), f'{ratio_w}:{ratio_h}')
        
        if width == 0 or height == 0:
            logger.warning(f"[Task {task_id}] 无法获取视频分辨率，使用默认值 1920x1080")
            width, height = 1920, 1080
        
        # 生成缩略图
        middle_time = max(1, int(duration / 2)) if duration > 0 else 1
        thumbnail_file = os.path.join(thumbnails_dir, f"{file_identifier}.jpg")
        
        thumbnail_cmd = [
            'ffmpeg',
            '-ss', str(middle_time),
            '-i', video_file_path,
            '-vframes', '1',
            '-vf', 'scale=480:-1',
            '-y',
            thumbnail_file
        ]
        
        try:
            subprocess.run(thumbnail_cmd, check=True, capture_output=True)
            logger.info(f"[Task {task_id}] 缩略图生成成功")
        except subprocess.CalledProcessError as e:
            logger.warning(f"[Task {task_id}] 缩略图生成失败: {e.stderr}")
            # 缩略图失败不影响整体流程
        
        # 确定转码分辨率 (宽, 高, 预估带宽用于m3u8, CRF值)
        # CRF 值越小质量越高：18-23 是视觉无损范围
        standard_resolutions = [
            (3840, 2160, 15000, 22),  # 4K
            (2560, 1440, 8000, 22),   # 2K
            (1920, 1080, 5000, 23),   # 1080p
            (1280, 720, 2800, 23),    # 720p
            (854, 480, 1400, 24),     # 480p
            (640, 360, 800, 25),      # 360p
        ]
        
        # 用短边判断，避免放大视频（同时兼容横屏和竖屏）
        src_short_side = min(width, height)
        resolutions = [(w, h, b, crf) for w, h, b, crf in standard_resolutions if min(w, h) <= src_short_side]
        
        if not resolutions:
            bitrate = max(800, int(height * width / 1000))
            resolutions = [(width, height, bitrate, 23)]
            logger.info(f"[Task {task_id}] 使用原始分辨率: {width}x{height}")
        
        logger.info(f"[Task {task_id}] 将生成分辨率: {[(w, h) for w, h, _, _ in resolutions]}")
        
        # 创建各分辨率目录
        for res_width, res_height, bitrate, crf in resolutions:
            res_dir = os.path.join(hls_dir, f"{res_height}p")
            os.makedirs(res_dir, exist_ok=True)
        
        # 创建主 m3u8 文件
        with open(master_m3u8_path, 'w') as f:
            f.write('#EXTM3U\n')
            f.write('#EXT-X-VERSION:3\n')
            for res_width, res_height, bitrate, crf in resolutions:
                f.write(f'#EXT-X-STREAM-INF:BANDWIDTH={bitrate}000,RESOLUTION={res_width}x{res_height}\n')
                f.write(f'{res_height}p/index.m3u8\n')
        
        # 检查是否所有分辨率都已转码完成
        all_exist = all(
            os.path.exists(os.path.join(hls_dir, f"{h}p", 'index.m3u8'))
            for _, h, _, _ in resolutions
        )
        
        if all_exist:
            logger.info(f"[Task {task_id}] 所有分辨率已存在，跳过转码")
        else:
            # 单命令多输出：一次读取源文件，同时输出所有分辨率
            # 这样只解码一次，效率提升约 40%
            logger.info(f"[Task {task_id}] 开始单命令多输出转码...")
            
            hls_cmd = [
                'ffmpeg',
                '-i', video_file_path,
            ]
            
            # 为每个分辨率添加输出流
            for idx, (res_width, res_height, bitrate, crf) in enumerate(resolutions):
                res_dir = os.path.join(hls_dir, f"{res_height}p")
                res_m3u8 = os.path.join(res_dir, 'index.m3u8')
                
                # 跳过已存在的分辨率
                if os.path.exists(res_m3u8):
                    logger.info(f"[Task {task_id}] {res_height}p 已存在，跳过")
                    continue
                
                # 视频流映射
                hls_cmd.extend(['-map', '0:v:0'])
                
                # 音频流映射（只在有音频时添加）
                if has_audio:
                    hls_cmd.extend(['-map', '0:a:0'])
                
                # 视频编码设置
                # 检测源视频色深，决定使用 H.264 还是 H.265
                if video_codec == 'vp9':
                    # VP9 视频可能是 10-bit，使用 H.265 保留色深
                    hls_cmd.extend([
                        '-c:v', 'libx265',
                        '-preset', 'fast',
                        '-crf', str(crf),
                        '-maxrate', f'{bitrate}k',
                        '-bufsize', f'{bitrate * 2}k',
                        '-vf', f'scale={res_width}:{res_height}:force_original_aspect_ratio=decrease,pad={res_width}:{res_height}:(ow-iw)/2:(oh-ih)/2',
                        '-tag:v', 'hvc1',  # 兼容性标签
                    ])
                else:
                    # 其他视频使用 H.264
                    hls_cmd.extend([
                        '-c:v', 'libx264',
                        '-preset', 'fast',
                        '-crf', str(crf),
                        '-maxrate', f'{bitrate}k',
                        '-bufsize', f'{bitrate * 2}k',
                        '-pix_fmt', 'yuv420p',
                        '-vf', f'scale={res_width}:{res_height}:force_original_aspect_ratio=decrease,pad={res_width}:{res_height}:(ow-iw)/2:(oh-ih)/2',
                        '-profile:v', 'high',
                        '-level', '4.0',
                    ])
                
                # 音频编码设置（只在有音频时添加）
                if has_audio:
                    hls_cmd.extend([
                        '-c:a', 'aac',
                        '-b:a', '128k',
                    ])
                else:
                    # 没有音频时，明确指定不处理音频
                    hls_cmd.extend(['-an'])
                
                # HLS 设置
                hls_cmd.extend([
                    '-start_number', '0',
                    '-hls_time', '6',
                    '-hls_list_size', '0',
                    '-hls_playlist_type', 'vod',
                    '-hls_segment_filename', os.path.join(res_dir, 'segment_%03d.ts'),
                    res_m3u8
                ])
            
            # 如果有需要转码的分辨率才执行
            if len(hls_cmd) > 3:
                # 记录完整的 ffmpeg 命令（用于调试）
                logger.info(f"[Task {task_id}] {'='*60}")
                logger.info(f"[Task {task_id}] 开始执行 FFmpeg 转码")
                logger.info(f"[Task {task_id}] 命令长度: {len(hls_cmd)} 个参数")
                logger.info(f"[Task {task_id}] FFmpeg 命令: {' '.join(hls_cmd)}")
                logger.info(f"[Task {task_id}] {'='*60}")
                
                try:
                    import time
                    start_time = time.time()
                    
                    result = subprocess.run(
                        hls_cmd,
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True
                    )
                    
                    elapsed_time = time.time() - start_time
                    logger.info(f"[Task {task_id}] {'='*60}")
                    logger.info(f"[Task {task_id}] 多输出转码完成")
                    logger.info(f"[Task {task_id}] 耗时: {elapsed_time:.2f} 秒")
                    logger.info(f"[Task {task_id}] {'='*60}")
                    
                    # 记录 ffmpeg 的标准输出（如果有）
                    if result.stdout:
                        logger.debug(f"[Task {task_id}] FFmpeg stdout:\n{result.stdout}")
                    
                    # 记录 ffmpeg 的标准错误（通常包含进度信息）
                    if result.stderr:
                        # 只记录最后几行，避免日志过大
                        stderr_lines = result.stderr.strip().split('\n')
                        logger.debug(f"[Task {task_id}] FFmpeg stderr (最后10行):\n" + '\n'.join(stderr_lines[-10:]))
                        
                except subprocess.CalledProcessError as e:
                    # 完整记录错误到日志
                    logger.error(f"[Task {task_id}] {'='*60}")
                    logger.error(f"[Task {task_id}] 转码失败！")
                    logger.error(f"[Task {task_id}] 返回码: {e.returncode}")
                    logger.error(f"[Task {task_id}] {'='*60}")
                    logger.error(f"[Task {task_id}] 完整错误输出:\n{e.stderr}")
                    logger.error(f"[Task {task_id}] {'='*60}")
                    
                    # 清理失败的转码文件
                    logger.warning(f"[Task {task_id}] 清理失败的转码文件...")
                    try:
                        if os.path.exists(hls_dir):
                            shutil.rmtree(hls_dir)
                            logger.info(f"[Task {task_id}] 已删除失败的 HLS 目录: {hls_dir}")
                    except Exception as cleanup_error:
                        logger.error(f"[Task {task_id}] 清理失败: {cleanup_error}")
                    
                    # 提取最后几行错误信息（通常是最有用的）
                    stderr_lines = e.stderr.strip().split('\n')
                    # 获取最后20行，这通常包含实际错误
                    error_summary = '\n'.join(stderr_lines[-20:])
                    raise Exception(f"转码失败: {error_summary}")
        
        # 更新视频信息
        relative_hls_path = f'videos/hls/{file_identifier}/master.m3u8'
        relative_thumbnail_path = os.path.relpath(thumbnail_file, settings.MEDIA_ROOT).replace('\\', '/')
        
        # 最终验证：确保 HLS 文件真的存在且完整
        final_check_passed = False
        try:
            if os.path.exists(master_m3u8_path):
                with open(master_m3u8_path, 'r') as f:
                    content = f.read()
                    # 检查是否有分辨率引用
                    if 'index.m3u8' in content:
                        # 随机检查一个分辨率的文件
                        import re
                        resolution_files = re.findall(r'(\d+p)/index\.m3u8', content)
                        if resolution_files:
                            # 检查第一个分辨率
                            first_res = resolution_files[0]
                            first_res_m3u8 = os.path.join(hls_dir, first_res, 'index.m3u8')
                            if os.path.exists(first_res_m3u8):
                                with open(first_res_m3u8, 'r') as rf:
                                    if '.ts' in rf.read():
                                        final_check_passed = True
                                        logger.info(f"[Task {task_id}] 最终验证通过：HLS 文件完整")
        except Exception as e:
            logger.error(f"[Task {task_id}] 最终验证失败: {e}")
        
        if not final_check_passed:
            logger.error(f"[Task {task_id}] 最终验证失败：HLS 文件不完整或不存在")
            # 清理失败的文件
            if os.path.exists(hls_dir):
                shutil.rmtree(hls_dir)
            raise Exception("转码完成但文件验证失败，HLS 文件不完整")
        
        # 刷新数据库对象，获取最新的 thumbnail 值
        video.refresh_from_db()
        
        video.hls_file = relative_hls_path
        video.duration = duration
        video.resolution = max(h for _, h, _, _ in resolutions)  # 保存最高分辨率
        
        # 保存视频技术参数
        video.width = width
        video.height = height
        video.aspect_ratio = aspect_ratio
        video.video_codec = video_codec
        video.audio_codec = audio_codec
        video.bitrate = total_bitrate
        video.video_bitrate = video_bitrate
        video.audio_bitrate = audio_bitrate
        video.frame_rate = frame_rate
        video.file_size = file_size
        
        # 检查用户是否上传了自定义封面
        has_user_thumbnail = False
        if video.thumbnail:
            thumbnail_path = os.path.join(settings.MEDIA_ROOT, video.thumbnail.name)
            if os.path.exists(thumbnail_path):
                has_user_thumbnail = True
                logger.info(f"[Task {task_id}] 保留用户上传的封面: {video.thumbnail.name}")
        
        if not has_user_thumbnail and os.path.exists(thumbnail_file):
            video.thumbnail = relative_thumbnail_path
            logger.info(f"[Task {task_id}] 使用自动生成的封面: {relative_thumbnail_path}")
        
        video.status = 'pending'
        video.save(update_fields=[
            'hls_file', 'duration', 'resolution', 'status', 'thumbnail',
            'width', 'height', 'aspect_ratio', 'video_codec', 'audio_codec',
            'bitrate', 'video_bitrate', 'audio_bitrate', 'frame_rate', 'file_size'
        ])
        
        # 发送转码完成通知
        try:
            send_video_notification(
                user=video.user,
                video=video,
                notification_type='processing_complete',
                title='视频处理完成',
                content=f'您的视频《{video.title}》已处理完成，正在等待审核。'
            )
            logger.info(f"[Task {task_id}] 已发送转码完成通知给用户 {video.user_id}")
        except Exception as e:
            logger.warning(f"[Task {task_id}] 发送通知失败: {e}")
        
        # 发送视频状态和元数据更新（包含时长等信息）
        try:
            from core.websocket import send_video_status_update
            
            # 格式化时长为 HH:MM:SS 或 MM:SS
            def format_duration(seconds):
                if seconds <= 0:
                    return "00:00"
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                secs = int(seconds % 60)
                if hours > 0:
                    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
                return f"{minutes:02d}:{secs:02d}"
            
            send_video_status_update(
                user_id=video.user_id,
                video_data={
                    'id': video.id,
                    'status': video.status,
                    'title': video.title,
                    'duration': format_duration(duration),
                    'resolution': video.resolution,
                    'thumbnail': video.thumbnail.url if video.thumbnail else None,
                }
            )
            logger.info(f"[Task {task_id}] 已发送视频状态更新给用户 {video.user_id}")
        except Exception as e:
            logger.warning(f"[Task {task_id}] 发送视频状态更新失败: {e}")
        
        logger.info(f"[Task {task_id}] {'='*60}")
        logger.info(f"[Task {task_id}] 视频 {video_id} 处理完成！")
        logger.info(f"[Task {task_id}] 生成了 {len(resolutions)} 个分辨率")
        logger.info(f"[Task {task_id}] HLS 文件: {relative_hls_path}")
        logger.info(f"[Task {task_id}] {'='*60}")
        return {"status": "success", "video_id": video_id, "resolutions": len(resolutions)}
        
    except Video.DoesNotExist:
        logger.error(f"[Task {task_id}] {'='*60}")
        logger.error(f"[Task {task_id}] 错误: 视频 {video_id} 不存在")
        logger.error(f"[Task {task_id}] {'='*60}")
        return {"status": "error", "reason": "video_not_found"}
    
    except FileNotFoundError as e:
        logger.error(f"[Task {task_id}] {'='*60}")
        logger.error(f"[Task {task_id}] 错误: {str(e)}")
        logger.error(f"[Task {task_id}] {'='*60}")
        try:
            Video.objects.filter(id=video_id).update(status='failed')
        except Exception:
            pass
        return {"status": "error", "reason": "file_not_found"}
    
    except Exception as e:
        logger.error(f"[Task {task_id}] {'='*60}")
        logger.exception(f"[Task {task_id}] 处理视频 {video_id} 失败: {str(e)}")
        logger.error(f"[Task {task_id}] {'='*60}")
        try:
            Video.objects.filter(id=video_id).update(status='failed')
        except Exception:
            pass
        
        # 如果还有重试次数，抛出异常让 Celery 重试
        if self.request.retries < self.max_retries:
            logger.warning(f"[Task {task_id}] 将在 60 秒后重试 (第 {self.request.retries + 1}/{self.max_retries} 次)")
            raise self.retry(exc=e)
        
        logger.error(f"[Task {task_id}] 已达到最大重试次数，任务失败")
        return {"status": "error", "reason": str(e)}
    
    finally:
        # 无论成功失败，都释放锁
        release_video_lock(video_id)
        logger.info(f"[Task {task_id}] 释放视频 {video_id} 的处理锁")
        logger.info(f"[Task {task_id}] 任务结束\n")


@shared_task
def extract_video_metadata(video_id):
    """
    仅提取视频元数据，不重新转码
    用于已转码视频补充技术参数
    """
    from .models import Video
    
    logger.info(f"开始提取视频 {video_id} 的元数据")
    
    try:
        video = Video.objects.get(id=video_id)
        video_file_path = os.path.join(settings.MEDIA_ROOT, video.video_file.name)
        
        if not os.path.exists(video_file_path):
            logger.error(f"视频文件不存在: {video_file_path}")
            return {"status": "error", "reason": "file_not_found"}
        
        # 用 ffprobe 提取信息
        probe_cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'stream=width,height,codec_name,codec_type,bit_rate,r_frame_rate:format=duration,size,bit_rate',
            '-of', 'json',
            video_file_path
        ]
        
        import json
        probe_process = subprocess.run(probe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        
        if probe_process.returncode != 0:
            logger.error(f"ffprobe 失败: {probe_process.stderr}")
            return {"status": "error", "reason": "ffprobe_failed"}
        
        video_info = json.loads(probe_process.stdout)
        
        # 解析参数
        width, height = 0, 0
        video_codec, audio_codec = '', ''
        video_bitrate, audio_bitrate = 0, 0
        frame_rate = 0
        
        for stream in video_info.get('streams', []):
            codec_type = stream.get('codec_type', '')
            
            if codec_type == 'video' or ('width' in stream and not video_codec):
                width = int(stream.get('width', 0))
                height = int(stream.get('height', 0))
                video_codec = stream.get('codec_name', '')
                
                if stream.get('bit_rate'):
                    try:
                        video_bitrate = int(int(stream['bit_rate']) / 1000)
                    except:
                        pass
                
                r_frame_rate = stream.get('r_frame_rate', '0/1')
                try:
                    if '/' in r_frame_rate:
                        num, den = r_frame_rate.split('/')
                        frame_rate = round(float(num) / float(den), 2) if float(den) != 0 else 0
                    else:
                        frame_rate = float(r_frame_rate)
                except:
                    frame_rate = 0
            
            elif codec_type == 'audio':
                audio_codec = stream.get('codec_name', '')
                if stream.get('bit_rate'):
                    try:
                        audio_bitrate = int(int(stream['bit_rate']) / 1000)
                    except:
                        pass
        
        # 文件大小和总码率
        file_size = 0
        total_bitrate = 0
        duration = 0
        if 'format' in video_info:
            try:
                file_size = int(video_info['format'].get('size', 0))
                total_bitrate = int(int(video_info['format'].get('bit_rate', 0)) / 1000)
                duration = float(video_info['format'].get('duration', 0))
            except:
                pass
        
        # 计算宽高比
        aspect_ratio = ''
        if width > 0 and height > 0:
            from math import gcd
            divisor = gcd(width, height)
            ratio_w, ratio_h = width // divisor, height // divisor
            common_ratios = {
                (16, 9): '16:9', (9, 16): '9:16', (4, 3): '4:3', (3, 4): '3:4',
                (21, 9): '21:9', (1, 1): '1:1', (3, 2): '3:2', (2, 3): '2:3',
            }
            aspect_ratio = common_ratios.get((ratio_w, ratio_h), f'{ratio_w}:{ratio_h}')
        
        # 更新数据库
        video.width = width
        video.height = height
        video.aspect_ratio = aspect_ratio
        video.video_codec = video_codec
        video.audio_codec = audio_codec
        video.bitrate = total_bitrate
        video.video_bitrate = video_bitrate
        video.audio_bitrate = audio_bitrate
        video.frame_rate = frame_rate
        video.file_size = file_size
        if duration > 0 and video.duration == 0:
            video.duration = duration
        if height > 0 and video.resolution == 0:
            video.resolution = height
        
        video.save(update_fields=[
            'width', 'height', 'aspect_ratio', 'video_codec', 'audio_codec',
            'bitrate', 'video_bitrate', 'audio_bitrate', 'frame_rate', 'file_size',
            'duration', 'resolution'
        ])
        
        logger.info(f"视频 {video_id} 元数据提取完成: {width}x{height}, {video_codec}, {total_bitrate}kbps")
        return {"status": "success", "video_id": video_id}
        
    except Video.DoesNotExist:
        return {"status": "error", "reason": "video_not_found"}
    except Exception as e:
        logger.exception(f"提取元数据失败: {e}")
        return {"status": "error", "reason": str(e)}


@shared_task
def cleanup_deleted_videos():
    """
    定时清理已软删除超过30天的视频及其文件
    建议每天凌晨执行一次
    """
    from .models import Video
    from datetime import timedelta
    
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    videos_to_delete = Video.objects.filter(
        deleted_at__isnull=False,
        deleted_at__lt=thirty_days_ago
    )
    
    deleted_count = 0
    for video in videos_to_delete:
        try:
            logger.info(f"开始永久删除视频: {video.id} ({video.title})")
            
            # 删除原始视频文件
            if video.video_file:
                video_file_path = os.path.join(settings.MEDIA_ROOT, video.video_file.name)
                if os.path.exists(video_file_path):
                    try:
                        os.remove(video_file_path)
                        logger.info(f"已删除视频文件: {video_file_path}")
                    except Exception as e:
                        logger.error(f"删除视频文件失败: {str(e)}")
            
            # 删除 HLS 文件目录
            if video.hls_file:
                hls_path_parts = video.hls_file.split('/')
                if len(hls_path_parts) >= 3:
                    hls_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'hls', hls_path_parts[2])
                    if os.path.exists(hls_dir):
                        try:
                            shutil.rmtree(hls_dir)
                            logger.info(f"已删除 HLS 目录: {hls_dir}")
                        except Exception as e:
                            logger.error(f"删除 HLS 目录失败: {str(e)}")
            
            # 删除缩略图
            if video.thumbnail:
                thumbnail_path = os.path.join(settings.MEDIA_ROOT, video.thumbnail.name)
                if os.path.exists(thumbnail_path):
                    try:
                        os.remove(thumbnail_path)
                        logger.info(f"已删除缩略图: {thumbnail_path}")
                    except Exception as e:
                        logger.error(f"删除缩略图失败: {str(e)}")
            
            video_id = video.id
            video_title = video.title
            video.delete()
            
            deleted_count += 1
            logger.info(f"视频 {video_id} ({video_title}) 已永久删除")
            
        except Exception as e:
            logger.error(f"永久删除视频 {video.id} 失败: {str(e)}")
            continue
    
    logger.info(f"定时清理任务完成，共永久删除 {deleted_count} 个视频")
    return deleted_count


@shared_task
def publish_scheduled_videos():
    """
    发布到期的定时视频
    
    这个任务应该通过 Celery Beat 定时执行（例如每分钟一次）
    """
    from .models import Video
    from django.utils import timezone
    
    now = timezone.now()
    logger.info(f"{'='*60}")
    logger.info(f"检查定时发布视频 - {now}")
    logger.info(f"{'='*60}")
    
    # 查找到期的定时视频
    scheduled_videos = Video.objects.filter(
        scheduled_publish_time__lte=now,
        is_published=False,
        status='approved'  # 只发布已审核通过的视频
    )
    
    published_count = 0
    
    for video in scheduled_videos:
        try:
            logger.info(f"发布定时视频: {video.id} - {video.title}")
            logger.info(f"  定时时间: {video.scheduled_publish_time}")
            logger.info(f"  当前时间: {now}")
            
            video.is_published = True
            video.published_at = now
            video.scheduled_publish_time = None  # 清除定时发布时间
            video.save(update_fields=['is_published', 'published_at', 'scheduled_publish_time'])
            
            published_count += 1
            
            # 发送发布成功通知
            try:
                send_video_notification(
                    user=video.user,
                    video=video,
                    notification_type='video_published',
                    title='视频已发布',
                    content=f'您的视频《{video.title}》已成功发布。'
                )
                logger.info(f"  已发送发布通知给用户 {video.user_id}")
            except Exception as e:
                logger.warning(f"  发送通知失败: {e}")
            
            # 发送视频状态更新
            try:
                from core.websocket import send_video_status_update
                send_video_status_update(
                    user_id=video.user_id,
                    video_data={
                        'id': video.id,
                        'status': video.status,
                        'is_published': video.is_published,
                        'published_at': video.published_at.isoformat() if video.published_at else None,
                        'title': video.title,
                    }
                )
                logger.info(f"  已发送视频状态更新")
            except Exception as e:
                logger.warning(f"  发送视频状态更新失败: {e}")
                
        except Exception as e:
            logger.error(f"发布视频 {video.id} 失败: {e}")
            logger.exception(e)
    
    logger.info(f"{'='*60}")
    logger.info(f"定时发布完成: 共发布 {published_count} 个视频")
    logger.info(f"{'='*60}")
    
    return {
        "status": "success",
        "published_count": published_count,
        "timestamp": now.isoformat()
    }



@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def detect_video_subtitle(self, video_id):
    """
    检测视频字幕（软字幕 + 硬字幕）
    
    Args:
        video_id: 视频ID
        
    Returns:
        检测结果字典
    """
    from .models import Video
    from .subtitle_detector import get_subtitle_detector
    
    task_id = self.request.id or 'unknown'
    logger.info(f"{'='*60}")
    logger.info(f"[Task {task_id}] 开始字幕检测: video_id={video_id}")
    logger.info(f"{'='*60}")
    
    try:
        # 获取视频对象
        video = Video.objects.get(id=video_id)
        
        # 检查视频文件是否存在
        video_file_path = os.path.join(settings.MEDIA_ROOT, video.video_file.name)
        if not os.path.exists(video_file_path):
            logger.error(f"[Task {task_id}] 视频文件不存在: {video_file_path}")
            return {"status": "error", "reason": "file_not_found"}
        
        logger.info(f"[Task {task_id}] 视频文件: {video_file_path}")
        logger.info(f"[Task {task_id}] 视频标题: {video.title}")
        
        # 获取字幕检测器并执行检测
        detector = get_subtitle_detector()
        result = detector.detect_subtitle(video_file_path)
        
        logger.info(f"[Task {task_id}] 检测结果: {result}")
        
        # 更新数据库
        video.has_subtitle = result['has_subtitle']
        video.subtitle_type = result['subtitle_type']
        video.subtitle_language = result['subtitle_language']
        video.subtitle_detected_at = timezone.now()
        
        video.save(update_fields=[
            'has_subtitle',
            'subtitle_type',
            'subtitle_language',
            'subtitle_detected_at'
        ])
        
        logger.info(f"[Task {task_id}] {'='*60}")
        logger.info(f"[Task {task_id}] 字幕检测完成")
        logger.info(f"[Task {task_id}] 有字幕: {result['has_subtitle']}")
        logger.info(f"[Task {task_id}] 字幕类型: {result['subtitle_type']}")
        logger.info(f"[Task {task_id}] 字幕语言: {result['subtitle_language']}")
        logger.info(f"[Task {task_id}] {'='*60}")
        
        # 如果没有检测到字幕，可以发送通知提醒用户
        if not result['has_subtitle']:
            try:
                send_video_notification(
                    user=video.user,
                    video=video,
                    notification_type='no_subtitle_detected',
                    title='视频字幕提示',
                    content=f'您的视频《{video.title}》未检测到字幕，如需添加字幕可使用字幕编辑器。'
                )
                logger.info(f"[Task {task_id}] 已发送无字幕提醒通知")
            except Exception as e:
                logger.warning(f"[Task {task_id}] 发送通知失败: {e}")
        
        return {
            "status": "success",
            "video_id": video_id,
            "has_subtitle": result['has_subtitle'],
            "subtitle_type": result['subtitle_type'],
            "subtitle_language": result['subtitle_language']
        }
        
    except Video.DoesNotExist:
        logger.error(f"[Task {task_id}] 视频 {video_id} 不存在")
        return {"status": "error", "reason": "video_not_found"}
    
    except Exception as e:
        logger.error(f"[Task {task_id}] 字幕检测失败: {str(e)}", exc_info=True)
        
        # 如果还有重试次数，抛出异常让 Celery 重试
        if self.request.retries < self.max_retries:
            logger.warning(f"[Task {task_id}] 将在 120 秒后重试 (第 {self.request.retries + 1}/{self.max_retries} 次)")
            raise self.retry(exc=e)
        
        logger.error(f"[Task {task_id}] 已达到最大重试次数，任务失败")
        return {"status": "error", "reason": str(e)}
