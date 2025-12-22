<template>
  <div class="detail-page" v-if="!loading && paper">
    <!-- 헤더 -->
    <div class="header-card">
      <div class="title-area">
        <h1 class="title">{{ paper.title || "(제목 없음)" }}</h1>

        <div class="meta-row">
          <span class="chip">{{ paper.subject || "-" }}</span>
          <span class="chip">{{ paper.institution || "-" }}</span>
          <span class="chip">Citations: {{ paper.citation ?? 0 }}</span>
          <span class="chip">Year: {{ paper.year ?? "-" }}</span>
        </div>

        <div class="meta-row">
          <span class="chip">
            Open Access:
            <b :class="paper.open_access ? 'yes' : 'no'">
              {{ paper.open_access ? "Yes" : "No" }}
            </b>
          </span>

          <span class="chip">
            Published:
            <b>{{ formattedDate }}</b>
          </span>
        </div>
      </div>
    </div>

    <!-- 저자 -->
    <div class="section-card">
      <h2 class="section-title">Authors</h2>
      <div class="authors">
        <router-link
          v-for="a in paper.authors"
          :key="a.author_id"
          class="author-pill"
          :to="`/author/${a.author_id}`"
        >
          {{ a.author_name }}
        </router-link>

        <div v-if="!paper.authors || !paper.authors.length" class="muted">
          저자 정보가 없습니다.
        </div>
      </div>
    </div>

    <!-- Abstract -->
    <div class="section-card">
      <h2 class="section-title">Abstract</h2>
      <p class="abstract" v-if="paper.abstract">
        {{ paper.abstract }}
      </p>
      <div v-else class="muted">
        Abstract 정보가 없습니다.
      </div>
    </div>

    <!-- Links -->
    <div class="section-card">
      <h2 class="section-title">Links</h2>

      <div v-if="linkList.length" class="links">
        <a
          v-for="(u, idx) in linkList"
          :key="idx"
          class="link-item"
          :href="u"
          target="_blank"
          rel="noopener noreferrer"
        >
          {{ u }}
        </a>
      </div>

      <div v-else class="muted">
        링크 정보가 없습니다.
      </div>
    </div>
  </div>

  <div class="loading" v-else-if="loading">
    불러오는 중...
  </div>

  <div class="loading" v-else>
    논문 정보를 찾을 수 없습니다.
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import api from "@/api";

const route = useRoute();
const paper = ref(null);
const loading = ref(true);

const paperId = computed(() => route.params.id);

const formattedDate = computed(() => {
  const d = paper.value?.announcement_date;
  if (!d) return "-";
  // YYYY-MM-DD -> ko-KR 표시
  try {
    const dt = new Date(d);
    if (Number.isNaN(dt.getTime())) return d;
    return dt.toLocaleDateString("ko-KR", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
  } catch {
    return d;
  }
});

// locations가 TEXT라서 어떤 포맷이든 최대한 안전하게 링크만 뽑아냄
const linkList = computed(() => {
  const raw = paper.value?.locations;
  if (!raw) return [];

  // 이미 배열 형태로 내려오는 경우
  if (Array.isArray(raw)) {
    return raw.map(String).filter(u => u.startsWith("http"));
  }

  const s = String(raw).trim();
  if (!s) return [];

  // JSON 가능성
  if (s.startsWith("[") || s.startsWith("{")) {
    try {
      const obj = JSON.parse(s);
      if (Array.isArray(obj)) {
        return obj.map(String).filter(u => u.startsWith("http"));
      }
      // { urls: [...] } 같은 형태
      if (obj && typeof obj === "object") {
        const maybe = obj.urls || obj.links || obj.locations;
        if (Array.isArray(maybe)) {
          return maybe.map(String).filter(u => u.startsWith("http"));
        }
      }
    } catch {
      // JSON 파싱 실패면 아래 fallback으로
    }
  }

  // fallback: 공백/쉼표/줄바꿈 기준 분리 후 http만 남김
  return s
    .split(/[\s,\n\r]+/g)
    .map(v => v.trim())
    .filter(v => v.startsWith("http"));
});

onMounted(async () => {
  loading.value = true;
  try {
    // ✅ paper detail
    const res = await api.get(`/papers/${paperId.value}/`);
    paper.value = res.data || null;

    // ✅ (선택) 상세보기 열람 트래킹
    // 엔드포인트가 이미 연결돼 있다면 그대로 동작함
    const guestId = localStorage.getItem("guest_id");
    if (guestId) {
      try {
        await api.post(`/papers/${paperId.value}/track/`, { guest_id: guestId });
      } catch (e) {
        // 트래킹 실패해도 상세보기는 떠야 함
        console.warn("track failed:", e);
      }
    }
  } catch (e) {
    console.error(e);
    paper.value = null;
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.detail-page {
  width: 100%;
  max-width: 980px;
  margin: 0 auto;
  padding: 34px 20px 60px;
}

/* 공통 카드 */
.header-card,
.section-card {
  background: white;
  border-radius: 18px;
  box-shadow: 0 6px 18px rgba(0,0,0,0.06);
  border: 1px solid rgba(0,0,0,0.05);
  padding: 22px 24px;
  margin-bottom: 18px;
}

.title {
  font-size: 26px;
  line-height: 1.25;
  font-weight: 800;
  margin: 0 0 14px;
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 10px;
}

.chip {
  background: #f3f4f6;
  border-radius: 999px;
  padding: 7px 12px;
  font-size: 13px;
  color: #333;
}

.yes {
  color: #0f766e;
}
.no {
  color: #b91c1c;
}

.section-title {
  font-size: 16px;
  font-weight: 800;
  margin: 0 0 14px;
}

.authors {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.author-pill {
  text-decoration: none;
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid #e5e7eb;
  background: #fff;
  color: #111;
  font-size: 13px;
  transition: 0.15s;
}
.author-pill:hover {
  transform: translateY(-1px);
  background: #f9fafb;
}

.abstract {
  font-size: 14px;
  line-height: 1.7;
  color: #222;
  white-space: pre-wrap;
}

.links {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.link-item {
  color: #2563eb;
  text-decoration: underline;
  font-size: 14px;
  word-break: break-all;
}

.muted {
  color: #6b7280;
  font-size: 14px;
}

.loading {
  padding: 60px 20px;
  text-align: center;
  color: #666;
  font-size: 16px;
}
</style>
