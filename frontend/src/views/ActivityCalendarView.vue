<template>
  <div class="page-header">
    <h1 class="page-title">Research Calendar</h1>
    <p class="page-desc">
      Your bookmarked papers, organized by date.
    </p>
  </div>
  <div class="calendar-wrapper">

    <!-- 헤더 -->
    <div class="calendar-header">
      <button class="nav-btn" @click="goPrevMonth">◀</button>
      <h2 class="month-title">{{ monthLabel }}</h2>
      <button class="nav-btn" @click="goNextMonth">▶</button>
    </div>

    <!-- 요일 -->
    <div class="weekdays">
      <div v-for="d in weekDays" :key="d">{{ d }}</div>
    </div>

    <!-- 날짜 그리드 -->
    <div class="calendar-grid">
      <!-- 앞쪽 빈칸 -->
      <div
        v-for="n in startDay"
        :key="'empty-' + n"
        class="calendar-cell empty"
      />

      <!-- 날짜 셀 -->
      <div
        v-for="day in daysInMonth"
        :key="day.fullDate"
        class="calendar-cell"
        :class="{ active: hasPapers(day.fullDate) }"
        @click="selectDate(day.fullDate)"
      >
        <div class="date-number">{{ day.date }}</div>

        <!-- 논문 미리보기 -->
        <div
          v-for="(paper, idx) in getPapers(day.fullDate).slice(0, 2)"
          :key="paper.id"
          class="paper-preview"
        >
          ⭐ {{ paper.title }}
        </div>

        <!-- + more -->
        <div
          v-if="getPapers(day.fullDate).length > 2"
          class="more"
        >
          +{{ getPapers(day.fullDate).length - 2 }} more
        </div>
      </div>
    </div>

    <!-- 선택 날짜 상세 -->
    <div v-if="selectedDate" class="detail-section">
      <h3>{{ selectedDate }} 에 저장한 논문</h3>

      <div class="paper-list">
        <PaperCard
          v-for="p in getPapers(selectedDate)"
          :key="p.id"
          :paper="p"
        />
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import PaperCard from "@/components/PaperCard.vue";

/* =========================
   날짜 상태
========================= */
const currentMonth = ref(new Date());
const selectedDate = ref(null);

const weekDays = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];

/* =========================
   월 이동
========================= */
const goPrevMonth = () => {
  const d = new Date(currentMonth.value);
  d.setMonth(d.getMonth() - 1);
  currentMonth.value = d;
};

const goNextMonth = () => {
  const d = new Date(currentMonth.value);
  d.setMonth(d.getMonth() + 1);
  currentMonth.value = d;
};

const monthLabel = computed(() => {
  const y = currentMonth.value.getFullYear();
  const m = currentMonth.value.getMonth() + 1;
  return `${y}.${String(m).padStart(2, "0")}`;
});

/* =========================
   날짜 계산
========================= */
const startDay = computed(() => {
  const y = currentMonth.value.getFullYear();
  const m = currentMonth.value.getMonth();
  return new Date(y, m, 1).getDay();
});

const daysInMonth = computed(() => {
  const y = currentMonth.value.getFullYear();
  const m = currentMonth.value.getMonth();
  const last = new Date(y, m + 1, 0).getDate();

  return Array.from({ length: last }, (_, i) => ({
    date: i + 1,
    fullDate: `${y}-${String(m + 1).padStart(2, "0")}-${String(i + 1).padStart(2, "0")}`,
  }));
});

/* =========================
   더미 즐겨찾기 데이터
========================= */
const bookmarked = ref({
  "2025-12-10": [
    { id: 1, title: "Reinforcement Learning Survey", year: 2024, citation: 88, institution: "Stanford" },
    { id: 2, title: "Efficient LLM Inference", year: 2023, citation: 55, institution: "KAIST" },
    { id: 3, title: "Diffusion Models Explained" },
  ],
  "2025-12-12": [
    { id: 4, title: "Attention Is All You Need" },
  ],
});

/* =========================
   헬퍼
========================= */
const hasPapers = (date) => bookmarked.value[date]?.length;
const getPapers = (date) => bookmarked.value[date] || [];

const selectDate = (date) => {
  selectedDate.value = date;
};
</script>

<style scoped>

.page-header {
  max-width: 2000px;
  margin: auto;
}

.page-title {
  font-size: 26px;
  font-weight: 800;
}

.page-desc {
  margin-top: 6px;
  font-size: 14px;
  color: #666;
}


.calendar-wrapper {
  max-width: 2000px;
  margin: auto;
}

/* 헤더 */
.calendar-header {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 30px;
  margin-bottom: 20px;
}

.month-title {
  font-size: 24px;
  font-weight: 700;
}

.nav-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
}

/* 요일 */
.weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  text-align: center;
  font-weight: 600;
  margin-bottom: 10px;
}

/* 캘린더 */
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 16px;
}

/* 셀 */
.calendar-cell {
  min-height: 150px;
  padding: 10px;
  border-radius: 12px;
  background: #fafafa;
  cursor: pointer;
}

.calendar-cell.active {
  background: #f2f6ff;
}

.calendar-cell.empty {
  background: transparent;
}

/* 날짜 */
.date-number {
  font-weight: 700;
  margin-bottom: 8px;
}

/* 논문 미리보기 */
.paper-preview {
  font-size: 12px;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.more {
  font-size: 12px;
  color: #666;
}

/* 상세 */
.detail-section {
  margin-top: 50px;
}

.paper-list {
  display: flex;
  gap: 20px;
  margin-top: 20px;
}
</style>
