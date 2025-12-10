<template>
  <div class="mypage-wrapper">
    
    <!-- 좌측 사이드바 -->
    <aside class="sidebar">
      <h2 class="sidebar-title">My Page</h2>

      <div 
        class="sidebar-item"
        :class="{ active: activeMenu === 'profile' }"
        @click="activeMenu = 'profile'"
      >
        개인정보 수정
      </div>

      <div 
        class="sidebar-item"
        :class="{ active: activeMenu === 'bookmarks' }"
        @click="activeMenu = 'bookmarks'"
      >
        즐겨찾기한 논문
      </div>

      <div 
        class="sidebar-item"
        :class="{ active: activeMenu === 'topics' }"
        @click="activeMenu = 'topics'"
      >
        관심있는 주제 추천
      </div>
    </aside>


    <!-- 오른쪽 컨텐츠 영역 -->
    <main class="content-area">

      <!-- 1. 개인정보 수정 -->
      <section v-if="activeMenu === 'profile'" class="section">
        <h2 class="section-title">개인정보 수정</h2>

        <div class="profile-card">
          <label>이름</label>
          <input v-model="profile.name" type="text" />

          <label>이메일</label>
          <input v-model="profile.email" type="email" />

          <label>소속 기관</label>
          <input v-model="profile.affiliation" type="text" />

          <button class="save-btn" @click="saveProfile">
            저장하기
          </button>
        </div>
      </section>


      <!-- 2. 즐겨찾기한 논문 -->
      <section v-if="activeMenu === 'bookmarks'" class="section">
        <h2 class="section-title">즐겨찾기한 논문</h2>

        <div v-if="bookmarkedPapers.length === 0" class="empty-box">
          ⭐ 즐겨찾기한 논문이 없습니다.
        </div>

        <div class="paper-grid">
          <div 
            class="paper-card"
            v-for="p in bookmarkedPapers"
            :key="p.id"
          >
            <h3 class="paper-title">{{ p.title }}</h3>
            <p class="paper-meta">{{ p.author }} · {{ p.year }}년 · 인용수 {{ p.citation }}</p>
            <span class="paper-inst">{{ p.institution }}</span>
          </div>
        </div>
      </section>


      <!-- 3. 관심 있는 주제 추천 -->
      <section v-if="activeMenu === 'topics'" class="section">
        <h2 class="section-title">관심있는 주제 기반 추천</h2>

        <p class="sub-desc">최근 자주 본 주제를 기반으로 맞춤 논문을 추천합니다.</p>

        <div v-if="topTopics.length === 0" class="empty-box">
          데이터가 부족해 추천을 생성할 수 없습니다.
        </div>

        <div v-for="topic in topTopics" :key="topic" class="topic-section">
          <h3 class="topic-label"># {{ topic }}</h3>

          <div class="paper-grid">
            <div 
              class="paper-card"
              v-for="p in recommendedPapers[topic]"
              :key="p.id"
            >
              <h3 class="paper-title">{{ p.title }}</h3>
              <p class="paper-meta">{{ p.author }} · {{ p.year }}년 · 인용수 {{ p.citation }}</p>
              <span class="paper-inst">{{ p.institution }}</span>
            </div>
          </div>
        </div>
      </section>

    </main>

  </div>
</template>


<script setup>
import { ref, computed } from "vue";

const activeMenu = ref("profile");

const profile = ref({
  name: "홍길동",
  email: "example@email.com",
  affiliation: "KAIST",
});

const saveProfile = () => {
  alert("프로필이 저장되었습니다! (백엔드 연결 예정)");
};


// 즐겨찾기
const bookmarks = JSON.parse(localStorage.getItem("bookmarks") || "[]");

const dummyPapers = [
  { id: 1, title: "Dummy Paper for AI", author: "John Doe", year: 2023, citation: 42, institution: "MIT", topic: "AI" },
  { id: 2, title: "Another Example Paper", author: "Alice Johnson", year: 2021, citation: 15, institution: "Stanford", topic: "Physics" },
  { id: 3, title: "Research Study Example", author: "Lee Seungwoo", year: 2022, citation: 88, institution: "KAIST", topic: "AI" },
  { id: 4, title: "Deep Learning Trends", author: "Kim Hana", year: 2020, citation: 120, institution: "SNU", topic: "AI" },
  { id: 5, title: "Quantum Computing Intro", author: "Tom Lee", year: 2022, citation: 55, institution: "Cambridge", topic: "Physics" },
];

const bookmarkedPapers = computed(() =>
  dummyPapers.filter((p) => bookmarks.includes(p.id))
);


// 관심 주제 추천
const viewedTopics = JSON.parse(localStorage.getItem("viewedTopics") || "[]");

const topicCount = {};
viewedTopics.forEach(t => {
  topicCount[t] = (topicCount[t] || 0) + 1;
});

const topTopics = computed(() =>
  Object.entries(topicCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([topic]) => topic)
);

const recommendedPapers = {};
topTopics.value.forEach(topic => {
  recommendedPapers[topic] = dummyPapers.filter(p => p.topic === topic).slice(0, 3);
});
</script>


<style scoped>

/* 전체 레이아웃 */
.mypage-wrapper {
  display: flex;
  height: 100vh;
  background: #fafbfe;
  font-family: "Pretendard", sans-serif;
}

/* 사이드바 */
.sidebar {
  width: 240px;
  background: white;
  padding: 30px;
  border-right: 1px solid #eee;
  box-shadow: 2px 0 10px rgba(0,0,0,0.04);
}

.sidebar-title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 30px;
}

.sidebar-item {
  padding: 14px 10px;
  margin-bottom: 6px;
  font-size: 15px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.25s, color 0.25s;
}

.sidebar-item:hover {
  background: #f2f4f8;
}

.sidebar-item.active {
  background: black;
  color: white;
}

/* 메인 영역 */
.content-area {
  flex: 1;
  padding: 45px 60px;
  overflow-y: auto;
}

.section-title {
  font-size: 26px;
  font-weight: 700;
  margin-bottom: 25px;
}

/* 개인정보 카드 */
.profile-card {
  background: white;
  padding: 30px;
  border-radius: 14px;
  box-shadow: 0 4px 14px rgba(0,0,0,0.06);
  max-width: 380px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.profile-card input {
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 10px;
  font-size: 15px;
}

.save-btn {
  margin-top: 14px;
  padding: 12px;
  width: 100%;
  background: black;
  color: white;
  border-radius: 10px;
  cursor: pointer;
}

/* 논문 카드 UI */
.paper-grid {
  margin-top: 20px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
  gap: 18px;
}

.paper-card {
  background: white;
  padding: 22px;
  border-radius: 12px;
  box-shadow: 0 4px 14px rgba(0,0,0,0.05);
  transition: transform 0.2s, box-shadow 0.2s;
}

.paper-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 18px rgba(0,0,0,0.08);
}

.paper-title {
  font-size: 17px;
  font-weight: 600;
  margin-bottom: 6px;
}

.paper-meta {
  font-size: 14px;
  color: #666;
}

.paper-inst {
  font-size: 13px;
  color: #999;
}

/* 관심 주제 */
.topic-section {
  margin-bottom: 45px;
}

.topic-label {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 10px;
}

.sub-desc {
  color: #666;
  margin-bottom: 20px;
}

/* 빈 공간 안내 */
.empty-box {
  background: white;
  padding: 30px;
  border-radius: 12px;
  text-align: center;
  color: #777;
  font-size: 15px;
}
</style>
