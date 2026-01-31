<template>
  <div class="create-center-wrapper">
    <!-- 顶部导航栏 -->
    <div class="top-nav">
      <div class="nav-content">
        <div class="nav-left">
          <div class="logo" @click="goToHome">
            <span class="logo-text">MindPalette</span>
          </div>
          <h1 class="page-title">创作中心</h1>
        </div>
        <div class="nav-actions">
          <!-- 草稿保存状态 -->
          <transition name="fade">
            <div v-if="draftSaveStatus" class="draft-status">
              <el-icon v-if="draftSaveStatus === 'saving'" class="is-loading">
                <Loading />
              </el-icon>
              <el-icon v-else-if="draftSaveStatus === 'saved'" class="success-icon">
                <CircleCheck />
              </el-icon>
              <span class="status-text">
                {{ draftSaveStatus === 'saving' ? '保存中...' : '已保存' }}
              </span>
            </div>
          </transition>
          
          <!-- 草稿操作按钮 -->
          <el-dropdown v-if="activeTab === 'upload'" trigger="click" @command="handleDraftCommand">
            <el-button class="draft-btn">
              <el-icon><DocumentCopy /></el-icon>
              草稿
              <el-badge v-if="hasDraft" is-dot class="draft-badge" />
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="save">
                  <el-icon><DocumentCopy /></el-icon>
                  保存草稿
                </el-dropdown-item>
                <el-dropdown-item command="clear" :disabled="!hasDraft">
                  <el-icon><Delete /></el-icon>
                  清除草稿
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          
          <el-button 
            class="dashboard-btn"
            @click="goToDashboard"
          >
            <el-icon><User /></el-icon>
            个人中心
          </el-button>
          <el-button 
            v-if="activeTab === 'upload'"
            type="primary" 
            class="record-btn"
            @click="switchTab('record')"
          >
            录制视频
            <el-icon class="btn-arrow"><ArrowRight /></el-icon>
          </el-button>
          <el-button 
            v-else
            class="back-btn"
            @click="switchTab('upload')"
          >
            <el-icon><ArrowLeft /></el-icon>
            返回投稿
          </el-button>
        </div>
      </div>
    </div>

    <!-- 主内容区域 - 滑动容器 -->
    <div class="main-container">
      <div class="slider-wrapper" :style="{ transform: `translateX(-${activeTab === 'record' ? 50 : 0}%)` }">
        <!-- 上传视频页面 -->
        <div class="slide-page upload-page">
          <div class="upload-container">
            <div class="upload-wrapper">
              <!-- 左侧上传区 -->
              <div class="upload-area">
                <VideoUploadPreview
                  :file="selectedFile"
                  :preview-url="videoPreviewUrl"
                  :uploading="uploading"
                  :progress="uploadProgress"
                  :status="uploadStatus"
                  :duration="videoDuration"
                  :aspect-ratio="videoAspectRatio"
                  :subtitle-detecting="subtitleDetecting"
                  :subtitle-info="subtitleInfo"
                  @change="handleFileChange"
                />
              </div>

              <!-- 右侧表单区 -->
              <div class="form-area">
                <el-form :model="videoForm" label-position="top" class="video-form">
                  <!-- 封面 -->
                  <el-form-item label="封面" required class="cover-item">
                    <CoverSelector
                      v-model:covers="generatedCovers"
                      v-model:selectedIndex="selectedCoverIndex"
                    />
                  </el-form-item>

                  <!-- 标题 -->
                  <el-form-item label="标题" required>
                    <el-input 
                      v-model="videoForm.title" 
                      placeholder="请输入标题" 
                      maxlength="100"
                      show-word-limit
                      class="title-input"
                    />
                  </el-form-item>

                  <!-- 分区 -->
                  <el-form-item label="分区" required>
                    <el-select 
                      v-model="videoForm.category_id" 
                      placeholder="选择分区" 
                      class="category-select"
                    >
                      <el-option
                        v-for="category in categories"
                        :key="category.id"
                        :label="category.name"
                        :value="category.id"
                      />
                    </el-select>
                  </el-form-item>

                  <!-- 标签 -->
                  <el-form-item label="标签" class="tag-form-item">
                    <div class="tag-container">
                      <div class="tag-wrapper">
                        <div class="tag-list">
                          <div 
                            v-for="tag in videoForm.tags" 
                            :key="tag" 
                            class="tag-chip"
                          >
                            {{ getTagName(tag) }}
                            <span class="tag-remove" @click="removeTag(tag)">×</span>
                          </div>
                          <input
                            ref="tagInput"
                            v-model="tagInputValue"
                            @keyup.enter="addTag"
                            @blur="handleTagInputBlur"
                            placeholder="按回车添加标签"
                            class="tag-input-field"
                            :disabled="videoForm.tags.length >= 10"
                          />
                        </div>
                        <div class="tag-actions" v-if="videoForm.tags.length > 0">
                          <el-button 
                            link 
                            type="danger" 
                            size="small"
                            @click="clearAllTags"
                            class="clear-tags-btn"
                          >
                            <el-icon><Delete /></el-icon>
                            清空
                          </el-button>
                        </div>
                      </div>
                      <div class="tag-footer">
                        <span class="tag-count" :class="{ 'tag-count-warning': videoForm.tags.length >= 8, 'tag-count-full': videoForm.tags.length >= 10 }">
                          <el-icon class="count-icon"><PriceTag /></el-icon>
                          {{ videoForm.tags.length }}/10
                        </span>
                        <span class="tag-tip">
                          <el-icon class="tip-icon"><InfoFilled /></el-icon>
                          {{ videoForm.tags.length >= 10 ? '已达到标签上限' : '添加标签有助于视频被更多人发现' }}
                        </span>
                      </div>
                    </div>
                  </el-form-item>

                  <!-- 简介 -->
                  <el-form-item label="简介">
                    <el-input 
                      v-model="videoForm.description" 
                      type="textarea" 
                      :rows="4" 
                      placeholder="填写更全面的相关信息，让更多的人能找到你的视频"
                      maxlength="1000"
                      show-word-limit
                      class="desc-textarea"
                    />
                  </el-form-item>

                  <!-- 发布设置 -->
                  <el-form-item label="发布设置" class="publish-settings-item">
                    <el-collapse v-model="activeCollapse" class="settings-collapse">
                      <el-collapse-item name="publish">
                        <template #title>
                          <div class="collapse-title">
                            <el-icon class="title-icon"><Setting /></el-icon>
                            <span>发布设置</span>
                            <span class="title-tip">设置视频的观看权限、评论等</span>
                          </div>
                        </template>
                        
                        <div class="settings-content">
                          <!-- 观看权限 -->
                          <div class="setting-row">
                            <div class="setting-label">
                              <el-icon><View /></el-icon>
                              <span>观看权限</span>
                            </div>
                            <el-radio-group v-model="publishSettings.viewPermission" class="setting-control">
                              <el-radio label="public">公开</el-radio>
                              <el-radio label="private">私密</el-radio>
                              <el-radio label="fans">仅粉丝</el-radio>
                            </el-radio-group>
                          </div>

                          <!-- 评论权限 -->
                          <div class="setting-row">
                            <div class="setting-label">
                              <el-icon><ChatDotRound /></el-icon>
                              <span>评论权限</span>
                            </div>
                            <el-radio-group v-model="publishSettings.commentPermission" class="setting-control">
                              <el-radio label="all">允许所有人</el-radio>
                              <el-radio label="fans">仅粉丝</el-radio>
                              <el-radio label="none">关闭评论</el-radio>
                            </el-radio-group>
                          </div>

                          <!-- 其他设置 -->
                          <div class="setting-row">
                            <div class="setting-label">
                              <el-icon><More /></el-icon>
                              <span>其他设置</span>
                            </div>
                            <div class="setting-switches">
                              <div class="switch-item">
                                <span class="switch-label">允许下载</span>
                                <el-switch v-model="publishSettings.allowDownload" />
                              </div>
                              <div class="switch-item">
                                <span class="switch-label">显示在主页</span>
                                <el-switch v-model="publishSettings.showInProfile" />
                              </div>
                              <div class="switch-item">
                                <span class="switch-label">开启弹幕</span>
                                <el-switch v-model="publishSettings.enableDanmaku" />
                              </div>
                            </div>
                          </div>

                          <!-- 定时发布 -->
                          <div class="setting-row">
                            <div class="setting-label">
                              <el-icon><Clock /></el-icon>
                              <span>定时发布</span>
                            </div>
                            <div class="setting-control">
                              <el-switch 
                                v-model="publishSettings.enableSchedule" 
                                class="schedule-switch"
                              />
                              <el-date-picker
                                v-if="publishSettings.enableSchedule"
                                v-model="publishSettings.scheduleTime"
                                type="datetime"
                                placeholder="选择发布时间"
                                :disabled-date="disabledDate"
                                :disabled-hours="disabledHours"
                                format="YYYY-MM-DD HH:mm"
                                value-format="YYYY-MM-DD HH:mm:ss"
                                class="schedule-picker"
                              />
                            </div>
                          </div>

                          <!-- 原创声明 -->
                          <div class="setting-row">
                            <div class="setting-label">
                              <el-icon><Document /></el-icon>
                              <span>原创声明</span>
                            </div>
                            <el-radio-group v-model="publishSettings.originalType" class="setting-control">
                              <el-radio label="original">原创</el-radio>
                              <el-radio label="repost">转载</el-radio>
                              <el-radio label="selfmade">自制</el-radio>
                            </el-radio-group>
                          </div>
                        </div>
                      </el-collapse-item>
                    </el-collapse>
                  </el-form-item>

                  <!-- 底部操作按钮 -->
                  <div class="form-footer">
                    <el-button @click="resetForm" class="btn-cancel">
                      取消
                    </el-button>
                    <el-button 
                      type="primary" 
                      @click="submitVideo" 
                      :loading="uploading"
                      class="btn-submit"
                    >
                      {{ uploading ? '上传中...' : '立即投稿' }}
                    </el-button>
                  </div>
                </el-form>
              </div>
            </div>
          </div>
        </div>

        <!-- 录制视频页面 -->
        <div class="slide-page record-page">
          <div class="record-container">
            <VideoRecorder 
              ref="videoRecorderRef"
              @save="handleRecordedVideo"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, watch, onBeforeUnmount, h } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { VideoCamera, Upload, RefreshLeft, ArrowRight, ArrowLeft, User, DocumentCopy, Delete, Loading, CircleCheck, Setting, View, ChatDotRound, More, Clock, Document, PriceTag, InfoFilled, Calendar } from '@element-plus/icons-vue';
