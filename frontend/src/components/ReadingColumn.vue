<template>
  <div class="column">
    <h3 class="column-title">
      {{ title }}
      <span class="count">({{ localList.length }})</span>
    </h3>

    <draggable
      :list="localList"
      :group="{ name: 'papers', pull: true, put: true }"
      item-key="id"
      class="column-list"
      ghost-class="ghost"
      chosen-class="chosen"
      drag-class="drag"
      :animation="160"
      @change="onChange"
    >
      <template #item="{ element }">
        <PaperCard :paper="element" @favoriteChanged="$emit('refresh')" />
      </template>

      <template #footer>
        <div v-if="localList.length === 0" class="empty">
          비어있습니다.
        </div>
      </template>
    </draggable>
  </div>
</template>

<script setup>
import { ref, watch } from "vue";
import draggable from "vuedraggable";
import PaperCard from "@/components/PaperCard.vue";

const props = defineProps({
  title: String,
  list: Array,
  status: String,
});

const emit = defineEmits(["changeStatus", "refresh"]);

const localList = ref([]);

// ✅ 부모 list 변경 시 동기화 (서버 reload 포함)
watch(
  () => props.list,
  (newVal) => {
    localList.value = Array.isArray(newVal) ? [...newVal] : [];
  },
  { immediate: true }
);

const onChange = (evt) => {
  // 다른 컬럼에서 "이 컬럼으로 들어온" 경우만 status 업데이트
  if (evt?.added?.element) {
    const paper = evt.added.element;
    emit("changeStatus", paper.id, props.status);
  }
};
</script>

<style scoped>
.column {
  background: #f6f7fb;
  border: 1px solid #eef0f5;
  border-radius: 14px;
  padding: 14px;
  height: calc(100vh - 220px);
  overflow-y: auto;
}

.column-title {
  font-size: 16px;
  font-weight: 800;
  margin-bottom: 12px;
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.count {
  font-size: 12px;
  color: #6b7280;
  font-weight: 700;
}

.column-list {
  min-height: 240px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.empty {
  padding: 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.7);
  color: #9ca3af;
  font-size: 13px;
  text-align: center;
}

/* 드래그 시 시각 효과 */
.ghost {
  opacity: 0.35;
}
.chosen {
  transform: scale(1.01);
}
.drag {
  opacity: 0.9;
}
</style>
