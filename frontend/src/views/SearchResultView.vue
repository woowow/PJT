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
      <p><strong>기간:</strong> {{ periodLabel }}</p>
      <p><strong>정렬:</strong> {{ sortLabel }}</p>
    </div>

    <hr />

    <div v-if="loading">검색 중...</div>

    <div v-else-if="paginatedPapers.length > 0" class="results">
      <PaperCard
        v-for="paper in paginatedPapers"
        :key="paper.id"
        :paper="paper"
        @favoriteChanged="onFavoriteChanged"
      />
    </div>

    <div v-else class="no-result">검색 결과가 없습니다.</div>

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
  ✅ HomeView 레거시(from/to, sortCitation 등) fallback 지원
-------------------------------- */
const queryState = computed(() => {
  const q = route.query;

  const keyword = q.keyword || "";

  const subject = q.subject || q.category_name || "";

  const country = q.country || q.country_code || "";

  // ✅ fallback: from/to -> year_from/year_to
  const year_from = q.year_from || q.from || "";
  const year_to = q.year_to || q.to || "";

  // ✅ fallback: sort 없으면 sortCitation/sortRecent 체크박스 기반으로 추론
  let sort = q.sort || "";
  if (!sort) {
    const sortCitation = q.sortCitation === "true" || q.sortCitation === true;
    const sortRecent = q.sortRecent === "true" || q.sortRecent === true;
    sort = sortCitation ? "citation" : (sortRecent ? "recent" : "recent");
  }
  if (sort !== "citation") sort = "recent"; // 값 방어

  return { keyword, subject, country, year_from, year_to, sort };
});

const keywordInput = ref(queryState.value.keyword);

/* 표시용 라벨 */
const periodLabel = computed(() => {
  const yf = queryState.value.year_from;
  const yt = queryState.value.year_to;
  if (!yf && !yt) return "-";
  return `${yf || "?"} ~ ${yt || "?"}`;
});

const sortLabel = computed(() => {
  return queryState.value.sort === "citation" ? "인용순" : "최신순";
});

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

const onFavoriteChanged = () => {};

const totalPages = computed(() => Math.ceil(papers.value.length / pageSize));

const paginatedPapers = computed(() => {
  const start = (page.value - 1) * pageSize;
  return papers.value.slice(start, start + pageSize);
});

/* -------------------------------
  Fetch Papers (advanced로 통일)
-------------------------------- */
const fetchPapers = async () => {
  loading.value = true;

  try {
    const res = await api.get("/papers/search/advanced/", {
      params: {
        keyword: queryState.value.keyword,
        subject: queryState.value.subject,
        country: queryState.value.country,
        year_from: queryState.value.year_from,
        year_to: queryState.value.year_to,
        sort: queryState.value.sort,
      },
    });

    const arr = Array.isArray(res.data) ? res.data : [];

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
watch(() => route.query, fetchPapers, { immediate: true });

/* route 쿼리 바뀔 때 input도 동기화 */
watch(
  () => queryState.value.keyword,
  (v) => {
    keywordInput.value = v;
  }
);

/* -------------------------------
  Re-search
-------------------------------- */
const searchAgain = () => {
  router.push({
    name: "search",
    query: {
      ...route.query,
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
