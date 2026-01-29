"""
测试字幕检测器（独立脚本，不依赖 Django）
"""
import os
import sys
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_detector_standalone(video_path):
    """独立测试字幕检测器（不需要 Django）"""
    print("=" * 60)
    print("字幕检测器测试")
    print("=" * 60)
    
    if not os.path.exists(video_path):
        print(f"✗ 视频文件不存在: {video_path}")
        return
    
    print(f"\n测试视频: {video_path}")
    print(f"文件大小: {os.path.getsize(video_path) / (1024*1024):.2f} MB")
    
    # 1. 测试 PaddleOCR 初始化
    print("\n1. 初始化 PaddleOCR...")
    try:
        from paddleocr import PaddleOCR
        
        # 模型路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        models_dir = os.path.join(script_dir, 'video', 'models', 'PP-OCRv5')
        det_model_dir = os.path.join(models_dir, 'PP-OCRv5_server_det_infer')
        rec_model_dir = os.path.join(models_dir, 'PP-OCRv5_server_rec_infer')
        
        print(f"   模型目录: {models_dir}")
        print(f"   检测模型存在: {os.path.exists(det_model_dir)}")
        print(f"   识别模型存在: {os.path.exists(rec_model_dir)}")
        
        # 设置模型缓存目录到项目本地
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cache_dir = os.path.join(script_dir, 'video', 'models', 'paddleocr_cache')
        os.makedirs(cache_dir, exist_ok=True)
        
        # 设置环境变量，让 PaddleOCR 使用本地缓存目录
        os.environ['PADDLEX_HOME'] = cache_dir
        
        print(f"   模型缓存目录: {cache_dir}")
        print("   使用 PP-OCRv5 模型（首次使用会自动下载）...")
        from paddleocr import PaddleOCR
        
        ocr = PaddleOCR(
            text_detection_model_name="PP-OCRv5_server_det",
            text_recognition_model_name="PP-OCRv5_server_rec",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )
        
        print("✓ PaddleOCR 初始化成功")
        
    except Exception as e:
        print(f"✗ PaddleOCR 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        ocr = None
    
    # 2. 测试软字幕检测
    print("\n2. 检测软字幕（FFprobe）...")
    soft_result = detect_soft_subtitle(video_path)
    print(f"   结果: {soft_result}")
    
    if soft_result['has_subtitle']:
        print("✓ 检测到软字幕")
        print(f"   语言: {soft_result.get('language', 'unknown')}")
        print(f"   轨道数: {len(soft_result.get('tracks', []))}")
        for track in soft_result.get('tracks', []):
            print(f"     - 轨道 {track['index']}: {track['codec']} ({track['language']})")
    else:
        print("   未检测到软字幕")
    
    # 3. 测试硬字幕检测
    if ocr and not soft_result['has_subtitle']:
        print("\n3. 检测硬字幕（OCR）...")
        print("   这可能需要几分钟...")
        hard_result = detect_hard_subtitle(video_path, ocr, sample_count=10)
        print(f"   结果: {hard_result}")
        
        if hard_result['has_subtitle']:
            print("✓ 检测到硬字幕")
            print(f"   检测帧数: {hard_result['detected_frames']}/{hard_result['total_frames']}")
            print(f"   语言: {hard_result.get('language', 'unknown')}")
        else:
            print("   未检测到硬字幕")
    
    # 4. 总结
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

def detect_soft_subtitle(video_path):
    """检测软字幕"""
    import subprocess
    import json
    
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 's',
            '-show_entries', 'stream=index,codec_name,codec_type:stream_tags=language',
            '-of', 'json',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return {'has_subtitle': False, 'tracks': [], 'language': ''}
        
        data = json.loads(result.stdout)
        streams = data.get('streams', [])
        
        if not streams:
            return {'has_subtitle': False, 'tracks': [], 'language': ''}
        
        tracks = []
        languages = set()
        
        for stream in streams:
            track_info = {
                'index': stream.get('index'),
                'codec': stream.get('codec_name'),
                'language': stream.get('tags', {}).get('language', 'unknown')
            }
            tracks.append(track_info)
            
            lang = track_info['language']
            if lang and lang != 'unknown':
                languages.add(lang)
        
        return {
            'has_subtitle': True,
            'tracks': tracks,
            'language': ','.join(sorted(languages)) if languages else 'unknown'
        }
        
    except Exception as e:
        print(f"   错误: {e}")
        return {'has_subtitle': False, 'tracks': [], 'language': ''}

def detect_hard_subtitle(video_path, ocr, sample_count=5):
    """检测硬字幕"""
    import subprocess
    import json
    import tempfile
    from PIL import Image
    
    try:
        # 获取视频时长
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'json',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        data = json.loads(result.stdout)
        duration = float(data.get('format', {}).get('duration', 0))
        
        if duration <= 0:
            return {'has_subtitle': False, 'detected_frames': 0, 'total_frames': 0}
        
        print(f"   视频时长: {duration:.2f} 秒")
        
        # 计算采样时间点
        sample_times = []
        for i in range(sample_count):
            percentage = i / (sample_count - 1) if sample_count > 1 else 0.5
            time_point = duration * percentage
            if time_point >= duration:
                time_point = duration - 1
            sample_times.append(round(time_point, 2))
        
        print(f"   采样时间点: {sample_times}")
        
        # 提取帧并检测
        detected_count = 0
        
        with tempfile.TemporaryDirectory() as temp_dir:
            for i, time_point in enumerate(sample_times):
                frame_path = os.path.join(temp_dir, f'frame_{i}.jpg')
                
                print(f"   处理帧 {i+1}/{sample_count} ({time_point}s)...", end=' ')
                
                # 提取帧
                cmd = [
                    'ffmpeg',
                    '-ss', str(time_point),
                    '-i', video_path,
                    '-vframes', '1',
                    '-q:v', '2',
                    '-y',
                    frame_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, timeout=10)
                
                if result.returncode == 0 and os.path.exists(frame_path):
                    # OCR 检测（PaddleOCR 3.x API）
                    ocr_result = ocr.predict(frame_path)
                    
                    if ocr_result and len(ocr_result) > 0:
                        # 检查是否在字幕区域
                        img = Image.open(frame_path)
                        img_width, img_height = img.size
                        subtitle_area_top = img_height * 0.7
                        
                        has_text_in_subtitle = False
                        # PaddleOCR 3.x 返回 OCRResult 对象列表
                        for page_result in ocr_result:
                            if hasattr(page_result, 'boxes'):
                                for box in page_result.boxes:
                                    # box 有 .box 和 .text 属性
                                    coords = box.box  # [x1,y1,x2,y2,x3,y3,x4,y4]
                                    text = box.text
                                    
                                    # 计算中心 Y 坐标
                                    y_coords = [coords[1], coords[3], coords[5], coords[7]]
                                    center_y = sum(y_coords) / len(y_coords)
                                    
                                    if center_y >= subtitle_area_top:
                                        detected_count += 1
                                        has_text_in_subtitle = True
                                        print(f"✓ 检测到字幕: {text[:20]}")
                                        break
                            
                            if has_text_in_subtitle:
                                break
                        
                        if not has_text_in_subtitle:
                            print("未检测到字幕")
                    else:
                        print("未检测到文字")
                else:
                    print("提取失败")
        
        threshold = max(2, sample_count * 0.3)
        has_subtitle = detected_count >= threshold
        
        return {
            'has_subtitle': has_subtitle,
            'detected_frames': detected_count,
            'total_frames': sample_count,
            'language': 'zh' if has_subtitle else ''
        }
        
    except Exception as e:
        print(f"   错误: {e}")
        import traceback
        traceback.print_exc()
        return {'has_subtitle': False, 'detected_frames': 0, 'total_frames': 0}

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python test_subtitle_detector.py <视频文件路径>")
        print('示例: python test_subtitle_detector.py "E:\\video\\test.mp4"')
        sys.exit(1)
    
    video_path = sys.argv[1]
    test_detector_standalone(video_path)
