<template>
  <div class="detail-container">
    <h1 class="title">{{ paper.title }}</h1>

    <div class="meta-box">
      <p><strong>저자:</strong> {{ paper.author }}</p>
      <p><strong>연도:</strong> {{ paper.year }}</p>
      <p><strong>인용수:</strong> {{ paper.citation }}</p>
      <p><strong>기관:</strong> {{ paper.institution }}</p>
    </div>

    <hr />

    <div class="abstract-box">
      <h2>초록 (Abstract)</h2>
      <p>{{ paper.abstract }}</p>
    </div>

    <hr />

    <!-- 나중에: 추천 논문, 관련 저자, 그래프 등을 더 추가할 예정 -->
  </div>
</template>

<script setup>
import { useRoute } from "vue-router";
import { ref, onMounted } from "vue";

const route = useRoute();
const paperId = route.params.id;

// 지금은 백엔드 없음 → 더미 데이터로 구성
const paper = ref({
  id: paperId,
  title: "Dummy Paper Title",
  author: "John Doe",
  year: 2023,
  citation: 42,
  institution: "MIT",
  abstract:
    "여기는 논문 초록(Abstract)이 표시되는 영역입니다. 백엔드가 연결되면 실제 논문 초록이 여기에 표시됩니다.",
});

// 백엔드 연결 후 이렇게 바뀔 예정:
// onMounted(async () => {
//   const res = await axios.get(`/api/paper/${paperId}`);
//   paper.value = res.data;
// });
</script>

<style scoped>
.detail-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 40px;
}

.title {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 25px;
}

.meta-box p {
  margin: 6px 0;
  font-size: 16px;
}

.abstract-box {
  margin-top: 20px;
}

.abstract-box h2 {
  font-size: 22px;
  margin-bottom: 10px;
}

.abstract-box p {
  line-height: 1.6;
  color: #555;
}
</style>
