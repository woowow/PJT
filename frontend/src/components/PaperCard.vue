<template>
  <div class="paper-card" @click="openDetail">
    
    <!-- 즐겨찾기 -->
    <div class="star" @click.stop="emit('toggleBookmark')">
      <span v-if="isBookmarked" class="filled">★</span>
      <span v-else class="empty">☆</span>
    </div>

    <h3 class="title">{{ paper.title }}</h3>
    <p class="meta">
      {{ paper.author }} · {{ paper.year }}년 · 인용수 {{ paper.citation }}
    </p>
    <p class="institution">{{ paper.institution }}</p>
  </div>
</template>

<script setup>
import { useRouter } from "vue-router";

const router = useRouter();

const props = defineProps({
  paper: Object,
  isBookmarked: Boolean
});

const emit = defineEmits(["toggleBookmark"]);

const openDetail = () => {
  router.push(`/paper/${props.paper.id}`);
};
</script>

<style scoped>
.paper-card {
  background: #f5f7fb;
  padding: 20px;
  border-radius: 15px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  cursor: pointer;
  position: relative;
}

/* 별 아이콘 */
.star {
  position: absolute;
  top: 12px;
  right: 15px;
  font-size: 22px;
}

.filled {
  color: gold;
}

.empty {
  color: #bbb;
}
</style>
