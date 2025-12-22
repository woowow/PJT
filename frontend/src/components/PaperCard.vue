<template>
  <div class="paper-card" @click="goDetail">
    <button
      class="bookmark-btn"
      @click.stop="toggleBookmark"
      :title="isFavorited ? '즐겨찾기 해제' : '즐겨찾기'"
    >
      {{ isFavorited ? "★" : "☆" }}
    </button>

    <h3 class="title">{{ paper.title }}</h3>

    <p class="authors" v-if="paper.authors && paper.authors.length">
      <span
        v-for="(a, idx) in paper.authors"
        :key="a.author_id"
        class="author"
        @click.stop="goAuthor(a.author_id)"
      >
        {{ a.author_name }}<span v-if="idx < paper.authors.length - 1">, </span>
      </span>
    </p>
    <p v-else class="authors-empty">저자 정보 없음</p>

    <p class="meta">
      <span>{{ paper.year }}</span>
      <span class="dot">·</span>
      <span>인용 {{ paper.citation }}</span>
    </p>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import api from "@/api";

const props = defineProps({ paper: Object });
const emit = defineEmits(["favoriteChanged"]);

const router = useRouter();
const isFavorited = ref(false);

const goDetail = () => router.push(`/paper/${props.paper.id}`);
const goAuthor = (id) => router.push(`/author/${id}`);

const toggleBookmark = async () => {
  const guestId = localStorage.getItem("guest_id");
  if (!guestId) return;

  // ✅ paper_id를 숫자로 강제 (ES 결과가 문자열인 케이스 방어)
  const paperIdNum = Number(props.paper.id);
  if (!Number.isFinite(paperIdNum)) {
    console.warn("Invalid paper.id (not numeric):", props.paper.id);
    return;
  }

  try {
    const res = await api.post("/favorites/toggle/", {
      guest_id: Number(guestId),
      paper_id: paperIdNum,
    });

    isFavorited.value = !!res.data.favorited;
    emit("favoriteChanged");
  } catch (e) {
    console.error("toggle favorite failed:", e?.response?.data || e);
  }
};

onMounted(async () => {
  const guestId = localStorage.getItem("guest_id");
  if (!guestId) return;

  try {
    const res = await api.get(`/favorites/${guestId}/`);

    const myId = Number(props.paper.id);
    isFavorited.value =
      Array.isArray(res.data) &&
      res.data.some((p) => Number(p.id) === myId);
  } catch (e) {
    console.warn("favorite list load failed:", e?.response?.data || e);
  }
});
</script>

<style scoped>
.paper-card {
  position: relative;
  background: #ffffff;
  border: 1px solid #e7eaf0;
  border-radius: 14px;
  padding: 16px 16px 14px;
  cursor: pointer;
  transition: transform 0.14s ease, box-shadow 0.14s ease, border-color 0.14s ease;
  box-shadow: 0 3px 10px rgba(0,0,0,0.04);
}

.paper-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 22px rgba(0,0,0,0.08);
  border-color: #c7d2fe;
}

.bookmark-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  background: #fff;
  border: 1px solid #f1f5f9;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  font-size: 18px;
  color: #f59e0b;
  cursor: pointer;
  display: grid;
  place-items: center;
}

.title {
  font-size: 15px;
  font-weight: 800;
  line-height: 1.3;
  margin: 2px 38px 8px 0;
}

.authors {
  font-size: 13px;
  color: #374151;
  margin-bottom: 8px;
}

.author {
  text-decoration: underline;
  cursor: pointer;
}

.author:hover {
  color: #2563eb;
}

.authors-empty {
  font-size: 13px;
  color: #9ca3af;
  margin-bottom: 8px;
}

.meta {
  font-size: 12px;
  color: #6b7280;
}

.dot {
  margin: 0 6px;
}
</style>
