<template>
  <div class="reading-page">
    <div class="page-header">
      <h1 class="page-title">연구 진행 보드</h1>
      <p class="page-desc">즐겨찾기한 논문을 드래그해서 읽기 상태를 관리하세요.</p>
    </div>

    <div class="board">
      <ReadingColumn
        title="📌 읽을 예정"
        status="TODO"
        :list="board.TODO"
        @changeStatus="updateStatus"
        @refresh="loadFavorites"
      />
      <ReadingColumn
        title="👀 읽는 중"
        status="READING"
        :list="board.READING"
        @changeStatus="updateStatus"
        @refresh="loadFavorites"
      />
      <ReadingColumn
        title="✅ 읽음"
        status="DONE"
        :list="board.DONE"
        @changeStatus="updateStatus"
        @refresh="loadFavorites"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import api from "@/api";
import ReadingColumn from "@/components/ReadingColumn.vue";

const board = ref({
  TODO: [],
  READING: [],
  DONE: [],
});

const normalizeStatus = (s) => (s ?? "").toString().trim().toUpperCase();

const loadFavorites = async () => {
  const guestId = localStorage.getItem("guest_id");
  if (!guestId) {
    board.value.TODO = [];
    board.value.READING = [];
    board.value.DONE = [];
    return;
  }

  // ✅ Django trailing slash 통일
  const res = await api.get(`/favorites/${guestId}/`);
  const data = Array.isArray(res.data) ? res.data : [];

  board.value.TODO = data.filter((p) => normalizeStatus(p.status) === "TODO");
  board.value.READING = data.filter((p) => normalizeStatus(p.status) === "READING");
  board.value.DONE = data.filter((p) => normalizeStatus(p.status) === "DONE");
};

const updateStatus = async (paperId, newStatus) => {
  const guestId = localStorage.getItem("guest_id");
  if (!guestId) return;

  await api.post("/favorites/status/", {
    guest_id: guestId,
    paper_id: paperId,
    status: newStatus,
  });

  await loadFavorites(); // ✅ 서버 기준으로 동기화
};

onMounted(loadFavorites);
</script>

<style scoped>
.reading-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 20px;
}

.page-header {
  margin-bottom: 18px;
}

.page-title {
  font-size: 26px;
  font-weight: 800;
}

.page-desc {
  margin-top: 6px;
  font-size: 14px;
  color: #6b7280;
}

.board {
  display: grid;
  grid-template-columns: repeat(3, minmax(260px, 1fr));
  gap: 18px;
  align-items: start;
}
</style>
