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

// 检测视频字幕
export function detectSubtitle(videoId) {
  return service({
    url: `/videos/videos/${videoId}/detect-subtitle/`,
    method: 'post',
    timeout: 60000  // 字幕检测需要更长时间，设置为 60 秒
  });
}

// 触发视频转码
export function triggerTranscode(videoId) {
  return service({
    url: `/videos/videos/${videoId}/trigger-transcode/`,
    method: 'post'
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
  triggerTranscode,
  getWatchHistory,
  deleteWatchRecord,
  clearWatchHistory,
  getCollections,
  toggleCollection,
  deleteCollection,
  clearCollections
}; 