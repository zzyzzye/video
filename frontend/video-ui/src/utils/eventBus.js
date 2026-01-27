import { ref } from 'vue';

// 创建一个简单的事件总线
const bus = ref(new Map());

export function useEventBus() {
  // 注册事件监听器
  function on(event, callback) {
    if (!bus.value.has(event)) {
      bus.value.set(event, []);
    }
    bus.value.get(event).push(callback);
  }

  // 移除事件监听器
  function off(event, callback) {
    if (!bus.value.has(event)) {
      return;
    }
    
    if (!callback) {
      bus.value.delete(event);
      return;
    }
    
    const callbacks = bus.value.get(event);
    const index = callbacks.indexOf(callback);
    if (index !== -1) {
      callbacks.splice(index, 1);
    }
    
    if (callbacks.length === 0) {
      bus.value.delete(event);
    }
  }

  // 触发事件
  function emit(event, ...args) {
    if (!bus.value.has(event)) {
      return;
    }
    
    const callbacks = bus.value.get(event);
    callbacks.forEach(callback => {
      callback(...args);
    });
  }

  return {
    on,
    off,
    emit
  };
} 