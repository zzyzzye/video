import service from './user';

// ==================== AI 审核相关 ====================

// 获取 AI 审核列表
export function getAIModerationList(params) {
  return service({
    url: '/ai/moderation/',
    method: 'get',
    params
  });
}

// 获取 AI 审核详情
export function getAIModerationDetail(id) {
  return service({
    url: `/ai/moderation/${id}/`,
    method: 'get'
  });
}

// 提交视频 AI 审核
export function submitAIModeration(data) {
  return service({
    url: '/ai/moderation/moderate/',
    method: 'post',
    data
  });
}

// 批量 AI 审核
export function batchAIModeration(data) {
  return service({
    url: '/ai/moderation/batch/',
    method: 'post',
    data
  });
}

// 查询 AI 审核任务状态
export function getAITaskStatus(taskId) {
  return service({
    url: '/ai/moderation/task-status/',
    method: 'get',
    params: { task_id: taskId }
  });
}

// 提交 AI 审核结果到人工审核
export function submitAIReview(data) {
  return service({
    url: '/ai/moderation/submit-review/',
    method: 'post',
    data
  });
}

// 撤销审核结果
export function revokeAIReview(data) {
  return service({
    url: '/ai/moderation/revoke-review/',
    method: 'post',
    data
  });
}

// 重新审核视频
export function reModerateVideo(data) {
  return service({
    url: '/ai/moderation/re-moderate/',
    method: 'post',
    data
  });
}

// ==================== 视频审核相关 ====================

// 获取待审核视频列表
export function getPendingVideos(params) {
  return service({
    url: '/admin/videos/pending/',
    method: 'get',
    params
  });
}

// 审核通过视频
export function approveVideo(videoId, remark = '') {
  return service({
    url: `/admin/videos/${videoId}/approve/`,
    method: 'post',
    data: { remark }
  });
}

// 拒绝视频
export function rejectVideo(videoId, reason) {
  return service({
    url: `/admin/videos/${videoId}/reject/`,
    method: 'post',
    data: { reason }
  });
}

// 获取已审核视频列表
export function getReviewedVideos(params) {
  return service({
    url: '/admin/videos/reviewed/',
    method: 'get',
    params
  });
}

// ==================== 用户管理相关 ====================

// 获取系统用户列表
export function getUsers(params) {
  return service({
    url: '/admin/users/',
    method: 'get',
    params
  });
}

// 更新用户状态（禁用/启用）
export function updateUserStatus(userId, status) {
  return service({
    url: `/admin/users/${userId}/status/`,
    method: 'post',
    data: { status }
  });
}

// ==================== 举报管理相关 ====================

// 获取举报列表
export function getReports(params) {
  return service({
    url: '/admin/reports/',
    method: 'get',
    params
  });
}

// 处理举报
export function handleReport(reportId, action, remark) {
  return service({
    url: `/admin/reports/${reportId}/handle/`,
    method: 'post',
    data: { action, remark }
  });
}

// ==================== 统计数据相关 ====================

// 获取系统统计数据
export function getStatistics() {
  return service({
    url: '/admin/statistics/',
    method: 'get'
  });
}

// 获取统计概览
export function getStatisticsOverview() {
  return service({
    url: '/users/statistics/overview/',
    method: 'get'
  });
}

// 获取用户增长趋势
export function getUserTrend(days = 7) {
  return service({
    url: '/users/statistics/user-trend/',
    method: 'get',
    params: { days }
  });
}

// 获取视频上传趋势
export function getVideoTrend(days = 7) {
  return service({
    url: '/users/statistics/video-trend/',
    method: 'get',
    params: { days }
  });
}

// 获取用户角色分布
export function getRoleDistribution() {
  return service({
    url: '/users/statistics/role-distribution/',
    method: 'get'
  });
}

// 获取视频状态分布
export function getStatusDistribution() {
  return service({
    url: '/users/statistics/status-distribution/',
    method: 'get'
  });
}

// 获取热门视频排行
export function getTopVideos(limit = 10) {
  return service({
    url: '/users/statistics/top-videos/',
    method: 'get',
    params: { limit }
  });
}

export default {
  // AI 审核
  getAIModerationList,
  getAIModerationDetail,
  submitAIModeration,
  batchAIModeration,
  getAITaskStatus,
  submitAIReview,
  revokeAIReview,
  reModerateVideo,
  // 视频审核
  getPendingVideos,
  approveVideo,
  rejectVideo,
  getReviewedVideos,
  // 用户管理
  getUsers,
  updateUserStatus,
  // 举报管理
  getReports,
  handleReport,
  // 统计数据
  getStatistics,
  getStatisticsOverview,
  getUserTrend,
  getVideoTrend,
  getRoleDistribution,
  getStatusDistribution,
  getTopVideos
}; 