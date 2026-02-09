import axios from 'axios';
import { getToken } from '@/utils/auth';
import service from './user';
import { uploadFile } from '@/utils/upload';

// 获取视频详情
export function getVideoDetail(videoId) {
  return service({
    url: `/videos/videos/${videoId}/`,
    method: 'get'
  });
}

// 获取所有视频分类
export function getCategories() {
  return service({
    url: '/videos/categories/',
    method: 'get'
  });
}

// 获取所有标签
export function getTags() {
  return service({
    url: '/videos/tags/',
    method: 'get'
  });
}

// 上传视频文件（使用分片上传）
export function uploadVideo(file, onProgress) {
  return uploadFile(file, onProgress);
}

// 上传视频缩略图
export function uploadThumbnail(videoId, file) {
  const formData = new FormData();
  formData.append('thumbnail', file);
  
  return service({
    url: `/videos/videos/${videoId}/upload-thumbnail/`,
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
}

// 更新视频信息
export function updateVideoInfo(videoId, data) {
  return service({
    url: `/videos/videos/${videoId}/`,
    method: 'patch',
    data
  });
}

// 获取我的视频列表
export function getMyVideos(params) {
  return service({
    url: '/videos/videos/my_videos/',
    method: 'get',
    params
  });
}

// 获取用户观看历史
export function getWatchHistory(params) {
  return service({
    url: '/videos/views/history/',
    method: 'get',
    params
  });
}

// 获取用户收藏列表
export function getCollections(params) {
  return service({
    url: '/videos/collections/list/',
    method: 'get',
    params
  });
}

// 添加或取消收藏
export function toggleCollection(videoId) {
  return service({
    url: `/videos/collections/${videoId}/toggle/`,
    method: 'post'
  });
}

// 删除单个收藏
export function deleteCollection(collectionId) {
  return service({
    url: `/videos/collections/${collectionId}/`,
    method: 'delete'
  });
}

// 清空所有收藏
export function clearCollections() {
  return service({
    url: '/videos/collections/clear/',
    method: 'post'
  });
}

// 删除单个观看记录
export function deleteWatchRecord(recordId) {
  return service({
    url: `/videos/views/${recordId}/`,
    method: 'delete'
  });
}

// 清空所有观看记录
export function clearWatchHistory() {
  return service({
    url: '/videos/views/clear/',
    method: 'post'
  });
}

// 发布视频
export function publishVideo(videoId) {
  return service({
    url: `/videos/videos/${videoId}/publish/`,
    method: 'post'
  });
}

// 删除视频
export function deleteVideo(videoId) {
  return service({
    url: `/videos/videos/${videoId}/`,
    method: 'delete'
  });
}

// 检测视频字幕（异步）
export function detectSubtitle(videoId) {
  return service({
    url: `/ai/subtitle/${videoId}/detect/`,
    method: 'post',
    timeout: 60000
  });
}

// 查询字幕检测状态
export function getSubtitleDetectionStatus(videoId, taskId) {
  return service({
    url: `/ai/subtitle/${videoId}/detection-status/`,
    method: 'get',
    params: { task_id: taskId },
    timeout: 30000
  });
}

// 触发视频转码
export function triggerTranscode(videoId) {
  return service({
    url: `/videos/videos/${videoId}/trigger-transcode/`,
    method: 'post'
  });
}

// 获取视频字幕（外置 JSON）
export function getVideoSubtitles(videoId) {
  return service({
    url: `/ai/subtitle/${videoId}/data/`,
    method: 'get'
  });
}

// 保存视频字幕（外置 JSON）
export function updateVideoSubtitles(videoId, subtitles, style = null) {
  const data = { subtitles }
  if (style) {
    data.style = style
  }
  return service({
    url: `/ai/subtitle/${videoId}/data/`,
    method: 'put',
    data
  });
}

// 异步生成字幕（Whisper）
export function generateSubtitles(videoId, language = 'auto') {
  return service({
    url: `/ai/subtitle/${videoId}/generate/`,
    method: 'post',
    data: { language },
    timeout: 60000
  });
}

// 查询字幕生成任务状态
export function getSubtitleTaskStatus(videoId, taskId) {
  return service({
    url: `/ai/subtitle/${videoId}/task-status/`,
    method: 'get',
    params: { task_id: taskId },
    timeout: 30000
  });
}

// 翻译字幕（DeepSeek）
export function translateSubtitles(videoId, targetLanguage) {
  return service({
    url: `/videos/videos/${videoId}/subtitles/translate/`,
    method: 'post',
    data: { target_language: targetLanguage },
    timeout: 120000
  });
}

// 优化字幕（DeepSeek）
export function optimizeSubtitles(videoId) {
  return service({
    url: `/videos/videos/${videoId}/subtitles/optimize/`,
    method: 'post',
    timeout: 120000
  });
}

export default {
  getVideoDetail,
  getCategories,
  getTags,
  uploadVideo,
  uploadThumbnail,
  updateVideoInfo,
  getMyVideos,
  publishVideo,
  deleteVideo,
  detectSubtitle,
  getSubtitleDetectionStatus,
  triggerTranscode,
  getVideoSubtitles,
  updateVideoSubtitles,
  generateSubtitles,
  getSubtitleTaskStatus,
  getWatchHistory,
  deleteWatchRecord,
  clearWatchHistory,
  getCollections,
  toggleCollection,
  deleteCollection,
  clearCollections,
  translateSubtitles,
  optimizeSubtitles
};