import PageHeader from '@/components/common/PageHeader.vue';
import { ElMessage, ElMessageBox, ElNotification, ElButton } from 'element-plus';
import { 
  uploadVideo, 
  updateVideoInfo, 
  getCategories, 
  getTags, 
  publishVideo,
  uploadThumbnail as apiUploadThumbnail,
  detectSubtitle,
  triggerTranscode as apiTriggerTranscode
} from '@/api/video';
import { generateCoversFromVideo, extractThumbnailFromVideo } from '@/utils/video';

// 组件
import VideoRecorder from './components/VideoRecorder.vue';
import CoverSelector from './components/CoverSelector.vue';
import VideoUploadPreview from './components/VideoUploadPreview.vue';

const router = useRouter();
const route = useRoute();
const activeTab = ref('upload');
const tagInput = ref(null);
const uploading = ref(false);
const uploadProgress = ref(0);
const uploadStatus = ref('');
const tagInputValue = ref('');
const selectedFile = ref(null);
const videoRecorderRef = ref(null);

// 封面相关
const generatedCovers = ref([null, null, null, null]);
const selectedCoverIndex = ref(0);
const videoPreviewUrl = ref('');
const videoDuration = ref(0);
const videoAspectRatio = ref('');

// 字幕检测相关
const subtitleDetecting = ref(false);
const subtitleInfo = ref(null);

// 字幕通知定时器管理（支持多个视频）
const subtitleNotificationTimers = ref(new Map());

// 视频表单数据
const videoForm = reactive({
  title: '',
  description: '',
  tags: [],
  category_id: null  // 改为单个分类 ID
});

// 分类和标签数据
const categories = ref([]);
const tags = ref([]);

// 草稿相关
const DRAFT_KEY = 'video_upload_draft';
const draftSaveStatus = ref(''); // 'saving', 'saved', ''
const hasDraft = ref(false);
let autoSaveTimer = null;

// 折叠面板
const activeCollapse = ref(['publish']);

// 发布设置
const publishSettings = reactive({
  viewPermission: 'public', // public, private, fans
  commentPermission: 'all', // all, fans, none
  allowDownload: false,
  showInProfile: true,
  enableDanmaku: true,
  enableSchedule: false,
  scheduleTime: null,
  originalType: 'original' // original, repost, selfmade
});

