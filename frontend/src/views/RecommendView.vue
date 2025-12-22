<template>
  <div class="recommend-page">

    <!-- ------------------------------------- -->
    <!-- (0) 관심있는 주제 기반 추천 (MyPage에서 이동) -->
    <!-- ------------------------------------- -->
    <section class="interest-wrapper">
      <h2 class="interest-title">관심있는 주제 기반 추천</h2>
      <div class="interest-desc">
        아래 관심 Topic 필터를 기준으로 추천을 제공할 예정입니다.
      </div>

      <div class="empty-box">
        🚧 추천 기능은 추후 구현 예정입니다.
      </div>
    </section>

    <!-- ------------------------------------- -->
    <!-- (1) 사용자 관심 Topic 태그 필터 영역 -->
    <!-- ------------------------------------- -->
    <div class="topic-filter">
      <button
        v-for="t in interestTopics"
        :key="t"
        class="topic-btn"
        :class="{ active: selectedTopic === t }"
        @click="selectedTopic = t"
      >
        {{ t }}
      </button>
    </div>

    <!-- ------------------------------------- -->
    <!-- (2) 즐겨찾기 기반 추천 섹션 -->
    <!-- ------------------------------------- -->
    <section class="recommend-wrapper">
      <h2 class="recommend-title">
        이런 논문은 어때요?:
      </h2>

      <div class="recommend-cards">
        <PaperCard
          v-for="p in bookmarkBasedPapers"
          :key="p.id"
          :paper="p"
        />
      </div>
    </section>

    <!-- ------------------------------------- -->
    <!-- (3) 카테고리별 추천 섹션 (Interest) -->
    <!-- ------------------------------------- -->
    <section
      v-for="category in categoryRecommend"
      :key="category.name"
      class="category-section"
    >
      <div class="category-header">
        <h3>{{ category.name }}</h3>
        <span class="see-more">More ></span>
      </div>

      <div class="category-carousel">
        <PaperCard
          v-for="p in category.papers"
          :key="p.id"
          :paper="p"
        />
      </div>
    </section>

  </div>
</template>

<script setup>
import { ref } from "vue";
import PaperCard from "@/components/PaperCard.vue";

/* 관심 Topic */
const interestTopics = ref(["AI", "Data Science", "BioHealth"]);
const selectedTopic = ref("AI");

/* 즐겨찾기 기반 추천 */
const bookmarkBasedPapers = ref([
  {
    id: 11,
    title: "Neural Network Optimization Strategies",
    author: "Kim",
    year: 2023,
    citation: 32,
    institution: "MIT",
  },
  {
    id: 12,
    title: "Deep Reinforcement Learning Guide",
    author: "Lee",
    year: 2024,
    citation: 80,
    institution: "Stanford",
  },
  {
    id: 13,
    title: "Efficient Transformer Models",
    author: "Park",
    year: 2023,
    citation: 55,
    institution: "KAIST",
  },
]);

/* 카테고리별 추천 */
const categoryRecommend = ref([
  {
    name: "AI Research",
    papers: [
      { id: 21, title: "GAN Innovations", author: "Choi", year: 2022, citation: 120, institution: "MIT" },
      { id: 22, title: "Vision Transformer Study", author: "Han", year: 2023, citation: 88, institution: "Harvard" },
      { id: 23, title: "RL with PPO & SAC", author: "Min", year: 2021, citation: 77, institution: "UC Berkeley" },
    ]
  },
  {
    name: "Data Engineering",
    papers: [
      { id: 31, title: "Distributed Databases", author: "Lee", year: 2023, citation: 66, institution: "CMU" },
      { id: 32, title: "Kafka Stream Processing", author: "Park", year: 2024, citation: 40, institution: "Google" },
      { id: 33, title: "Large-Scale ETL", author: "Kim", year: 2023, citation: 55, institution: "KAIST" },
    ]
  },
  {
    name: "Bio & Health",
    papers: [
      { id: 41, title: "Genomic Pattern Analysis", author: "Jung", year: 2023, citation: 90, institution: "Oxford" },
      { id: 42, title: "Cancer Cell Detection AI", author: "Seo", year: 2024, citation: 48, institution: "Harvard" },
    ]
  },
]);
</script>

<style scoped>
/* 전체 페이지 */
.recommend-page {
  width: 100%;
  max-width: 1200px;
  margin: auto;
  padding: 40px 0;
}

/* (0) 관심있는 주제 기반 추천 (이동된 영역) */
.interest-wrapper {
  background: white;
  padding: 26px;
  border-radius: 14px;
  margin-bottom: 18px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

.interest-title {
  font-size: 20px;
  font-weight: 800;
  margin-bottom: 8px;
}

.interest-desc {
  font-size: 14px;
  color: #666;
  margin-bottom: 14px;
}

.empty-box {
  background: #f8fafc;
  padding: 18px;
  border-radius: 12px;
  text-align: center;
  color: #777;
  font-size: 14px;
}

/* ------------------------ */
/*     Interest Topics      */
/* ------------------------ */
.topic-filter {
  display: flex;
  gap: 10px;
  margin-bottom: 25px;
}

.topic-btn {
  padding: 8px 18px;
  border-radius: 20px;
  border: 1px solid #ddd;
  background: white;
  cursor: pointer;
  font-size: 14px;
}

.topic-btn.active {
  background: black;
  color: white;
}

/* -------------------------------------------- */
/*  (2) 즐겨찾기 추천 박스 */
/* -------------------------------------------- */
.recommend-wrapper {
  background: #f8f6ef;
  padding: 28px;
  border-radius: 14px;
  margin-bottom: 50px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

.recommend-title {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 20px;
}

.recommend-cards {
  display: flex;
  gap: 20px;
}

/* ------------------------ */
/* (3) 카테고리 추천 섹션 */
/* ------------------------ */
.category-section {
  margin-top: 50px;
}

.category-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.category-header h3 {
  font-size: 18px;
  font-weight: 700;
}

.see-more {
  font-size: 14px;
  color: #666;
  cursor: pointer;
}

.category-carousel {
  display: flex;
  gap: 18px;
}
</style>
