<template>
  <div class="trend-page">

    <!-- ================================ -->
    <!-- 제목 영역 -->
    <!-- ================================ -->
    <h1 class="page-title">Trends</h1>

    <!-- ================================ -->
    <!-- 🔥 Hot Topics -->
    <!-- ================================ -->
    <section class="hot-topic-section">
      <h2 class="section-title">🔥 Hot Topics</h2>

      <div class="topic-card-container">
        <div 
          v-for="t in hotTopics"
          :key="t.rank"
          class="topic-card"
          :style="{ background: t.bg }"
        >
          <div class="topic-rank">{{ t.rank }}.</div>
          <div class="topic-name">{{ t.name }}</div>
          <div class="topic-trend">{{ t.trend }}</div>
        </div>
      </div>
    </section>

    <!-- ================================ -->
    <!-- 🏆 Hot Papers -->
    <!-- ================================ -->
    <section class="hot-paper-section">
      <h2 class="section-title">🏆 Hot Papers (This Week's Most Cited)</h2>

      <div class="paper-list">
        <PaperCard
          v-for="p in hotPapers"
          :key="p.id"
          :paper="p"
        />
      </div>

      <div class="more-btn">More ></div>
    </section>

  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import PaperCard from "@/components/PaperCard.vue";
import api from "@/api";

/* 🔥 Hot Topics (일단 더미 유지) */
const hotTopics = ref([
  { rank: 1, name: "Generative AI & LLMs", trend: "Trend ↗", bg: "linear-gradient(135deg, #ffe1df, #fce4bd)" },
  { rank: 2, name: "Climate Change Modeling", trend: "Trend ↗", bg: "linear-gradient(135deg, #e0f7ff, #c7f5d9)" },
  { rank: 3, name: "Quantum Computing", trend: "Stable", bg: "linear-gradient(135deg, #e3e8ff, #f0f4ff)" },
]);

/* 🏆 Hot Papers (DB 기반) */
const hotPapers = ref([]);

onMounted(async () => {
  const res = await api.get("/papers/");
  hotPapers.value = res.data
    .sort((a, b) => b.citation - a.citation)
    .slice(0, 3);
});
</script>


<style scoped>
.trend-page {
  width: 100%;
  max-width: 1200px;
  margin: auto;
  padding: 40px 0;
}

/* 제목 */
.page-title {
  font-size: 28px;
  font-weight: 800;
  margin-bottom: 25px;
}

/* 공통 섹션 제목 */
.section-title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 18px;
}

/* ================= Hot Topics =============== */
.topic-card-container {
  display: flex;
  gap: 18px;
  margin-bottom: 50px;
}

.topic-card {
  flex: 1;
  min-width: 180px;
  padding: 18px 20px;
  border-radius: 16px;
  background: #f4f4f4;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  transition: 0.2s;
}

.topic-card:hover {
  transform: translateY(-3px);
}

.topic-rank {
  font-weight: 700;
  font-size: 18px;
  margin-bottom: 5px;
}

.topic-name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}

.topic-trend {
  font-size: 13px;
  color: #444;
}

/* ================= Hot Papers =============== */
.paper-list {
  display: flex;
  gap: 18px;
}

.more-btn {
  margin-top: 14px;
  font-size: 14px;
  color: #666;
  cursor: pointer;
  text-align: right;
}

.more-btn:hover {
  color: #000;
}
</style>
