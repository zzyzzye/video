/**
 * NSFW 检测标签和说明
 * 与 EVA 模型 README 保持一致
 */

// NSFW 风险等级定义
export const NSFW_LEVELS = {
  neutral: {
    key: 'neutral',
    label: '正常内容',
    shortLabel: '正常',
    color: '#67c23a',
    description: '安全、正常的内容',
    icon: 'CircleCheck'
  },
  low: {
    key: 'low',
    label: '低风险及以上',
    shortLabel: '低风险+',
    color: '#409eff',
    description: '低风险 + 中风险 + 高风险的累积概率（泳装、紧身衣等）',
    icon: 'InfoFilled'
  },
  medium: {
    key: 'medium',
    label: '中风险及以上',
    shortLabel: '中风险+',
    color: '#e6a23c',
    description: '中风险 + 高风险的累积概率（暴露、裸露等）',
    icon: 'Warning'
  },
  high: {
    key: 'high',
    label: '高风险',
    shortLabel: '高风险',
    color: '#f56c6c',
    description: '色情、露骨内容的概率',
    icon: 'WarningFilled'
  }
}

// 审核状态定义
export const MODERATION_STATUS = {
  pending: {
    key: 'pending',
    label: '待审核',
    type: 'info',
    color: '#909399'
  },
  processing: {
    key: 'processing',
    label: '审核中',
    type: 'warning',
    color: '#e6a23c'
  },
  completed: {
    key: 'completed',
    label: '已完成',
    type: 'success',
    color: '#67c23a'
  },
  failed: {
    key: 'failed',
    label: '失败',
    type: 'danger',
    color: '#f56c6c'
  }
}

// 审核结果定义
export const MODERATION_RESULT = {
  safe: {
    key: 'safe',
    label: '安全',
    type: 'success',
    color: '#67c23a',
    suggestion: '通过',
    description: '未检测到问题内容，建议通过该视频'
  },
  unsafe: {
    key: 'unsafe',
    label: '不安全',
    type: 'danger',
    color: '#f56c6c',
    suggestion: '拒绝',
    description: '检测到不安全内容，建议拒绝该视频'
  },
  uncertain: {
    key: 'uncertain',
    label: '不确定',
    type: 'warning',
    color: '#e6a23c',
    suggestion: '人工复审',
    description: '检测结果不确定，建议人工审核'
  }
}

/**
 * 获取风险等级信息
 * @param {string} level - 风险等级 key
 * @returns {object} 风险等级信息
 */
export function getNSFWLevel(level) {
  return NSFW_LEVELS[level] || NSFW_LEVELS.neutral
}

/**
 * 获取审核状态信息
 * @param {string} status - 状态 key
 * @returns {object} 状态信息
 */
export function getModerationStatus(status) {
  return MODERATION_STATUS[status] || MODERATION_STATUS.pending
}

/**
 * 获取审核结果信息
 * @param {string} result - 结果 key
 * @returns {object} 结果信息
 */
export function getModerationResult(result) {
  return MODERATION_RESULT[result] || MODERATION_RESULT.uncertain
}

/**
 * 根据分数获取风险等级
 * @param {number} score - 分数 (0-1)
 * @returns {string} 风险等级 (low/medium/high)
 */
export function getScoreLevelByValue(score) {
  if (score < 0.3) return 'low'
  if (score < 0.7) return 'medium'
  return 'high'
}

/**
 * 根据分数获取颜色
 * @param {number} score - 分数 (0-1)
 * @returns {string} 颜色值
 */
export function getScoreColor(score) {
  if (score < 0.3) return '#67c23a'
  if (score < 0.7) return '#e6a23c'
  return '#f56c6c'
}

/**
 * 格式化分数为百分比
 * @param {number} score - 分数 (0-1)
 * @param {number} decimals - 小数位数
 * @returns {string} 百分比字符串
 */
export function formatScorePercent(score, decimals = 1) {
  return `${(score * 100).toFixed(decimals)}%`
}

/**
 * 获取审核建议
 * @param {number} mediumScore - 中风险及以上分数
 * @returns {object} 建议信息
 */
export function getModerationSuggestion(mediumScore) {
  if (mediumScore >= 0.7) {
    return {
      action: 'reject',
      label: '建议拒绝',
      type: 'danger',
      description: '检测到高风险内容，建议拒绝该视频'
    }
  } else if (mediumScore >= 0.3) {
    return {
      action: 'review',
      label: '建议人工复审',
      type: 'warning',
      description: '检测结果不确定，建议人工审核'
    }
  } else {
    return {
      action: 'approve',
      label: '建议通过',
      type: 'success',
      description: '未检测到明显问题，可以考虑通过'
    }
  }
}

/**
 * 模型说明文本
 */
export const MODEL_DESCRIPTION = {
  title: 'EVA-based Fast NSFW Image Classifier',
  version: 'v1.0',
  description: '基于 EVA 架构的快速 NSFW 图像分类器',
  outputFormat: [
    'neutral: 正常内容的概率',
    'low: 低风险 + 中风险 + 高风险的累积概率',
    'medium: 中风险 + 高风险的累积概率',
    'high: 仅高风险内容的概率'
  ],
  note: '模型返回的是累积概率，每个等级包含该等级及以上的所有风险'
}

/**
 * 审核参数配置
 */
export const MODERATION_PARAMS = {
  thresholdLevel: {
    low: {
      key: 'low',
      label: '低风险及以上（Low+）',
      description: '使用 low 累积概率判断，检测最宽松',
      recommended: false,
      color: '#409eff'
    },
    medium: {
      key: 'medium',
      label: '中风险及以上（Medium+）',
      description: '使用 medium 累积概率判断，推荐使用',
      recommended: true,
      color: '#e6a23c'
    },
    high: {
      key: 'high',
      label: '高风险（High）',
      description: '仅检测高风险内容，最严格',
      recommended: false,
      color: '#f56c6c'
    }
  },
  threshold: {
    min: 0,
    max: 1,
    step: 0.05,
    default: 0.6,
    recommended: [0.6, 0.7],
    description: '当选定级别的概率超过此阈值时，该帧会被标记为问题帧'
  },
  fps: {
    min: 1,
    max: 10,
    step: 1,
    default: 1,
    recommended: [1, 2],
    description: '每秒抽取多少帧进行检测，值越大检测越精细但耗时越长'
  }
}

/**
 * 获取检测级别配置
 * @param {string} level - 检测级别
 * @returns {object} 配置信息
 */
export function getThresholdLevelConfig(level) {
  return MODERATION_PARAMS.thresholdLevel[level] || MODERATION_PARAMS.thresholdLevel.medium
}

