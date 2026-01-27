/**
 * 视频处理工具函数
 */

/**
 * 计算视频宽高比
 * @param {number} width - 视频宽度
 * @param {number} height - 视频高度
 * @returns {string} 宽高比字符串
 */
export function getVideoAspectRatio(width, height) {
  const gcd = (a, b) => b === 0 ? a : gcd(b, a % b);
  const divisor = gcd(width, height);
  const ratioW = width / divisor;
  const ratioH = height / divisor;
  
  const ratioMap = {
    '16:9': '16:9 (横屏)',
    '9:16': '9:16 (竖屏)',
    '4:3': '4:3',
    '3:4': '3:4',
    '1:1': '1:1 (方形)',
    '21:9': '21:9 (超宽)'
  };
  
  const key = `${ratioW}:${ratioH}`;
  return ratioMap[key] || key;
}

/**
 * 从视频生成多个封面（不同时间点）
 * @param {File} videoFile - 视频文件
 * @param {number[]} timePercents - 时间点百分比数组，默认 [0.1, 0.5, 0.8]
 * @returns {Promise<{covers: string[], duration: number, aspectRatio: string}>}
 */
export function generateCoversFromVideo(videoFile, timePercents = [0.1, 0.5, 0.8]) {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video');
    video.preload = 'metadata';
    video.playsInline = true;
    video.muted = true;
    
    const videoUrl = URL.createObjectURL(videoFile);
    video.src = videoUrl;
    
    video.onloadedmetadata = () => {
      const duration = video.duration;
      const aspectRatio = getVideoAspectRatio(video.videoWidth, video.videoHeight);
      const times = timePercents.map(p => duration * p);
      
      const covers = [];
      let capturedCount = 0;
      
      const captureFrame = (timeIndex) => {
        if (timeIndex >= times.length) {
          URL.revokeObjectURL(videoUrl);
          resolve({ covers, duration, aspectRatio });
          return;
        }
        
        video.currentTime = times[timeIndex];
        
        video.onseeked = () => {
          try {
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            covers.push(canvas.toDataURL('image/jpeg', 0.8));
          } catch (e) {
            console.error('捕获视频帧失败:', e);
            covers.push(null);
          }
          capturedCount++;
          captureFrame(capturedCount);
        };
      };
      
      captureFrame(0);
    };
    
    video.onerror = () => {
      URL.revokeObjectURL(videoUrl);
      reject(new Error('视频加载失败'));
    };
  });
}

/**
 * 从视频文件中提取封面（Blob格式）
 * @param {File} videoFile - 视频文件
 * @param {number} timeOffset - 提取时间点（秒），默认0.5秒
 * @returns {Promise<Blob>} 封面图片Blob
 */
export function extractThumbnailFromVideo(videoFile, timeOffset = 0.5) {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video');
    video.preload = 'metadata';
    video.playsInline = true;
    video.muted = true;
    
    const videoUrl = URL.createObjectURL(videoFile);
    video.src = videoUrl;
    
    video.onloadeddata = () => {
      try {
        video.currentTime = timeOffset;
      } catch (e) {
        // 如果设置时间失败，继续使用默认时间
      }
    };
    
    video.onseeked = () => {
      try {
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        canvas.toBlob((blob) => {
          URL.revokeObjectURL(videoUrl);
          blob ? resolve(blob) : reject(new Error('无法创建封面图片'));
        }, 'image/jpeg', 0.8);
      } catch (e) {
        URL.revokeObjectURL(videoUrl);
        reject(e);
      }
    };
    
    video.onerror = () => {
      URL.revokeObjectURL(videoUrl);
      reject(new Error('视频加载失败'));
    };
    
    // 超时处理
    setTimeout(() => {
      if (!video.videoWidth) {
        URL.revokeObjectURL(videoUrl);
        reject(new Error('视频加载超时'));
      }
    }, 5000);
  });
}