// 保存草稿到 localStorage
const saveDraft = () => {
  try {
    draftSaveStatus.value = 'saving';
    
    const draft = {
      title: videoForm.title,
      description: videoForm.description,
      tags: videoForm.tags,
      category_id: videoForm.category_id,
      selectedCoverIndex: selectedCoverIndex.value,
      publishSettings: { ...publishSettings },
      timestamp: Date.now()
    };
    
    localStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
    draftSaveStatus.value = 'saved';
    
    setTimeout(() => {
      draftSaveStatus.value = '';
    }, 2000);
  } catch (error) {
    console.error('保存草稿失败:', error);
    draftSaveStatus.value = '';
  }
};

// 加载草稿
const loadDraft = () => {
  try {
    const draftStr = localStorage.getItem(DRAFT_KEY);
    if (!draftStr) {
      hasDraft.value = false;
      return null;
    }
    
    const draft = JSON.parse(draftStr);
    hasDraft.value = true;
    return draft;
  } catch (error) {
    console.error('加载草稿失败:', error);
    hasDraft.value = false;
    return null;
  }
};

// 应用草稿
const applyDraft = (draft) => {
  if (!draft) return;
  
  videoForm.title = draft.title || '';
  videoForm.description = draft.description || '';
  videoForm.tags = draft.tags || [];
  videoForm.category_id = draft.category_id || null;
  selectedCoverIndex.value = draft.selectedCoverIndex || 0;
  
  // 恢复发布设置
  if (draft.publishSettings) {
    Object.assign(publishSettings, draft.publishSettings);
  }
  
  ElMessage.success('已恢复草稿内容');
};

// 清除草稿
const clearDraft = () => {
  try {
    localStorage.removeItem(DRAFT_KEY);
    hasDraft.value = false;
    ElMessage.success('草稿已清除');
  } catch (error) {
    console.error('清除草稿失败:', error);
  }
};

// 手动保存草稿
const handleSaveDraft = () => {
  saveDraft();
  ElMessage.success('草稿已保存');
};

// 询问是否恢复草稿
const askToRestoreDraft = async () => {
  const draft = loadDraft();
  if (!draft) return;
  
  try {
    await ElMessageBox.confirm(
      `检测到未完成的草稿（${new Date(draft.timestamp).toLocaleString()}），是否恢复？`,
      '恢复草稿',
      {
        confirmButtonText: '恢复',
        cancelButtonText: '放弃',
        type: 'info'
      }
    );
    applyDraft(draft);
  } catch {
    // 用户选择放弃草稿
    clearDraft();
  }
};

onMounted(async () => {
  if (route.query.activeTab) {
    activeTab.value = route.query.activeTab.toString();
    if (activeTab.value === 'record' && videoRecorderRef.value) {
      setTimeout(() => {
        videoRecorderRef.value.initCamera();
      }, 500);
    }
  }
  
  await fetchCategoriesAndTags();
  
  // 检查是否有草稿
  await askToRestoreDraft();
  
  // 启动自动保存
  startAutoSave();
});

// 启动自动保存
const startAutoSave = () => {
  // 每30秒自动保存一次
  autoSaveTimer = setInterval(() => {
    // 只有在有内容时才保存
    if (videoForm.title || videoForm.description || videoForm.tags.length > 0) {
      saveDraft();
    }
  }, 30000); // 30秒
};

// 停止自动保存
const stopAutoSave = () => {
  if (autoSaveTimer) {
    clearInterval(autoSaveTimer);
    autoSaveTimer = null;
  }
};

// 处理草稿下拉菜单命令
const handleDraftCommand = (command) => {
  if (command === 'save') {
    handleSaveDraft();
  } else if (command === 'clear') {
    ElMessageBox.confirm(
      '确定要清除草稿吗？此操作不可恢复。',
      '清除草稿',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    ).then(() => {
      clearDraft();
    }).catch(() => {
      // 用户取消
    });
  }
};

// 监听表单变化，防抖保存
let debounceTimer = null;
watch(
  () => ({
    title: videoForm.title,
    description: videoForm.description,
    tags: videoForm.tags,
    category_id: videoForm.category_id,
    publishSettings: { ...publishSettings }
  }),
  () => {
    // 清除之前的定时器
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    
    // 3秒后保存
    debounceTimer = setTimeout(() => {
      if (videoForm.title || videoForm.description || videoForm.tags.length > 0) {
        saveDraft();
      }
    }, 3000);
  },
  { deep: true }
);

// 禁用过去的日期
const disabledDate = (time) => {
  return time.getTime() < Date.now() - 8.64e7; // 禁用昨天之前的日期
};

// 禁用过去的小时
const disabledHours = () => {
  const hours = [];
  const now = new Date();
  const currentHour = now.getHours();
  
  // 如果是今天，禁用当前小时之前的时间
  if (publishSettings.scheduleTime) {
    const selectedDate = new Date(publishSettings.scheduleTime);
    if (selectedDate.toDateString() === now.toDateString()) {
      for (let i = 0; i < currentHour; i++) {
        hours.push(i);
      }
    }
  }
  
  return hours;
};

const fetchCategoriesAndTags = async () => {
  try {
    const [categoriesRes, tagsRes] = await Promise.all([
      getCategories(),
      getTags()
    ]);
    
    if (categoriesRes && categoriesRes.results) {
      categories.value = categoriesRes.results;
    } else if (Array.isArray(categoriesRes)) {
      categories.value = categoriesRes;
    } else {
      categories.value = [];
    }
    
    if (tagsRes && tagsRes.results) {
      tags.value = tagsRes.results;
    } else if (Array.isArray(tagsRes)) {
      tags.value = tagsRes;
    } else {
      tags.value = [];
    }
  } catch (error) {
    console.error('获取分区和标签失败:', error);
    categories.value = [];
    tags.value = [];
  }
};

watch(activeTab, (newTab, oldTab) => {
  if (!newTab) {
    activeTab.value = 'upload';
    return;
  }
  
  if (newTab === 'record' && videoRecorderRef.value) {
    nextTick(() => {
      videoRecorderRef.value.initCamera();
    });
  } else if (oldTab === 'record' && videoRecorderRef.value) {
    videoRecorderRef.value.stopCamera();
  }
});

const switchTab = (tabName) => {
  if (activeTab.value === tabName) return;
  
  if (activeTab.value === 'record' && videoRecorderRef.value) {
    videoRecorderRef.value.stopCamera();
  }
  
  activeTab.value = tabName;
  
  if (tabName === 'record' && videoRecorderRef.value) {
    nextTick(() => {
      videoRecorderRef.value.initCamera();
    });
  }
};

const goToHome = () => {
  router.push('/');
};

const goToDashboard = () => {
  router.push('/user/dashboard');
};

