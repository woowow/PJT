<template>
  <div class="recommend-page">
    <header class="theme-header">
      <p class="user-greeting">✨ {{ userName }}님의 활동 기반 맞춤형 인텔리전스 추천</p>
      <h1 class="selected-theme-title">{{ selectedTopic }}</h1>
    </header>

    <nav class="topic-navigation">
      <button
        v-for="t in interestTopics"
        :key="t"
        class="nav-topic-btn"
        :class="{ active: selectedTopic === t }"
        @click="selectedTopic = t"
      >
        # {{ t }}
      </button>
    </nav>

    <div v-if="!loading" class="recommend-container">
      <section class="rec-section">
        <h2 class="section-title">📚 <span>{{ selectedTopic }}</span> 분야의 기본기를 다지고 싶다면?</h2>
        <div class="card-grid">
          <PaperCard v-for="p in displayedFundamental" :key="p.id" :paper="p" />
        </div>
      </section>

      <section class="rec-section">
        <h2 class="section-title">🔥 <span>{{ selectedTopic }}</span> 분야의 최신 연구 트렌드를 파악하고 싶다면?</h2>
        <div class="card-grid">
          <PaperCard v-for="p in displayedTrend" :key="p.id" :paper="p" />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from "vue";
import axios from "axios";
import PaperCard from "@/components/PaperCard.vue";

const loading = ref(true);
const userName = ref("사용자"); // ✅ 실시간 이름 저장 변수
const allData = ref([]);
const interestTopics = ref([]);
const selectedTopic = ref("");
const displayedFundamental = ref([]);
const displayedTrend = ref([]);

/**
 * 1. 유저 정보 및 관심사 조회 (이름 포함)
 */
const fetchUserInfo = async () => {
  try {
    const guestId = localStorage.getItem("guest_id") || 3;
    const response = await axios.get(`http://localhost:8000/api/guests/${guestId}/`);
    
    // 🔍 확인: 백엔드는 'guestname'이라는 키로 이름을 보내줍니다.
    // response.data.guestname을 userName.value에 대입합니다.
    if (response.data.guestname) {
      userName.value = response.data.guestname;
    } else {
      userName.value = "방문객";
    }
    
    // 관심사 데이터 연동 (동일)
    const topics = [];
    if (response.data.interest_1) topics.push(response.data.interest_1);
    if (response.data.interest_2) topics.push(response.data.interest_2);
    if (response.data.interest_3) topics.push(response.data.interest_3);
    
    interestTopics.value = topics;
    
    // 만약 추천 목록 호출 전이라면 여기서 첫 번째 주제를 설정해줍니다.
    if (topics.length > 0 && !selectedTopic.value) {
      selectedTopic.value = topics[0];
    }

  } catch (error) {
    console.error("유저 정보 로드 실패:", error);
    userName.value = "방문객";
  }
};

/**
 * 2. 추천 논문 데이터 가져오기 (5+5 로직)
 */
const fetchRecommendations = async () => {
  try {
    const guestId = localStorage.getItem("guest_id") || 3;
    const res = await axios.get(`http://localhost:8000/api/recommendations/`, { params: { guest_id: guestId } });
    if (res.data.results) {
      allData.value = res.data.results;
      if (!selectedTopic.value) {
        selectedTopic.value = allData.value[0].category_name;
      }
      updateUI();
    }
  } catch (e) { console.error(e); } finally { loading.value = false; }
};

const updateUI = () => {
  const data = allData.value.find(d => d.category_name === selectedTopic.value);
  if (data) {
    const mapPaper = p => ({
      id: p.paper_id, title: p.title, author: p.author_name || "저자 미상",
      year: p.announcement_date ? new Date(p.announcement_date).getFullYear() : "N/A", 
      citation: p.citation
    });
    displayedFundamental.value = data.fundamental_papers.map(mapPaper);
    displayedTrend.value = data.trend_papers.map(mapPaper);
  }
};

watch(selectedTopic, updateUI);
onMounted(() => {
  fetchUserInfo();
  fetchRecommendations();
});
</script>

<style scoped>
/* 📌 전체 페이지 폭 제한 (가로로 너무 길어지지 않게) */
.recommend-page { width: 100%; max-width: 1000px; margin: auto; padding: 60px 20px; }

/* 📌 헤더: 문구(상) 주제(하) 및 크기 조정 */
.theme-header { text-align: center; margin-bottom: 40px; }
.user-greeting { font-size: 18px; color: #666; margin-bottom: 8px; font-weight: 500; }
.selected-theme-title { font-size: 56px; font-weight: 900; color: #000; letter-spacing: -2px; }

/* 📌 주제 필터 버튼 */
.topic-navigation { display: flex; justify-content: center; gap: 12px; margin-bottom: 60px; }
.nav-topic-btn { 
  padding: 10px 20px; border-radius: 25px; border: 1px solid #ddd; background: #fff;
  cursor: pointer; font-weight: 600; transition: all 0.3s;
}
.nav-topic-btn.active { background: #000; color: #fff; transform: scale(1.05); }

/* 📌 카드 레이아웃: 가로 스크롤 제거 후 2열/3열 그리드 (세로 방향) */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); /* 화면 너비에 맞춰 자동 조절 */
  gap: 20px;
  padding: 10px 0;
}

.rec-section { margin-bottom: 80px; }
.section-title { font-size: 22px; font-weight: 700; margin-bottom: 25px; line-height: 1.4; }
.section-title span { color: #2563eb; text-decoration: underline; text-underline-offset: 4px; }

/* PaperCard 내부는 컴포넌트 내부 스타일을 따르므로, 
   이곳의 그리드 설정만으로도 논문들이 세로로 쌓이게 됩니다. */
</style>