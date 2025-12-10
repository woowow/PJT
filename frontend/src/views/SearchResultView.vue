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
      <p><strong>키워드:</strong> {{ query.keyword || "-" }}</p>
      <p><strong>주제:</strong> {{ query.subject || "-" }}</p>
      <p><strong>국가:</strong> {{ query.country || "-" }}</p>
    </div>

    <hr />

    <!-- 🔵 검색 결과 리스트 -->
    <div v-if="paginatedPapers.length > 0" class="results">
      <PaperCard
        v-for="item in paginatedPapers"
        :key="item.id"
        :paper="item"
        :isBookmarked="isBookmarked(item.id)"
        @toggleBookmark="toggleBookmark(item.id)"
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
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";

import PaperCard from "@/components/PaperCard.vue";
import ProfileIcon from "@/components/ProfileIcon.vue";

/* -------------------------------
    🔵 QUERY 파싱
-------------------------------- */
const route = useRoute();
const router = useRouter();

const query = {
  keyword: route.query.keyword || "",
  subject: route.query.subject || "",
  country: route.query.country || "",
};

/* -------------------------------
    🔵 검색창 v-model
-------------------------------- */
const keywordInput = ref(query.keyword);

/* -------------------------------
    🔵 더미 데이터 (나중에 백엔드 연결)
-------------------------------- */
const papers = ref([]);

/* -------------------------------
    🔵 페이지네이션
-------------------------------- */
const page = ref(1);
const pageSize = 10;

const totalPages = computed(() => Math.ceil(papers.value.length / pageSize));

const paginatedPapers = computed(() => {
  const start = (page.value - 1) * pageSize;
  return papers.value.slice(start, start + pageSize);
});

/* -------------------------------
    🔵 즐겨찾기 (localStorage 저장)
-------------------------------- */
const bookmarks = ref(JSON.parse(localStorage.getItem("bookmarks") || "[]"));

const isBookmarked = (id) => bookmarks.value.includes(id);

const toggleBookmark = (id) => {
  if (bookmarks.value.includes(id)) {
    bookmarks.value = bookmarks.value.filter((x) => x !== id);
  } else {
    bookmarks.value.push(id);
  }
  localStorage.setItem("bookmarks", JSON.stringify(bookmarks.value));
};

/* -------------------------------
    🔵 다시 검색 기능
-------------------------------- */
const searchAgain = () => {
  router.push({
    path: "/search",
    query: { keyword: keywordInput.value }
  });
};

/* -------------------------------
    🔵 더미 데이터 로딩
-------------------------------- */
onMounted(() => {
  papers.value = [
    { id: 1, title: "Dummy Paper for AI", author: "John Doe", year: 2023, citation: 42, institution: "MIT" },
    { id: 2, title: "Another Example Paper", author: "Alice Johnson", year: 2021, citation: 15, institution: "Stanford" },
    { id: 3, title: "Research Study Example", author: "Lee Seungwoo", year: 2022, citation: 88, institution: "KAIST" },
    // 테스트 위해 10개 이상 넣어도 OK
  ];
});
</script>



<style scoped>
/* 전체 페이지 */
.search-page {
  padding: 40px;
  max-width: 900px;
  margin: auto;
  position: relative;
}

/* 🔵 검색창 */
.search-box {
  width: 100%;
  background: #f5f7fb;
  border-radius: 35px;
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 25px;
  margin-bottom: 25px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
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
  opacity: 0.75;
}

/* 검색 조건 */
.query-info {
  margin: 10px 0 20px 0;
  line-height: 1.6;
}

/* 검색 결과 */
.results {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* 결과 없음 */
.no-result {
  margin-top: 50px;
  text-align: center;
  color: #777;
  font-size: 18px;
}

/* 페이지네이션 */
.pagination {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin: 30px 0;
}

.pagination button {
  padding: 8px 18px;
  border-radius: 8px;
  border: none;
  background: black;
  color: white;
  cursor: pointer;
}

.pagination button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
