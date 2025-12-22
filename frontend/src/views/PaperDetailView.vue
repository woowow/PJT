<template>
  <div class="detail-wrapper">
    <div v-if="paper" class="detail-container">
      <h1 class="title">{{ paper.title }}</h1>

      <div class="meta-box">
        <p>
          <strong>저자:</strong>
          <span
            v-for="(author, idx) in paper.authors"
            :key="author.author_id"
            class="author-link"
            @click="goAuthor(author.author_id)"
          >
            {{ author.author_name }}<span v-if="idx < paper.authors.length - 1">, </span>
          </span>
        </p>

        <p><strong>연도:</strong> {{ paper.year || "-" }}</p>
        <p><strong>주제:</strong> {{ paper.subject || "-" }}</p>
        <p><strong>기관:</strong> {{ paper.institution || "-" }}</p>
        <p><strong>인용수:</strong> {{ paper.citation ?? 0 }}</p>
      </div>

      <hr />

      <div class="abstract-box">
        <h2>초록 (Abstract)</h2>
        <p v-if="paper.abstract">{{ paper.abstract }}</p>
        <p v-else class="empty">
          초록 정보가 제공되지 않는 논문입니다.
        </p>
      </div>
    </div>

    <div v-else class="loading">
      논문 정보를 불러오는 중입니다...
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import api from "@/api";

const route = useRoute();
const router = useRouter();
const paper = ref(null);

const goAuthor = (authorId) => {
  router.push(`/author/${authorId}`);
};

onMounted(async () => {
  const paperId = route.params.id;

  const res = await api.get(`/papers/${paperId}/`);
  paper.value = res.data;

  const guestId = localStorage.getItem("guest_id");
  if (guestId) {
    try {
      await api.post(`/papers/${paperId}/track/`, {
        guest_id: guestId,
        event: "VIEW",
      });
    } catch (e) {
      // 트래킹 실패가 상세 렌더링을 막으면 UX가 깨져서 조용히 무시
      console.warn("track failed:", e);
    }
  }
});
</script>

<style scoped>
.author-link {
  cursor: pointer;
  text-decoration: underline;
}

.author-link:hover {
  color: #2563eb;
}
</style>
