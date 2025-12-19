<template>
  <div class="paper-card" @click="goDetail">
    <!-- 제목 -->
    <h3 class="title">
      {{ paper.title }}
    </h3>

    <!-- 메타 정보 -->
    <p class="meta">
      {{ paper.author }} · {{ paper.year }}
    </p>

    <p class="meta">
      인용 수: {{ paper.citation }}
    </p>

    <!-- 북마크 -->
    <button
      class="bookmark-btn"
      @click.stop="emitToggle"
      :aria-label="isBookmarked ? '북마크 해제' : '북마크 추가'"
    >
      {{ isBookmarked ? "★" : "☆" }}
    </button>
  </div>
</template>

<script setup>
import { useRouter } from "vue-router";

/* =========================
   Props
========================= */
const props = defineProps({
  paper: {
    type: Object,
    required: true,
  },
  isBookmarked: {
    type: Boolean,
    default: false,
  },
});

/* =========================
   Emits
========================= */
const emit = defineEmits(["toggleBookmark"]);

const router = useRouter();

/* =========================
   Handlers
========================= */
const goDetail = () => {
  router.push(`/paper/${props.paper.id}`);
};

const emitToggle = () => {
  emit("toggleBookmark");
};
</script>

<style scoped>
/* =========================
   카드 전체
========================= */
.paper-card {
  position: relative;
  padding: 22px 26px;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  background-color: #ffffff;
  cursor: pointer;

  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
  transition: all 0.2s ease;
}

/* Hover 효과 */
.paper-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 26px rgba(0, 0, 0, 0.08);
  border-color: #c7d2fe;
}

/* =========================
   제목
========================= */
.title {
  margin: 0 0 10px 0;
  font-size: 18px;
  font-weight: 600;
  line-height: 1.45;
  color: #111827;
}

.paper-card:hover .title {
  text-decoration: underline;
}

/* =========================
   메타 정보
========================= */
.meta {
  margin: 4px 0;
  font-size: 14px;
  color: #4b5563;
}

/* =========================
   북마크 버튼
========================= */
.bookmark-btn {
  position: absolute;
  top: 18px;
  right: 20px;

  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #f59e0b;

  transition: transform 0.15s ease;
}

.bookmark-btn:hover {
  transform: scale(1.15);
}
</style>