const handleRecordedVideo = async (videoFile) => {
  selectedFile.value = videoFile;
  const now = new Date();
  videoForm.title = `录制视频_${now.getMonth()+1}月${now.getDate()}日${now.getHours()}:${now.getMinutes()}`;
  
  ElMessage.success('视频录制完成，正在上传...');
  activeTab.value = 'upload';
  
  try {
    uploading.value = true;
    uploadStatus.value = '上传视频中...';
    uploadProgress.value = 0;
    
    const result = await uploadVideo(videoFile, (progress, status) => {
      uploadProgress.value = progress;
      if (status) uploadStatus.value = status;
    });
    
    try {
      uploadStatus.value = '正在生成封面...';
      const thumbnailBlob = await extractThumbnailFromVideo(videoFile);
      const thumbnailFile = new File([thumbnailBlob], 'thumbnail.jpg', { type: 'image/jpeg' });
      uploadStatus.value = '上传封面中...';
      await apiUploadThumbnail(result.id, thumbnailFile);
    } catch (thumbnailError) {
      console.error('生成或上传封面失败:', thumbnailError);
      ElMessage.warning('封面生成失败，将使用默认封面');
    }
    
    uploadStatus.value = '更新视频信息...';
    await updateVideoInfo(result.id, {
      title: videoForm.title,
      description: videoForm.description || '录制的视频',
      category_id: videoForm.category_id,
      tag_ids: [],
      new_tags: []
    });
    
    uploadStatus.value = '提交审核...';
    await publishVideo(result.id);
    
    ElMessage.success('录制视频上传成功，已提交审核');
    resetForm();
  } catch (error) {
    console.error('上传录制视频失败:', error);
    ElMessage.error('上传录制视频失败: ' + (error.message || '未知错误'));
  } finally {
    uploading.value = false;
    uploadStatus.value = '';
  }
};

const handleTagInputBlur = () => {
  if (tagInputValue.value.trim()) {
    addTag();
  }
  tagInputValue.value = '';
};

const addTag = () => {
  if (!tagInputValue.value) return;
  
  // 检查标签数量限制
  if (videoForm.tags.length >= 10) {
    ElMessage.warning('最多只能添加10个标签');
    tagInputValue.value = '';
    return;
  }
  
  try {
    const newTagName = String(tagInputValue.value).trim();
    if (newTagName) {
      const newTagId = `new-${Date.now()}`;
      const newTag = { id: newTagId, name: newTagName, isNew: true };
      if (!Array.isArray(tags.value)) {
        tags.value = [];
      }
      tags.value.push(newTag);
      videoForm.tags.push(newTagId);
    }
    
    tagInputValue.value = '';
    nextTick(() => {
      if (tagInput.value) {
        tagInput.value.focus();
      }
    });
  } catch (err) {
    console.error('添加标签出错:', err);
    ElMessage.error('添加标签失败');
  }
};

const removeTag = (tag) => {
  videoForm.tags.splice(videoForm.tags.indexOf(tag), 1);
};

const clearAllTags = () => {
  ElMessageBox.confirm(
    '确定要清空所有标签吗？',
    '清空标签',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    videoForm.tags = [];
    ElMessage.success('已清空所有标签');
  }).catch(() => {
    // 用户取消
  });
};

const getTagName = (tagId) => {
  try {
    if (!Array.isArray(tags.value)) return tagId;
    const tag = tags.value.find(t => t && t.id === tagId);
    return tag ? tag.name : tagId;
  } catch (err) {
    return tagId;
  }
};

const handleFileChange = async (file) => {
  selectedFile.value = file.raw;
  
  if (!videoForm.title && file.name) {
    videoForm.title = file.name.split('.').slice(0, -1).join('.');
  }
  
  videoPreviewUrl.value = URL.createObjectURL(file.raw);
  
  try {
    const result = await generateCoversFromVideo(file.raw);
    generatedCovers.value = [...result.covers, null];
    videoDuration.value = result.duration;
    videoAspectRatio.value = result.aspectRatio;
    ElMessage.success('封面生成成功');
  } catch (error) {
    console.error('生成封面失败:', error);
    ElMessage.warning('封面生成失败，请手动上传');
  }
};

const handleCategoryChange = (value) => {
  console.log('选择的分类:', value);
};

