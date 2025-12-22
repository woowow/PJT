<template>
  <div class="search-page">

    <!-- 🔵 상단 검색창 -->
    <div class="search-box">
      <input 
        v-model="keywordInput"
        type="text"
        placeholder="검색어 입력"
        class="search-input"
        @keyup.enter="searchAgain"
      />
      <img 
        src="@/assets/search-icon.png" 
        class="search-icon"
        @click="searchAgain"
      />
    </div>

    <!-- 🔵 검색 조건 표시 -->
    <div class="query-info">
      <p><strong>키워드:</strong> {{ queryState.keyword || "-" }}</p>
      <p><strong>주제:</strong> {{ queryState.subject || "-" }}</p>
      <p><strong>국가:</strong> {{ queryState.country || "-" }}</p>
    </div>

    <hr />

    <div v-if="loading">검색 중...</div>

    <div v-else-if="paginatedPapers.length > 0" class="results">
      <PaperCard
        v-for="paper in papers"
        :key="paper.id"
        :paper="paper"
        @favoriteChanged="onFavoriteChanged"
      />
    </div>

    <div v-else class="no-result">
      검색 결과가 없습니다.
    </div>

    <!-- 🔵 페이지네이션 -->
    <div class="pagination" v-if="papers.length > pageSize">
      <button :disabled="page === 1" @click="page--">◀ 이전</button>
      <span>{{ page }} / {{ totalPages }}</span>
      <button :disabled="page === totalPages" @click="page++">다음 ▶</button>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import PaperCard from "@/components/PaperCard.vue";
import api from "@/api";

const route = useRoute();
const router = useRouter();

/* -------------------------------
  Query State
-------------------------------- */
const queryState = computed(() => ({
  keyword: route.query.keyword || "",
  subject: route.query.subject || "",
  country: route.query.country || "",
  year_from: route.query.year_from || "",
  year_to: route.query.year_to || "",
  sort: route.query.sort || "",
}));

const keywordInput = ref(queryState.value.keyword);

/* -------------------------------
  State
-------------------------------- */
const papers = ref([]);
const loading = ref(false);

/* -------------------------------
  Pagination
-------------------------------- */
const page = ref(1);
const pageSize = 10;

const onFavoriteChanged = () => {
  // 아무것도 안 해도 OK
  // MyPage → 즐겨찾기 탭으로 가면 ReadingBoard가 새로 mount됨
};

const totalPages = computed(() =>
  Math.ceil(papers.value.length / pageSize)
);

const paginatedPapers = computed(() => {
  const start = (page.value - 1) * pageSize;
  return papers.value.slice(start, start + pageSize);
});

/* -------------------------------
  Fetch Papers (🔥 핵심 수정 지점)
-------------------------------- */
const fetchPapers = async () => {
  loading.value = true;

  const isAdvanced =
    !!queryState.value.subject ||
    !!queryState.value.country ||
    !!queryState.value.year_from ||
    !!queryState.value.year_to ||
    !!queryState.value.sort;

  try {
    const res = isAdvanced
      ? await api.get("/papers/search/advanced/", {
          params: route.query,
        })
      : await api.get("/papers/", {
          params: { keyword: queryState.value.keyword },
        });

    // ✅ PaperCard가 기대하는 구조 그대로 전달
    papers.value = res.data.map(p => ({
      id: p.id,
      title: p.title || "(제목 없음)",
      authors: p.authors || [],          // ⭐ 핵심
      year: p.year || "-",
      citation: p.citation ?? 0,
      institution: p.institution || "-",
      subject: p.subject || "-",
      country: p.country || "-"
    }));

    page.value = 1;
  } catch (err) {
    console.error(err);
    papers.value = [];
  } finally {
    loading.value = false;
  }
};

watch(
  () => route.query,
  fetchPapers,
  { immediate: true }
);

/* -------------------------------
  Re-search (단순 검색)
-------------------------------- */
const searchAgain = () => {
  router.push({
    name: "search",
    query: {
      keyword: keywordInput.value,
    },
  });
};

const checkBookmarked = (paperId) => {
  return false;
};

const toggleBookmark = (paperId) => {
  alert("북마크 기능은 아직 구현 중입니다");
};
</script>

<style scoped>
.search-page {
  padding: 40px;
  max-width: 900px;
  margin: auto;
}

.search-box {
  width: 100%;
  background: #f5f7fb;
  border-radius: 35px;
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 25px;
  margin-bottom: 25px;
}

.search-input {
  flex: 1;
  border: none;
  background: none;
  font-size: 18px;
  outline: none;
}

.search-icon {
  width: 26px;
  cursor: pointer;
}

.results {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.no-result {
  margin-top: 50px;
  text-align: center;
  color: #777;
  font-size: 18px;
}

.pagination {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin: 30px 0;
}
</style>
