<template>
  <div class="author-view" v-if="author">
    <h1>{{ author.author_name }}</h1>

    <p class="institution">
      {{ author.institution.institution_name }}
      ({{ author.institution.country_code }})
    </p>

    <p>총 인용 수: {{ author.citation_total }}</p>

    <div class="topics">
      <span
        v-for="topic in author.main_topics"
        :key="topic"
        class="topic"
      >
        {{ topic }}
      </span>
    </div>

    <h2>논문 목록</h2>

    <PaperCard
      v-for="paper in papers"
      :key="paper.id"
      :paper="paper"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import api from "@/api";
import PaperCard from "@/components/PaperCard.vue";

const route = useRoute();
const author = ref(null);
const papers = ref([]);

onMounted(async () => {
  const res = await api.get(`/authors/${route.params.id}/`);
  author.value = res.data.author;
  papers.value = res.data.papers;
});
</script>

<style scoped>
.author-view {
  max-width: 900px;
  margin: 0 auto;
}

.institution {
  color: #555;
}

.topic {
  margin-right: 8px;
  padding: 4px 8px;
  background: #eef;
  border-radius: 6px;
}
</style>
