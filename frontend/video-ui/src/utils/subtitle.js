/**
 * 解析 SRT 字幕文件
 * @param {string} content - SRT 文件内容
 * @returns {Array} 字幕数组
 */
export function parseSRT(content) {
  try {
    const subtitles = [];
    const blocks = content.trim().split(/\n\s*\n/);
    
    blocks.forEach((block) => {
      const lines = block.trim().split('\n');
      if (lines.length < 3) return;
      
      const index = parseInt(lines[0]);
      const timeMatch = lines[1].match(/(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})/);
      
      if (timeMatch) {
        const text = lines.slice(2).join('\n');
        subtitles.push({
          id: index,
          startTime: parseSubtitleTime(timeMatch[1]),
          endTime: parseSubtitleTime(timeMatch[2]),
          text: text
        });
      }
    });
    
    return subtitles;
  } catch (error) {
    console.error('SRT 解析失败:', error);
    return [];
  }
}

/**
 * 解析 VTT 字幕文件
 * @param {string} content - VTT 文件内容
 * @returns {Array} 字幕数组
 */
export function parseVTT(content) {
  try {
    const subtitles = [];
    const cleanContent = content.replace(/^WEBVTT\s*\n\n?/, '');
    const blocks = cleanContent.trim().split(/\n\s*\n/);
    
    blocks.forEach((block, index) => {
      const lines = block.trim().split('\n');
      if (lines.length < 2) return;
      
      const timeMatch = lines[0].match(/(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})/);
      
      if (timeMatch) {
        const text = lines.slice(1).join('\n');
        subtitles.push({
          id: index + 1,
          startTime: parseSubtitleTime(timeMatch[1]),
          endTime: parseSubtitleTime(timeMatch[2]),
          text: text
        });
      }
    });
    
    return subtitles;
  } catch (error) {
    console.error('VTT 解析失败:', error);
    return [];
  }
}

/**
 * 将字幕数组转换为 SRT 格式
 * @param {Array} subtitles - 字幕数组
 * @returns {string} SRT 格式字符串
 */
export function toSRT(subtitles) {
  try {
    return subtitles.map((subtitle, index) => {
      const startTime = formatSubtitleTime(subtitle.startTime).replace('.', ',');
      const endTime = formatSubtitleTime(subtitle.endTime).replace('.', ',');
      return `${index + 1}\n${startTime} --> ${endTime}\n${subtitle.text}\n`;
    }).join('\n');
  } catch (error) {
    console.error('SRT 生成失败:', error);
    return '';
  }
}

/**
 * 将字幕数组转换为 VTT 格式
 * @param {Array} subtitles - 字幕数组
 * @returns {string} VTT 格式字符串
 */
export function toVTT(subtitles) {
  try {
    const content = subtitles.map((subtitle, index) => {
      const startTime = formatSubtitleTime(subtitle.startTime);
      const endTime = formatSubtitleTime(subtitle.endTime);
      return `${startTime} --> ${endTime}\n${subtitle.text}\n`;
    }).join('\n');
    return `WEBVTT\n\n${content}`;
  } catch (error) {
    console.error('VTT 生成失败:', error);
    return '';
  }
}

/**
 * 格式化时间（秒转为 HH:MM:SS.mmm）
 * @param {number} seconds - 秒数
 * @returns {string} 格式化的时间字符串
 */