const submitVideo = async () => {
  if (!videoForm.title) {
    ElMessage.error('请填写视频标题');
    return;
  }
  
  if (!selectedFile.value) {
    ElMessage.error('请选择要上传的视频文件');
    return;
  }
  
  try {
    uploading.value = true;
    uploadStatus.value = '准备上传...';
    uploadProgress.value = 0;
    
    let thumbnailFile = null;
    if (generatedCovers.value[selectedCoverIndex.value]) {
      try {
        uploadStatus.value = '准备封面...';
        const coverDataUrl = generatedCovers.value[selectedCoverIndex.value];
        const response = await fetch(coverDataUrl);
        const blob = await response.blob();
        thumbnailFile = new File([blob], 'thumbnail.jpg', { type: 'image/jpeg' });
      } catch (thumbnailError) {
        console.error('准备封面失败:', thumbnailError);
        ElMessage.warning('封面准备失败，将使用自动生成的封面');
      }
    }
    
    const video = await uploadVideo(
      selectedFile.value, 
      (progress, status) => {
        uploadProgress.value = progress;
        if (status) uploadStatus.value = status;
      }
    );
    
    if (!video || !video.id) {
      throw new Error('上传失败，未返回视频数据');
    }
    
    const videoId = video.id;
    
    // 并行处理：字幕检测 + 封面上传
    const tasks = [];
    
    // 字幕检测任务
    tasks.push(
      (async () => {
        try {
          subtitleDetecting.value = true;
          uploadStatus.value = '检测字幕中...';
          const subtitleResult = await detectSubtitle(videoId);
          subtitleInfo.value = subtitleResult.subtitle_info;
          
          // 显示详细的字幕检测结果
          if (subtitleResult.subtitle_info?.has_subtitle) {
            const typeText = subtitleResult.subtitle_info.subtitle_type === 'soft' ? '软字幕' : '硬字幕';
            const langText = subtitleResult.subtitle_info.subtitle_language || '未知语言';
            ElMessage.success(`字幕检测完成：检测到${typeText}（${langText}）`);
          } else {
            ElMessage.info('字幕检测完成：未检测到字幕');
          }
          
          // 处理字幕检测结果，显示引导通知
          handleSubtitleDetectionResult(videoId, subtitleResult.subtitle_info);
        } catch (subtitleError) {
          console.error('字幕检测失败:', subtitleError);
          ElMessage.warning('字幕检测失败，但不影响视频上传');
        } finally {
          subtitleDetecting.value = false;
        }
      })()
    );
    
    // 封面上传任务
    if (thumbnailFile) {
      tasks.push(
        (async () => {
          try {
            uploadStatus.value = '上传封面中...';
            await apiUploadThumbnail(videoId, thumbnailFile);
          } catch (thumbnailError) {
            console.error('上传封面失败:', thumbnailError);
            ElMessage.warning('封面上传失败，将使用自动生成的封面');
          }
        })()
      );
    }
    
    // 等待所有任务完成
    await Promise.all(tasks);

    const newTags = [];
    const existingTagIds = [];
    
    for (const tagId of videoForm.tags) {
      if (typeof tagId === 'string' && tagId.startsWith('new-')) {
        const tag = tags.value.find(t => t.id === tagId);
        if (tag && tag.isNew) {
          newTags.push(tag.name);
        }
      } else {
        existingTagIds.push(tagId);
      }
    }
    
    uploadStatus.value = '更新视频信息...';
    try {
      await updateVideoInfo(videoId, {
        title: videoForm.title,
        description: videoForm.description,
        category_id: videoForm.category_id,
        tag_ids: existingTagIds,
        new_tags: newTags,
        // 发布设置
        view_permission: publishSettings.viewPermission,
        comment_permission: publishSettings.commentPermission,
        allow_download: publishSettings.allowDownload,
        enable_danmaku: publishSettings.enableDanmaku,
        show_in_profile: publishSettings.showInProfile,
        scheduled_publish_time: publishSettings.enableSchedule 
          ? publishSettings.scheduleTime 
          : null,
        original_type: publishSettings.originalType
      });
    } catch (updateError) {
      console.error('更新视频信息失败:', updateError);
      ElMessage.warning('视频已上传，但更新视频信息失败');
    }
    
    uploadStatus.value = '提交审核...';
    try {
      await publishVideo(videoId);
    } catch (publishError) {
      console.error('提交视频失败:', publishError);
    }
    
    // 构建成功消息，包含字幕检测结果
    let successMessage = '视频上传成功，状态为"未审核"，请等待管理员审核';
    if (subtitleInfo.value) {
      if (subtitleInfo.value.has_subtitle) {
        const typeText = subtitleInfo.value.subtitle_type === 'soft' ? '软字幕' : '硬字幕';
        const langText = subtitleInfo.value.subtitle_language || '未知语言';
        successMessage += `\n✓ 已检测到${typeText}（${langText}）`;
      } else {
        successMessage += '\n✗ 未检测到字幕';
      }
    }
    
    ElMessage({
      message: successMessage,
      type: 'success',
      duration: 5000,  // 显示 5 秒
      dangerouslyUseHTMLString: false
    });
    
    // 延迟 3 秒后重置表单，让用户有时间看到字幕信息
    setTimeout(() => {
      resetForm();
    }, 3000);
  } catch (error) {
    console.error('视频上传失败:', error);
    let errorMessage = '视频上传失败';
    if (error.response?.data?.detail) {
      errorMessage += `: ${error.response.data.detail}`;
    } else if (error.message) {
      errorMessage += `: ${error.message}`;
    }
    ElMessage.error(errorMessage);
  } finally {
    uploading.value = false;
    uploadStatus.value = '';
  }
};

// ==================== 字幕编辑引导功能 ====================

/**
 * 处理字幕检测结果
 * @param {number} videoId - 视频ID
 * @param {object} subtitleInfo - 字幕信息对象
 */
const handleSubtitleDetectionResult = (videoId, subtitleInfo) => {
  if (!subtitleInfo) return;
  
  const { has_subtitle, subtitle_type, subtitle_language } = subtitleInfo;
  
  // 情况1: 未检测到字幕
  if (!has_subtitle) {
    showSubtitleNotification(videoId, {
      has_subtitle: false,
      title: '未检测到字幕',
      message: '是否添加字幕？添加字幕可以让更多人看懂您的视频'
    });
  }
  // 情况2: 检测到软字幕
  else if (subtitle_type === 'soft') {
    showSubtitleNotification(videoId, {
      has_subtitle: true,
      subtitle_type: 'soft',
      subtitle_language: subtitle_language,
      title: `检测到字幕（${subtitle_language || '未知语言'}）`,
      message: '是否查看或编辑字幕？'
    });
  }
  // 情况3: 检测到硬字幕
  else if (subtitle_type === 'hard') {
    ElMessage.info({
      message: `检测到字幕（${subtitle_language || '未知语言'}），视频处理中...`,
      duration: 3000
    });
    // 硬字幕直接处理，后端已自动处理
  }
};

/**
 * 显示字幕通知
 * @param {number} videoId - 视频ID
 * @param {object} subtitleInfo - 字幕信息
 */
const showSubtitleNotification = (videoId, subtitleInfo) => {
  let countdown = 10;
  
  // 创建响应式的倒计时文本
  const countdownDisplay = ref(`${countdown}秒后将自动继续`);
  
  // 每秒更新倒计时
  const countdownInterval = setInterval(() => {
    countdown--;
    countdownDisplay.value = `${countdown}秒后将自动继续`;
    if (countdown <= 0) {
      clearInterval(countdownInterval);
    }
  }, 1000);
  
  // 10秒后自动开始处理
  const timer = setTimeout(async () => {
    clearInterval(countdownInterval);
    subtitleNotificationTimers.value.delete(videoId);
    try {
      await triggerTranscodeHandler(videoId);
      ElMessage.info('视频已自动开始处理');
    } catch (error) {
      console.error('处理启动失败:', error);
      ElMessage.error('处理启动失败，请稍后重试');
    }
  }, 10000);
  
  // 存储定时器（支持多个视频）
  subtitleNotificationTimers.value.set(videoId, { timer, countdownInterval });
  
  // 显示通知
  const notification = ElNotification({
    title: subtitleInfo.title,
    message: h('div', { class: 'subtitle-notification-content' }, [
      // 提示文本
      h('p', { 
        style: 'margin: 0 0 8px 0; font-size: 14px; color: #606266;' 
      }, subtitleInfo.message),
      
      // 倒计时提示（动态显示）
      h('div', { 
        style: 'background: #f0f9ff; padding: 8px 12px; border-radius: 4px; margin-bottom: 12px; font-size: 12px; color: #0369a1; display: flex; align-items: center; gap: 6px;' 
      }, [
        h('span', '⏱️'),
        h('span', () => countdownDisplay.value)
      ]),
      
      // 操作按钮
      h('div', { 
        style: 'display: flex; gap: 8px; justify-content: flex-end;' 
      }, [
        // 立即添加/编辑按钮
        h(ElButton, {
          size: 'small',
          type: 'primary',
          onClick: () => {
            notification.close();
            handleEditSubtitle(videoId, subtitleInfo);
          }
        }, () => subtitleInfo.has_subtitle ? '立即编辑' : '立即添加'),
        
        // 跳过按钮
        h(ElButton, {
          size: 'small',
          onClick: () => {
            notification.close();
            handleSkipEdit(videoId);
          }
        }, () => '跳过')
      ])
    ]),
    duration: 10000,
    showClose: true,
    position: 'top-right',
    onClose: () => {
      // 用户关闭通知 = 立即开始处理
      const timers = subtitleNotificationTimers.value.get(videoId);
      if (timers) {
        clearTimeout(timers.timer);
        clearInterval(timers.countdownInterval);
        subtitleNotificationTimers.value.delete(videoId);
      }
      
      // 立即触发处理
      triggerTranscodeHandler(videoId).then(() => {
        ElMessage.info('视频已开始处理');
      }).catch(error => {
        console.error('处理启动失败:', error);
        ElMessage.error('处理启动失败，请稍后重试');
      });
    }
  });
};

