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
      <!-- ✅ paginatedPapers를 렌더링해야 페이지네이션이 동작 -->
      <PaperCard
        v-for="paper in paginatedPapers"
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
  - Hot Topics에서 subject로 넘어옴
  - 혹시 다른 이름으로 넘어오는 케이스도 대비해서 fallback 추가
-------------------------------- */
const queryState = computed(() => ({
  keyword: route.query.keyword || "",
  // ✅ Hot Topics: subject로 넘어오게 구현했지만, 혹시 category_name 등으로 넘어와도 표시되게 처리
  subject: route.query.subject || route.query.category_name || "",
  country: route.query.country || route.query.country_code || "",
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
  // nothing (필요하면 여기서 재조회 트리거 가능)
};

const totalPages = computed(() =>
  Math.ceil(papers.value.length / pageSize)
);

const paginatedPapers = computed(() => {
  const start = (page.value - 1) * pageSize;
  return papers.value.slice(start, start + pageSize);
});

/* -------------------------------
  Fetch Papers
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
          params: {
            keyword: queryState.value.keyword,
            subject: queryState.value.subject,
            country: queryState.value.country,
            year_from: queryState.value.year_from,
            year_to: queryState.value.year_to,
            sort: queryState.value.sort,
          },
        })
      : await api.get("/papers/", {
          params: { keyword: queryState.value.keyword },
        });

    const arr = Array.isArray(res.data) ? res.data : [];

    // ✅ PaperCard가 기대하는 구조 그대로 전달
    papers.value = arr.map((p) => ({
      id: p.id,
      title: p.title || "(제목 없음)",
      authors: p.authors || [],
      year: p.year || "-",
      citation: p.citation ?? 0,
      institution: p.institution || "-",
      subject: p.subject || "-",
      country: p.country || "-",
    }));

    page.value = 1;
  } catch (err) {
    console.error(err);
    papers.value = [];
  } finally {
    loading.value = false;
  }
};

/* route.query가 바뀌면 자동 검색 */
watch(
  () => route.query,
  fetchPapers,
  { immediate: true }
);

/* route 쿼리 바뀔 때 input도 동기화 */
watch(
  () => queryState.value.keyword,
  (v) => {
    keywordInput.value = v;
  }
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

.query-info {
  margin-bottom: 10px;
  font-size: 14px;
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
