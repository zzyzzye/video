<!-- <template>
  <div class="category-nav">
    <div class="category-scroll">
      <div
        v-for="category in categories"
        :key="category.id"
        class="category-item"
        :class="{ active: category.id === activeCategory }"
        @click="handleSelect(category.id)"
      >
        {{ category.name }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  categories: {
    type: Array,
    default: () => []
  },
  activeCategory: {
    type: [Number, String, null],
    default: null
  }
})

const emit = defineEmits(['change'])

const handleSelect = (categoryId) => {
  emit('change', categoryId)
}
</script>

<style scoped>
.category-nav {
  background: #fff;
  border-bottom: 1px solid #e5e5e5;
  position: sticky;
  top: 60px;
  z-index: 100;
  padding: 0 20px;
}

.category-scroll {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 12px 0;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
}

.category-scroll::-webkit-scrollbar {
  display: none; /* Chrome/Safari */
}

.category-item {
  flex-shrink: 0;
  padding: 8px 20px;
  border-radius: 20px;
  background: #f1f2f3;
  color: #333;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

.category-item:hover {
  background: #e3e5e7;
}

.category-item.active {
  background: #00a1d6;
  color: #fff;
}

/* 响应式 */
@media (max-width: 768px) {
  .category-nav {
    padding: 0 12px;
  }

  .category-item {
    padding: 6px 16px;
    font-size: 13px;
  }
}
</style> -->