/**
 * 处理立即编辑/添加字幕
 * @param {number} videoId - 视频ID
 * @param {object} subtitleInfo - 字幕信息
 */
const handleEditSubtitle = (videoId, subtitleInfo) => {
  // 取消倒计时
  const timers = subtitleNotificationTimers.value.get(videoId);
  if (timers) {
    clearTimeout(timers.timer);
    clearInterval(timers.countdownInterval);
    subtitleNotificationTimers.value.delete(videoId);
  }
  
  // 跳转到字幕编辑器
  router.push({
    path: '/creator/subtitle',
    query: { 
      videoId: videoId,
      mode: 'edit_before_transcode',
      hasSubtitle: subtitleInfo.has_subtitle,
      language: subtitleInfo.subtitle_language || ''
    }
  });
};

/**
 * 处理跳过编辑
 * @param {number} videoId - 视频ID
 */
const handleSkipEdit = async (videoId) => {
  // 取消倒计时
  const timers = subtitleNotificationTimers.value.get(videoId);
  if (timers) {
    clearTimeout(timers.timer);
    clearInterval(timers.countdownInterval);
    subtitleNotificationTimers.value.delete(videoId);
  }
  
  // 立即开始处理
  try {
    await triggerTranscodeHandler(videoId);
    ElMessage.success('视频已开始处理');
  } catch (error) {
    console.error('处理启动失败:', error);
    ElMessage.error('处理启动失败，请稍后重试');
  }
};

/**
 * 触发视频转码处理
 * @param {number} videoId - 视频ID
 */
const triggerTranscodeHandler = async (videoId) => {
  try {
    const response = await apiTriggerTranscode(videoId);
    return response;
  } catch (error) {
    console.error('触发转码失败:', error);
    throw error;
  }
};

// ==================== 字幕编辑引导功能结束 ====================

const resetForm = () => {
  if (videoPreviewUrl.value) {
    URL.revokeObjectURL(videoPreviewUrl.value);
  }
  
  videoForm.title = '';
  videoForm.description = '';
  videoForm.tags = [];
  videoForm.category_id = null;
  selectedFile.value = null;
  uploadProgress.value = 0;
  generatedCovers.value = [null, null, null, null];
  selectedCoverIndex.value = 0;
  videoPreviewUrl.value = '';
  videoDuration.value = 0;
  videoAspectRatio.value = '';
  
  // 重置字幕检测状态
  subtitleDetecting.value = false;
  subtitleInfo.value = null;
  
  // 重置发布设置
  publishSettings.viewPermission = 'public';
  publishSettings.commentPermission = 'all';
  publishSettings.allowDownload = false;
  publishSettings.showInProfile = true;
  publishSettings.enableDanmaku = true;
  publishSettings.enableSchedule = false;
  publishSettings.scheduleTime = null;
  publishSettings.originalType = 'original';
  
  // 清除草稿
  clearDraft();
};

onBeforeUnmount(() => {
  if (videoPreviewUrl.value) {
    URL.revokeObjectURL(videoPreviewUrl.value);
  }
  
  // 停止自动保存
  stopAutoSave();
  
  // 清除防抖定时器
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }
  
  // 清理所有字幕通知的倒计时定时器
  subtitleNotificationTimers.value.forEach(({ timer, countdownInterval }) => {
    clearTimeout(timer);
    clearInterval(countdownInterval);
  });
  subtitleNotificationTimers.value.clear();
});
</script>

