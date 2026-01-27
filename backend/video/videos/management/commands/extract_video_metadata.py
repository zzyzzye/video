"""
批量提取已有视频的技术参数
用法: python manage.py extract_video_metadata
"""
from django.core.management.base import BaseCommand
from videos.models import Video
from videos.tasks import extract_video_metadata


class Command(BaseCommand):
    help = '批量提取已有视频的技术参数（不重新转码）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='提取所有视频（默认只提取缺少参数的视频）',
        )
        parser.add_argument(
            '--sync',
            action='store_true',
            help='同步执行（不使用 Celery）',
        )

    def handle(self, *args, **options):
        if options['all']:
            videos = Video.objects.filter(video_file__isnull=False).exclude(video_file='')
            self.stdout.write(f'将处理所有 {videos.count()} 个视频')
        else:
            # 只处理缺少技术参数的视频
            videos = Video.objects.filter(
                video_file__isnull=False,
                width=0
            ).exclude(video_file='')
            self.stdout.write(f'将处理 {videos.count()} 个缺少参数的视频')

        success_count = 0
        fail_count = 0

        for video in videos:
            self.stdout.write(f'处理视频 {video.id}: {video.title}')
            
            try:
                if options['sync']:
                    # 同步执行
                    from videos.tasks import extract_video_metadata
                    import subprocess
                    import json
                    import os
                    from django.conf import settings
                    from math import gcd
                    
                    video_file_path = os.path.join(settings.MEDIA_ROOT, video.video_file.name)
                    
                    if not os.path.exists(video_file_path):
                        self.stdout.write(self.style.WARNING(f'  文件不存在: {video_file_path}'))
                        fail_count += 1
                        continue
                    
                    probe_cmd = [
                        'ffprobe', '-v', 'error',
                        '-show_entries', 'stream=width,height,codec_name,codec_type,bit_rate,r_frame_rate:format=duration,size,bit_rate',
                        '-of', 'json', video_file_path
                    ]
                    
                    result = subprocess.run(probe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                    
                    if result.returncode != 0:
                        self.stdout.write(self.style.WARNING(f'  ffprobe 失败'))
                        fail_count += 1
                        continue
                    
                    video_info = json.loads(result.stdout)
                    
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
                                try: video_bitrate = int(int(stream['bit_rate']) / 1000)
                                except: pass
                            r_frame_rate = stream.get('r_frame_rate', '0/1')
                            try:
                                if '/' in r_frame_rate:
                                    num, den = r_frame_rate.split('/')
                                    frame_rate = round(float(num) / float(den), 2) if float(den) != 0 else 0
                            except: pass
                        elif codec_type == 'audio':
                            audio_codec = stream.get('codec_name', '')
                            if stream.get('bit_rate'):
                                try: audio_bitrate = int(int(stream['bit_rate']) / 1000)
                                except: pass
                    
                    file_size, total_bitrate, duration = 0, 0, 0
                    if 'format' in video_info:
                        try:
                            file_size = int(video_info['format'].get('size', 0))
                            total_bitrate = int(int(video_info['format'].get('bit_rate', 0)) / 1000)
                            duration = float(video_info['format'].get('duration', 0))
                        except: pass
                    
                    aspect_ratio = ''
                    if width > 0 and height > 0:
                        divisor = gcd(width, height)
                        ratio_w, ratio_h = width // divisor, height // divisor
                        common_ratios = {(16,9):'16:9',(9,16):'9:16',(4,3):'4:3',(3,4):'3:4',(21,9):'21:9',(1,1):'1:1'}
                        aspect_ratio = common_ratios.get((ratio_w, ratio_h), f'{ratio_w}:{ratio_h}')
                    
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
                    
                    self.stdout.write(self.style.SUCCESS(f'  完成: {width}x{height}, {video_codec}, {total_bitrate}kbps'))
                    success_count += 1
                else:
                    # 异步执行
                    extract_video_metadata.delay(video.id)
                    self.stdout.write(self.style.SUCCESS(f'  已提交任务'))
                    success_count += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  失败: {e}'))
                fail_count += 1

        self.stdout.write(self.style.SUCCESS(f'\n完成！成功: {success_count}, 失败: {fail_count}'))
