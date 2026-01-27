/**
 * 日期时间格式化工具函数
 */

/**
 * 格式化日期为指定格式
 * @param {Date|string|number} date - 日期对象、时间戳或日期字符串
 * @param {string} [format='YYYY-MM-DD HH:mm:ss'] - 格式化模式
 * @returns {string} 格式化后的日期字符串
 */
export function formatDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
  if (!date) return '';
  
  // 转换为Date对象
  const dateObj = typeof date === 'object' ? date : new Date(date);
  
  // 检查日期是否有效
  if (isNaN(dateObj.getTime())) {
    console.warn('Invalid date:', date);
    return '';
  }
  
  const year = dateObj.getFullYear();
  const month = String(dateObj.getMonth() + 1).padStart(2, '0');
  const day = String(dateObj.getDate()).padStart(2, '0');
  const hours = String(dateObj.getHours()).padStart(2, '0');
  const minutes = String(dateObj.getMinutes()).padStart(2, '0');
  const seconds = String(dateObj.getSeconds()).padStart(2, '0');
  
  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds);
}

/**
 * 格式化相对时间（如：3分钟前，2小时前，昨天等）
 * @param {Date|string|number} date - 日期对象、时间戳或日期字符串
 * @returns {string} 相对时间字符串
 */
export function formatRelativeTime(date) {
  if (!date) return '';
  
  // 转换为Date对象
  const dateObj = typeof date === 'object' ? date : new Date(date);
  
  // 检查日期是否有效
  if (isNaN(dateObj.getTime())) {
    console.warn('Invalid date:', date);
    return '';
  }
  
  const now = new Date();
  const diff = now.getTime() - dateObj.getTime();
  
  // 计算时间差
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  
  if (seconds < 60) {
    return '刚刚';
  } else if (minutes < 60) {
    return `${minutes}分钟前`;
  } else if (hours < 24) {
    return `${hours}小时前`;
  } else if (days < 7) {
    return `${days}天前`;
  } else {
    // 超过一周则显示具体日期
    return formatDate(dateObj, 'YYYY-MM-DD');
  }
}

/**
 * 格式化视频时长（将秒数转为 mm:ss 或 hh:mm:ss 格式）
 * @param {number} seconds - 视频时长（秒）
 * @returns {string} 格式化后的时长
 */
export function formatDuration(seconds) {
  if (!seconds || isNaN(seconds)) return '00:00';
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  } else {
    return `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }
}

/**
 * 格式化数字（如将1000转为1k）
 * @param {number} num - 要格式化的数字
 * @returns {string} 格式化后的数字
 */
export function formatNumber(num) {
  if (num === null || num === undefined) return '0';
  
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  } else {
    return num.toString();
  }
}

/**
 * 格式化文件大小
 * @param {number} bytes - 文件大小（字节）
 * @returns {string} 格式化后的文件大小
 */
export function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

/**
 * 获取文件扩展名
 * @param {string} filename - 文件名
 * @returns {string} 大写的扩展名
 */
export function getFileExtension(filename) {
  if (!filename) return '';
  return filename.split('.').pop().toUpperCase();
} 