export function formatSubtitleTime(seconds) {
  if (!seconds || isNaN(seconds)) seconds = 0;
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  const ms = Math.floor((seconds % 1) * 1000);
  
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${String(ms).padStart(3, '0')}`;
}

/**
 * 解析时间字符串为秒数
 * @param {string} timeStr - 时间字符串 (HH:MM:SS.mmm 或 HH:MM:SS,mmm)
 * @returns {number} 秒数
 */
export function parseSubtitleTime(timeStr) {
  if (!timeStr) return 0;
  
  // 统一使用点号作为毫秒分隔符
  const normalized = timeStr.replace(',', '.');
  const parts = normalized.split(':');
  
  if (parts.length !== 3) return 0;
  
  const hours = parseInt(parts[0], 10) || 0;
  const minutes = parseInt(parts[1], 10) || 0;
  const secondsParts = parts[2].split('.');
  const seconds = parseInt(secondsParts[0], 10) || 0;
  const ms = secondsParts[1] ? parseInt(secondsParts[1].padEnd(3, '0'), 10) : 0;
  
  return hours * 3600 + minutes * 60 + seconds + ms / 1000;
}

/**
 * 验证字幕时间轴是否有效
 * @param {Array} subtitles - 字幕数组
 * @returns {Object} 验证结果
 */
export function validateSubtitles(subtitles) {
  const errors = [];
  
  subtitles.forEach((subtitle, index) => {
    // 检查开始时间是否小于结束时间
    if (subtitle.startTime >= subtitle.endTime) {
      errors.push({
        index,
        type: 'time_order',
        message: `字幕 #${index + 1}: 开始时间必须小于结束时间`
      });
    }
    
    // 检查是否有文本
    if (!subtitle.text || subtitle.text.trim() === '') {
      errors.push({
        index,
        type: 'empty_text',
        message: `字幕 #${index + 1}: 字幕内容不能为空`
      });
    }
    
    // 检查是否与下一条字幕重叠
    if (index < subtitles.length - 1) {
      const nextSubtitle = subtitles[index + 1];
      if (subtitle.endTime > nextSubtitle.startTime) {
        errors.push({
          index,
          type: 'overlap',
          message: `字幕 #${index + 1} 与 #${index + 2} 时间重叠`
        });
      }
    }
  });
  
  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * 自动调整字幕时间轴（避免重叠）
 * @param {Array} subtitles - 字幕数组
 * @param {number} minGap - 最小间隔（秒）
 * @returns {Array} 调整后的字幕数组
 */
export function adjustSubtitleTimeline(subtitles, minGap = 0.1) {
  const adjusted = [...subtitles].sort((a, b) => a.startTime - b.startTime);
  
  for (let i = 0; i < adjusted.length - 1; i++) {
    const current = adjusted[i];
    const next = adjusted[i + 1];
    
    if (current.endTime + minGap > next.startTime) {
      current.endTime = next.startTime - minGap;
      
      // 确保持续时间至少为 0.5 秒
      if (current.endTime - current.startTime < 0.5) {
        current.endTime = current.startTime + 0.5;
      }
    }
  }
  
  return adjusted;
}

/**
 * 合并相邻的短字幕
 * @param {Array} subtitles - 字幕数组
 * @param {number} maxDuration - 最大持续时间（秒）
 * @param {number} maxGap - 最大间隔（秒）
 * @returns {Array} 合并后的字幕数组
 */
export function mergeShortSubtitles(subtitles, maxDuration = 5, maxGap = 1) {
  const merged = [];
  let current = null;
  
  subtitles.forEach((subtitle) => {
    if (!current) {
      current = { ...subtitle };
      return;
    }
    
    const gap = subtitle.startTime - current.endTime;
    const totalDuration = subtitle.endTime - current.startTime;
    
    if (gap <= maxGap && totalDuration <= maxDuration) {
      // 合并
      current.endTime = subtitle.endTime;
      current.text += ' ' + subtitle.text;
    } else {
      // 保存当前，开始新的
      merged.push(current);
      current = { ...subtitle };
    }
  });
  
  if (current) {
    merged.push(current);
  }
  
  return merged;
}

/**
 * 分割过长的字幕
 * @param {Array} subtitles - 字幕数组
 * @param {number} maxLength - 最大字符数
 * @returns {Array} 分割后的字幕数组
 */
export function splitLongSubtitles(subtitles, maxLength = 50) {
  const result = [];
  
  subtitles.forEach((subtitle) => {
    if (subtitle.text.length <= maxLength) {
      result.push(subtitle);
      return;
    }
    
    // 按标点符号分割
    const sentences = subtitle.text.split(/([。！？,.!?])/);
    const duration = subtitle.endTime - subtitle.startTime;
    const charPerSecond = subtitle.text.length / duration;
    
    let currentText = '';
    let currentStart = subtitle.startTime;
    
    sentences.forEach((sentence, index) => {
      if (currentText.length + sentence.length <= maxLength) {
        currentText += sentence;
      } else {
        if (currentText) {
          const segmentDuration = currentText.length / charPerSecond;
          result.push({
            startTime: currentStart,
            endTime: currentStart + segmentDuration,
            text: currentText.trim()
          });
          currentStart += segmentDuration;
        }
        currentText = sentence;
      }
    });
    
    if (currentText) {
      result.push({
        startTime: currentStart,
        endTime: subtitle.endTime,
        text: currentText.trim()
      });
    }
  });
  
  return result;
}

export default {
  parseSRT,
  parseVTT,
  toSRT,
  toVTT,
  formatSubtitleTime,
  parseSubtitleTime,
  validateSubtitles,
  adjustSubtitleTimeline,
  mergeShortSubtitles,
  splitLongSubtitles
};
