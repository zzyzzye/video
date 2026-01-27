import service from './user';

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

// 获取系统统计数据
export function getStatistics() {
  return service({
    url: '/admin/statistics/',
    method: 'get'
  });
}

export default {
  getPendingVideos,
  approveVideo,
  rejectVideo,
  getReviewedVideos,
  getUsers,
  updateUserStatus,
  getReports,
  handleReport,
  getStatistics
}; 