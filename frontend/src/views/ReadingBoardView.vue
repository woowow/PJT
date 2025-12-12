<template>
  <div class="reading-page">

    <div class="page-header">
      <h1 class="page-title">연구 진행 보드</h1>
      <p class="page-desc">
        즐겨찾기한 논문과 읽기 상태를 드래그로 관리하세요.
      </p>
    </div>

    <div class="board">
      <ReadingColumn title="⭐ 즐겨찾기" :list="board.bookmark" />
      <ReadingColumn title="📌 읽을 예정" :list="board.todo" />
      <ReadingColumn title="👀 읽는 중" :list="board.reading" />
      <ReadingColumn title="✅ 읽음" :list="board.done" />
    </div>

  </div>
</template>

<script setup>
import { ref } from "vue";
import ReadingColumn from "@/components/ReadingColumn.vue";

/* =========================
   부모가 모든 상태 소유
========================= */
const board = ref({
  bookmark: [
    { id: 1, title: "Attention Is All You Need" },
    { id: 2, title: "Diffusion Models Explained" },
  ],
  todo: [
    { id: 3, title: "Reinforcement Learning Survey" },
  ],
  reading: [
    { id: 4, title: "Efficient LLM Inference" },
  ],
  done: [],
});
</script>

<style scoped>
.reading-page {
  max-width: 1600px;
  margin: auto;
  padding: 40px 20px;
}

.page-title {
  font-size: 26px;
  font-weight: 800;
}

.page-desc {
  margin-top: 6px;
  font-size: 14px;
  color: #666;
}

.board {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-top: 30px;
}
</style>
