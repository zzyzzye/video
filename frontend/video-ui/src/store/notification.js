import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getToken } from '@/utils/auth'
import { getNotifications, getUnreadNotificationCount, markNotificationAsRead } from '@/api/user'
import { ElNotification } from 'element-plus'
import router from '@/router'

export const useNotificationStore = defineStore('notification', () => {
  const unreadCount = ref(0)
  const recentNotifications = ref([])
  const videoStatusUpdates = ref([]) // 存储视频状态更新
  let ws = null
  let reconnectTimer = null
  let pollTimer = null
  let reconnectAttempts = 0
  const maxReconnectAttempts = 5
  let wsConnected = false
  let isInitialized = false

  // 视频状态更新回调列表
  const videoStatusCallbacks = ref([])

  // 注册视频状态更新回调
  const onVideoStatusUpdate = (callback) => {
    videoStatusCallbacks.value.push(callback)
    // 返回取消注册的函数
    return () => {
      const index = videoStatusCallbacks.value.indexOf(callback)
      if (index > -1) {
        videoStatusCallbacks.value.splice(index, 1)
      }
    }
  }

  // 触发视频状态更新回调
  const triggerVideoStatusUpdate = (videoData) => {
    videoStatusCallbacks.value.forEach(callback => {
      try {
        callback(videoData)
      } catch (e) {
        console.error('视频状态更新回调执行失败:', e)
      }
    })
  }

  // 获取未读消息数量（API 方式）
  const fetchUnreadCount = async () => {
    const token = getToken()
    if (!token) {
      unreadCount.value = 0
      return
    }
    try {
      const res = await getUnreadNotificationCount()
      unreadCount.value = res.count || 0
    } catch (error) {
      console.error('获取未读消息数量失败:', error)
    }
  }

  // 获取最近消息列表
  const fetchRecentNotifications = async () => {
    const token = getToken()
    if (!token) {
      recentNotifications.value = []
      return
    }
    try {
      const res = await getNotifications({ page_size: 5 })
      recentNotifications.value = res || []
    } catch (error) {
      console.error('获取消息列表失败:', error)
    }
  }

  // 建立 WebSocket 连接
  const connectWebSocket = () => {
    const token = getToken()
    if (!token) {
      return
    }
    
    // 已经连接了就不重复连接
    if (ws && ws.readyState === WebSocket.OPEN) {
      return
    }
    
    // 关闭现有连接
    if (ws) {
      ws.close()
    }
    
    const wsUrl = `ws://localhost:8000/ws/notifications/?token=${token}`
    
    try {
      ws = new WebSocket(wsUrl)
      
      ws.onopen = () => {
        reconnectAttempts = 0
        wsConnected = true
        // WebSocket 连接成功，停止轮询
        if (pollTimer) {
          clearInterval(pollTimer)
          pollTimer = null
        }
      }
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          if (data.type === 'unread_count') {
            unreadCount.value = data.count
          } else if (data.type === 'notification') {
            // 收到新通知，更新未读数量
            unreadCount.value++
            
            // 添加到最近消息列表
            recentNotifications.value.unshift({
              id: data.data.id,
              title: data.data.title,
              content: data.data.content,
              source_type: data.data.source_type,
              source_id: data.data.source_id,
              created_at: data.data.created_at,
              read: false
            })
            
            // 保持最多 5 条
            if (recentNotifications.value.length > 5) {
              recentNotifications.value.pop()
            }
            
            // 显示桌面通知
            ElNotification({
              title: data.data.title,
              message: data.data.content,
              type: 'success',
              duration: 5000,
              onClick: () => {
                if (data.data.source_type === 'video' && data.data.source_id) {
                  router.push(`/video/${data.data.source_id}`)
                } else {
                  router.push('/user/message')
                }
              }
            })
          } else if (data.type === 'video_status_update') {
            // 收到视频状态更新
            videoStatusUpdates.value.push(data.data)
            // 触发回调
            triggerVideoStatusUpdate(data.data)
            
            // 显示状态更新提示
            const statusText = {
              'processing': '处理中',
              'pending': '待审核',
              'approved': '已通过',
              'rejected': '未通过',
              'ready': '就绪',
              'failed': '处理失败'
            }
            ElNotification({
              title: '视频状态更新',
              message: `《${data.data.title}》状态已更新为：${statusText[data.data.status] || data.data.status}`,
              type: data.data.status === 'approved' ? 'success' : 
                    data.data.status === 'rejected' || data.data.status === 'failed' ? 'error' : 'info',
              duration: 4000
            })
          }
        } catch (error) {
          console.error('解析 WebSocket 消息失败:', error)
        }
      }
      
      ws.onclose = (event) => {
        ws = null
        wsConnected = false
        
        // 非正常关闭时尝试重连
        const token = getToken()
        if (event.code !== 1000 && token && reconnectAttempts < maxReconnectAttempts) {
          reconnectAttempts++
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000)
          reconnectTimer = setTimeout(connectWebSocket, delay)
        } else if (reconnectAttempts >= maxReconnectAttempts) {
          // 重连失败，降级为轮询
          startPolling()
        }
      }
      
      ws.onerror = (error) => {
        console.error('WebSocket 错误:', error)
      }
    } catch (error) {
      console.error('创建 WebSocket 失败:', error)
      startPolling()
    }
  }

  // 启动轮询（降级方案）
  const startPolling = () => {
    if (pollTimer) return
    fetchUnreadCount()
    pollTimer = setInterval(fetchUnreadCount, 30000)
  }

  // 关闭 WebSocket 连接
  const disconnect = () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
    if (ws) {
      ws.close(1000)
      ws = null
    }
    wsConnected = false
    isInitialized = false
  }

  // 初始化（登录后调用）
  const init = () => {
    if (isInitialized) {
      return
    }
    
    const token = getToken()
    if (!token) {
      return
    }
    
    isInitialized = true
    
    // 先获取一次未读数量
    fetchUnreadCount()
    
    // 尝试建立 WebSocket
    connectWebSocket()
    
    // 如果 2 秒后 WebSocket 还没连上，启动轮询
    setTimeout(() => {
      if (!wsConnected && getToken()) {
        startPolling()
      }
    }, 2000)
  }

  // 重置（登出时调用）
  const reset = () => {
    disconnect()
    unreadCount.value = 0
    recentNotifications.value = []
  }

  // 标记消息已读
  const markAsRead = async (notificationId) => {
    try {
      await markNotificationAsRead(notificationId)
      const notification = recentNotifications.value.find(n => n.id === notificationId)
      if (notification) {
        notification.read = true
      }
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    } catch (error) {
      console.error('标记已读失败:', error)
    }
  }

  return {
    unreadCount,
    recentNotifications,
    videoStatusUpdates,
    fetchUnreadCount,
    fetchRecentNotifications,
    init,
    reset,
    markAsRead,
    disconnect,
    onVideoStatusUpdate
  }
})