<style scoped>
/* 主容器 */
.create-center-wrapper {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100vw;
  height: 100vh;
  background: #f4f5f7;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 顶部导航 */
.top-nav {
  background: #fff;
  border-bottom: 1px solid #e3e5e7;
  flex-shrink: 0;
  z-index: 10;
}

.nav-content {
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.logo {
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: all 0.3s;
}

.logo:hover {
  transform: scale(1.05);
}

.logo-text {
  font-size: 24px;
  font-weight: 700;
  background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.5px;
}

.page-title {
  font-size: 20px;
  font-weight: 500;
  color: #18191c;
  margin: 0;
  padding-left: 24px;
  border-left: 2px solid #e3e5e7;
}

.nav-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* 草稿保存状态 */
.draft-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 12px;
  height: 32px;
  background: #f0fdf4;
  border-radius: 4px;
  font-size: 13px;
  color: #16a34a;
}

.draft-status .is-loading {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.draft-status .success-icon {
  color: #16a34a;
}

.status-text {
  font-weight: 500;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 草稿按钮 */
.draft-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 16px;
  height: 36px;
  border-radius: 4px;
  font-size: 14px;
  border: 1px solid #e3e5e7;
  background: #fff;
  color: #61666d;
  transition: all 0.3s;
  position: relative;
}

.draft-btn:hover {
  border-color: #8b5cf6;
  color: #8b5cf6;
  background: #faf5ff;
}

.draft-badge {
  position: absolute;
  top: 6px;
  right: 6px;
}

:deep(.el-badge__content.is-dot) {
  background-color: #f59e0b;
  border: 2px solid #fff;
}

.dashboard-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 20px;
  height: 36px;
  border-radius: 4px;
  font-size: 14px;
  border: 1px solid #e3e5e7;
  background: #fff;
  color: #61666d;
  transition: all 0.3s;
}

.dashboard-btn:hover {
  border-color: #8b5cf6;
  color: #8b5cf6;
  background: #faf5ff;
}

.record-btn {
  background: #8b5cf6;
  border: none;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 20px;
  height: 36px;
  border-radius: 4px;
  font-size: 14px;
  transition: all 0.3s;
}

.record-btn:hover {
  background: #7c3aed;
  transform: translateX(4px);
}

.btn-arrow {
  font-size: 16px;
  transition: transform 0.3s;
}

.record-btn:hover .btn-arrow {
  transform: translateX(4px);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 20px;
  height: 36px;
  border-radius: 4px;
  font-size: 14px;
  border: 1px solid #e3e5e7;
  background: #fff;
  color: #61666d;
  transition: all 0.3s;
}

.back-btn:hover {
  border-color: #8b5cf6;
  color: #8b5cf6;
  background: #fff;
  transform: translateX(-4px);
}

/* 主容器 */
.main-container {
  flex: 1;
  overflow: hidden;
  position: relative;
}

/* 滑动容器 */
.slider-wrapper {
  display: flex;
  height: 100%;
  width: 200%;
  transition: transform 1.2s cubic-bezier(0.19, 1, 0.22, 1);
  will-change: transform;
}

.slide-page {
  width: 50%;
  height: 100%;
  flex-shrink: 0;
}

/* 上传页面 */
.upload-page {
  background: #f4f5f7;
}

.upload-container {
  width: 100%;
  height: 100%;
  background: #fff;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.upload-wrapper {
  flex: 1;
  display: grid;
  grid-template-columns: 1.7fr 1fr;
  overflow: hidden;
  gap: 0;
}

/* 左侧上传区 */
.upload-area {
  background: #fafafa;
  display: flex;
  flex-direction: column;
  padding: 32px;
  border-right: 1px solid #e3e5e7;
  overflow: hidden;
}

/* 右侧表单区 */
.form-area {
  padding: 28px 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #fafbfc 0%, #ffffff 100%);
}

.video-form {
  width: 100%;
}

/* 表单项样式 */
:deep(.el-form-item) {
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
}

:deep(.el-form-item__content) {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  margin-left: 0 !important;
}

:deep(.el-form-item__label) {
  font-size: 14px;
  color: #18191c;
  font-weight: 600;
  line-height: 22px;
  padding-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

:deep(.el-form-item__label::before) {
  content: '';
  width: 3px;
  height: 14px;
  background: linear-gradient(180deg, #8b5cf6 0%, #7c3aed 100%);
  border-radius: 2px;
  margin-right: 2px;
}

/* 输入框样式 */
:deep(.el-input__wrapper) {
  border-radius: 6px;
  border: 1.5px solid #e3e5e7;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
  padding: 8px 12px;
  background: #fff;
  transition: all 0.2s;
  /* min-height: 38px; */
}

:deep(.el-input__wrapper:hover) {
  border-color: #8b5cf6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.05);
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #8b5cf6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
}

:deep(.el-input__inner) {
  font-size: 14px;
  color: #18191c;
  line-height: 22px;
  font-weight: 400;
}

:deep(.el-input__inner::placeholder) {
  color: #9ca3af;
  font-size: 13px;
}

/* 文本域样式 */
:deep(.el-textarea__inner) {
  border-radius: 6px;
  border: 1.5px solid #e3e5e7;
  padding: 10px 12px;
  font-size: 14px;
  color: #18191c;
  font-family: inherit;
  resize: vertical;
  transition: all 0.2s;
  line-height: 1.6;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
}

:deep(.el-textarea__inner:hover) {
  border-color: #8b5cf6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.05);
}

:deep(.el-textarea__inner:focus) {
  border-color: #8b5cf6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
}

:deep(.el-textarea__inner::placeholder) {
  color: #9ca3af;
  font-size: 13px;
}

/* 字数统计 */
:deep(.el-input__count) {
  color: #9ca3af;
  font-size: 12px;
  background: rgba(255, 255, 255, 0.9);
  padding: 2px 6px;
  border-radius: 4px;
}

:deep(.el-textarea .el-input__count) {
  background: rgba(255, 255, 255, 0.9);
  bottom: 8px;
  right: 12px;
}

/* 下拉选择器 */
:deep(.el-select) {
  width: 100%;
}

:deep(.el-select .el-input__wrapper) {
  cursor: pointer;
}

:deep(.el-select .el-input__inner) {
  cursor: pointer;
}

/* 标签输入 */
.tag-form-item {
  margin-bottom: 16px;
}

.tag-container {
  width: 100%;
  max-width: 100%;
}

.tag-wrapper {
  border: 1px solid #e3e5e7;
  border-radius: 6px;
  padding: 8px;
  background: #fff;
  transition: all 0.2s;
  min-height: 42px;
  max-height: 200px;
  overflow-y: auto;
  position: relative;
  width: 100%;
  box-sizing: border-box;
}

.tag-wrapper:hover {
  border-color: #8b5cf6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.05);
}

.tag-wrapper:focus-within {
  border-color: #8b5cf6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
}

/* 自定义滚动条 */
.tag-wrapper::-webkit-scrollbar {
  width: 6px;
}

.tag-wrapper::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.tag-wrapper::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.tag-wrapper::-webkit-scrollbar-thumb:hover {
  background: #8b5cf6;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  padding-right: 60px;
}

.tag-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  align-items: center;
  background: #fff;
  padding: 2px;
  border-radius: 4px;
}

.tag-chip {
  display: inline-flex;
  align-items: center;
  height: 26px;
  padding: 0 12px;
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  border-radius: 13px;
  font-size: 12px;
  color: #fff;
  gap: 6px;
  transition: all 0.2s;
  flex-shrink: 0;
  box-shadow: 0 2px 4px rgba(139, 92, 246, 0.2);
}

.tag-chip:hover {
  background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(139, 92, 246, 0.3);
}

.tag-remove {
  cursor: pointer;
  font-size: 16px;
  color: rgba(255, 255, 255, 0.8);
  line-height: 1;
  transition: all 0.2s;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
}

.tag-remove:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.35);
  transform: scale(1.15);
}

.tag-input-field {
  flex: 1;
  min-width: 140px;
  height: 26px;
  border: none;
  outline: none;
  background: transparent;
  font-size: 13px;
  color: #18191c;
}

.tag-input-field::placeholder {
  color: #9499a0;
  font-size: 12px;
}

.tag-input-field:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.tag-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
  padding: 8px 12px;
  background: linear-gradient(135deg, #faf5ff 0%, #f3f4f6 100%);
  border-radius: 6px;
  border: 1px solid #e3e5e7;
  width: 100%;
  box-sizing: border-box;
}

.tag-count {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 600;
  color: #8b5cf6;
  padding: 4px 10px;
  background: #fff;
  border-radius: 12px;
  transition: all 0.2s;
  border: 1px solid #e3e5e7;
}

