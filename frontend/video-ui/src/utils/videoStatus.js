/**
 * 视频状态工具函数
 * 统一管理视频状态的文本映射和样式类
 */

// 视频状态文本映射
export const VIDEO_STATUS_MAP = {
  uploading: '上传中',
  processing: '处理中',
  transcoding: '转码中',
  ready: '就绪',
  failed: '失败',
  pending: '待审核',
  approved: '已通过',
  rejected: '已拒绝',
  pending_subtitle_edit: '等待字幕编辑'
}

// 视频状态样式类映射
export const VIDEO_STATUS_CLASS_MAP = {
  uploading: 'status-uploading',
  processing: 'status-processing',
  transcoding: 'status-transcoding',
  ready: 'status-ready',
  failed: 'status-failed',
  pending: 'status-pending',
  approved: 'status-approved',
  rejected: 'status-rejected',
  pending_subtitle_edit: 'status-pending-subtitle'
}

/**
 * 获取状态文本
 * @param {string} status - 状态值
 * @returns {string} 状态文本
 */
export const getStatusText = (status) => {
  return VIDEO_STATUS_MAP[status] || status
}

/**
 * 获取状态样式类
 * @param {string} status - 状态值
 * @returns {string} 样式类名
 */
export const getStatusClass = (status) => {
  return VIDEO_STATUS_CLASS_MAP[status] || ''
}

/**
 * 判断状态是否为处理中（需要显示动画）
 * @param {string} status - 状态值
 * @returns {boolean}
 */
export const isProcessingStatus = (status) => {
  return ['processing', 'transcoding', 'uploading'].includes(status)
}
