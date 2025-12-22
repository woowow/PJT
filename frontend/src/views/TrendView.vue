<template>
  <div class="trend-page">
    <h1 class="page-title">Trends</h1>

    <!-- 🔥 Hot Topics -->
    <section class="hot-topic-section">
      <h2 class="section-title">🔥 Hot Topics</h2>

      <div class="topic-card-container">
        <div
          v-for="t in hotTopics"
          :key="t.rank"
          class="topic-card"
          :style="{ background: t.bg }"
          role="button"
          tabindex="0"
          @click="goTopic(t)"
          @keyup.enter="goTopic(t)"
        >
          <div class="topic-rank">{{ t.rank }}.</div>
          <div class="topic-name">{{ t.name }}</div>
          <div class="topic-trend">Hot Score {{ t.cnt }}(pt)</div>
        </div>

        <div v-if="!hotTopics.length" class="empty-topics">
          아직 집계 데이터가 없습니다. (논문 상세보기/즐겨찾기 후 집계됩니다)
        </div>
      </div>
    </section>

    <!-- 🏆 Hot Papers -->
    <section class="hot-paper-section">
      <h2 class="section-title">🏆 Hot Papers (This Week's Most Watched)</h2>

      <div class="paper-list">
        <PaperCard
          v-for="p in hotPapers"
          :key="p.id"
          :paper="p"
        />
      </div>

      <div v-if="!hotPapers.length" class="empty-papers">
        아직 집계 데이터가 없습니다.
      </div>

      <!-- More -->
      <div v-if="hotPapers.length" class="more-wrap">
        <button
          class="more-btn"
          @click="loadMorePapers"
          :disabled="loadingMorePapers || !papersHasMore"
        >
          {{ !papersHasMore ? "No more" : (loadingMorePapers ? "Loading..." : "More") }}
        </button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import PaperCard from "@/components/PaperCard.vue";
import api from "@/api";

const router = useRouter();

const hotTopics = ref([]);
const hotPapers = ref([]);

const topicLimit = ref(3);
const paperLimit = ref(5);

const loadingMorePapers = ref(false);
const papersHasMore = ref(true);

const topicBackgrounds = [
  "linear-gradient(135deg, #ffe1df, #fce4bd)",
  "linear-gradient(135deg, #e0f7ff, #c7f5d9)",
  "linear-gradient(135deg, #e3e8ff, #f0f4ff)",
  "linear-gradient(135deg, #f1f5f9, #e2e8f0)",
  "linear-gradient(135deg, #fef9c3, #fde68a)",
];

const fetchHotTopics = async () => {
  try {
    const res = await api.get(`/trend/topics/?limit=${topicLimit.value}`);
    hotTopics.value = (Array.isArray(res.data) ? res.data : []).map((row, idx) => ({
      rank: idx + 1,
      id: row.category_id,
      name: row.category_name,
      cnt: row.total_cnt,
      bg: topicBackgrounds[idx % topicBackgrounds.length],
    }));
  } catch (e) {
    console.warn("trend topics failed:", e);
    hotTopics.value = [];
  }
};

const fetchHotPapers = async () => {
  try {
    const res = await api.get(`/trend/papers/?limit=${paperLimit.value}`);
    const arr = Array.isArray(res.data) ? res.data : [];
    hotPapers.value = arr;

    // limit보다 적게 오면 더 이상 없음
    papersHasMore.value = arr.length >= paperLimit.value;
  } catch (e) {
    console.warn("trend papers failed:", e);
    hotPapers.value = [];
    papersHasMore.value = false;
  }
};

const loadMorePapers = async () => {
  if (loadingMorePapers.value || !papersHasMore.value) return;

  loadingMorePapers.value = true;
  try {
    paperLimit.value += 5;
    await fetchHotPapers();
  } finally {
    loadingMorePapers.value = false;
  }
};

const goTopic = (t) => {
  // ✅ 백엔드 advanced search는 subject(=category_name)로 필터링하므로
  //    topic.name을 subject로 넘기면 바로 해당 토픽 결과로 이동 가능
  router.push({
    name: "search",
    query: {
      subject: t.name,
      // 필요하면 여기서 sort: "recent" 같은 것도 같이 보낼 수 있음
    },
  });
};

onMounted(async () => {
  await fetchHotTopics();
  await fetchHotPapers();
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
  flex-wrap: wrap;
}

.topic-card {
  flex: 1;
  min-width: 180px;
  padding: 18px 20px;
  border-radius: 16px;
  background: #f4f4f4;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  transition: 0.2s;
  cursor: pointer;
  user-select: none;
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

.empty-topics {
  font-size: 14px;
  color: #6b7280;
}

/* ================= Hot Papers =============== */
.paper-list {
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
}

.empty-papers {
  margin-top: 10px;
  font-size: 14px;
  color: #6b7280;
}

.more-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}

.more-btn {
  padding: 10px 16px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  background: white;
  cursor: pointer;
  font-weight: 600;
}

.more-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