.count-icon {
  font-size: 14px;
}

.tag-count-warning {
  color: #f59e0b;
  border-color: #fbbf24;
  background: #fffbeb;
}

.tag-count-full {
  color: #ef4444;
  border-color: #f87171;
  background: #fef2f2;
}

.tag-tip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #6b7280;
}

.tip-icon {
  font-size: 14px;
  color: #9ca3af;
}

.clear-tags-btn {
  font-size: 11px;
  padding: 4px 8px;
  height: 24px;
  display: flex;
  align-items: center;
  gap: 3px;
  transition: all 0.2s;
  border-radius: 4px;
}

.clear-tags-btn:hover {
  background: #fee2e2;
}

.clear-tags-btn .el-icon {
  font-size: 12px;
}

/* 底部按钮 */
.form-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 24px;
  margin-top: 24px;
  border-top: 2px solid #f3f4f6;
}

/* 发布设置样式 */
.publish-settings-item {
  margin-bottom: 24px;
}

.settings-collapse {
  border: none;
  border-radius: 0;
  background: transparent;
  overflow: hidden;
  width: 100%;
  box-sizing: border-box;
}

:deep(.el-collapse) {
  width: 100%;
  box-sizing: border-box;
}

:deep(.el-collapse-item__header) {
  background: transparent;
  border: none;
  padding: 16px 0;
  font-size: 14px;
  color: #18191c;
  transition: all 0.2s;
  width: 100%;
  box-sizing: border-box;
}

:deep(.el-collapse-item__header:hover) {
  background: transparent;
}

:deep(.el-collapse-item__wrap) {
  border: none;
  background: transparent;
}

:deep(.el-collapse-item__content) {
  padding: 0 0 20px;
}

.collapse-title {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.title-icon {
  font-size: 18px;
  color: #8b5cf6;
}

.title-tip {
  font-size: 12px;
  color: #9ca3af;
  font-weight: 400;
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.setting-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #fafbfc;
  border-radius: 6px;
  border: 1px solid #e3e5e7;
  transition: all 0.2s;
}

.setting-row:hover {
  border-color: #8b5cf6;
  background: #faf5ff;
}

.setting-label {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 100px;
  font-size: 14px;
  font-weight: 500;
  color: #18191c;
  flex-shrink: 0;
}

.setting-label .el-icon {
  font-size: 16px;
  color: #8b5cf6;
}

.setting-control {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

:deep(.el-radio-group) {
  display: flex;
  gap: 16px;
}

:deep(.el-radio) {
  margin-right: 0;
}

:deep(.el-radio__label) {
  font-size: 14px;
  color: #61666d;
  padding-left: 8px;
}

:deep(.el-radio__input.is-checked + .el-radio__label) {
  color: #8b5cf6;
}

:deep(.el-radio__input.is-checked .el-radio__inner) {
  background-color: #8b5cf6;
  border-color: #8b5cf6;
}

.setting-switches {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
}

.switch-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #fff;
  border-radius: 4px;
  border: 1px solid #e3e5e7;
  transition: all 0.2s;
}

.switch-item:hover {
  border-color: #8b5cf6;
  background: #faf5ff;
}

.switch-label {
  font-size: 13px;
  color: #61666d;
}

:deep(.el-switch) {
  --el-switch-on-color: #8b5cf6;
}

.schedule-switch {
  flex-shrink: 0;
}

.schedule-picker {
  flex: 1;
  max-width: 280px;
}

:deep(.el-date-editor) {
  width: 100%;
}

:deep(.el-date-editor .el-input__wrapper) {
  border-radius: 4px;
  border: 1px solid #e3e5e7;
  box-shadow: none;
  padding: 8px 12px;
  background: #fff;
  transition: all 0.2s;
}

:deep(.el-date-editor .el-input__wrapper:hover) {
  border-color: #8b5cf6;
}

:deep(.el-date-editor .el-input__wrapper.is-focus) {
  border-color: #8b5cf6;
  box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.1);
}

/* 底部按钮 */
.form-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 24px;
  margin-top: 24px;
  border-top: 1px solid #e3e5e7;
}

:deep(.el-button) {
  height: 38px;
  padding: 0 24px;
  font-size: 14px;
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.2s;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.btn-cancel {
  border: 1.5px solid #e3e5e7;
  background: #fff;
  color: #61666d;
}

.btn-cancel:hover {
  border-color: #8b5cf6;
  color: #8b5cf6;
  background: #faf5ff;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(139, 92, 246, 0.15);
}

.btn-submit {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  border: none;
  color: #fff;
  min-width: 120px;
}

.btn-submit:hover {
  background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

.btn-submit:active {
  background: linear-gradient(135deg, #6d28d9 0%, #5b21b6 100%);
  transform: translateY(0);
}

/* 录制页面 */
.record-page {
  background: #f4f5f7;
}

.record-container {
  width: 100%;
  height: 100%;
  background: #fff;
  padding: 24px;
  overflow: auto;
}



/* 响应式 */
@media screen and (max-width: 1400px) {
  .upload-wrapper {
    grid-template-columns: minmax(500px, 1fr) 1fr;
  }
}

/* 字幕通知样式 */
:deep(.subtitle-notification-content) {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

:deep(.subtitle-notification-content p) {
  line-height: 1.6;
}

/* 倒计时提示动画 */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.8;
  }
}

/* 响应式 */
@media screen and (max-width: 1400px) {
  .upload-wrapper {
    grid-template-columns: minmax(500px, 1fr) 1fr;
  }
}

@media screen and (max-width: 1200px) {
  .upload-wrapper {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }

  .upload-area {
    border-right: none;
    border-bottom: 1px solid #e3e5e7;
    height: calc((100vw - 80px) * 9 / 16);
    max-height: 50vh;
    min-height: 350px;
  }
}

@media screen and (max-width: 768px) {
  .nav-content {
    padding: 0 16px;
  }

  .nav-left {
    gap: 12px;
  }

  .logo-text {
    font-size: 20px;
  }

  .page-title {
    font-size: 16px;
    padding-left: 12px;
  }

  .form-area {
    padding: 24px 20px;
  }

  .upload-area {
    padding: 24px;
    height: calc((100vw - 48px) * 9 / 16);
    max-height: 40vh;
    min-height: 280px;
  }
  
  .record-btn,
  .back-btn,
  .dashboard-btn,
  .draft-btn {
    font-size: 13px;
    padding: 0 16px;
  }
  
  .dashboard-btn span {
    display: none;
  }
  
  .draft-status {
    display: none;
  }
  
  .draft-btn span {
    display: none;
  }
}
</style>
