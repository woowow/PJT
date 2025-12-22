<script setup>
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import api from "@/api";

const router = useRouter();
const emit = defineEmits(["close"]);

const keyword = ref("");
const subject = ref("");
const country = ref("");

// 기간 모드: range | recent1y | all
const dateMode = ref("all");
const yearFrom = ref("");
const yearTo = ref("");

const sort = ref("recent");

const subjects = ref([]);
const countries = ref([]);

const loadOptions = async () => {
  try {
    const res = await api.get("/papers/search/options/");
    subjects.value = res.data.subjects || [];
    countries.value = res.data.countries || [];
  } catch (e) {
    console.error("옵션 로딩 실패", e);
  }
};

onMounted(loadOptions);

const currentYear = new Date().getFullYear();

const computedRange = computed(() => {
  if (dateMode.value === "recent1y") {
    return { yf: String(currentYear - 1), yt: String(currentYear) };
  }
  if (dateMode.value === "range") {
    return { yf: yearFrom.value.trim(), yt: yearTo.value.trim() };
  }
  return { yf: "", yt: "" };
});

const reset = () => {
  keyword.value = "";
  subject.value = "";
  country.value = "";
  dateMode.value = "all";
  yearFrom.value = "";
  yearTo.value = "";
  sort.value = "recent";
};

const search = () => {
  const k = keyword.value.trim();
  const s = subject.value.trim();
  const c = country.value.trim();
  const { yf, yt } = computedRange.value;

  router.push({
    name: "search",
    query: {
      ...(k && { keyword: k }),
      ...(s && { subject: s }),
      ...(c && { country: c }),
      ...(yf && { year_from: yf }),
      ...(yt && { year_to: yt }),
      ...(sort.value && { sort: sort.value }),
    },
  });

  emit("close");
};
</script>

<template>
  <div class="modal-backdrop">
    <div class="modal">
      <h2>상세 검색</h2>

      <div class="section">
        <div class="label">검색어 입력</div>
        <input v-model="keyword" placeholder="검색어" />
      </div>

      <div class="section">
        <div class="label">주제 검색</div>
        <select v-model="subject">
          <option value="">주제 선택</option>
          <option v-for="s in subjects" :key="s" :value="s">
            {{ s }}
          </option>
        </select>
      </div>

      <div class="section">
        <div class="label">국가 코드</div>
        <select v-model="country">
          <option value="">국가 선택</option>
          <option v-for="c in countries" :key="c" :value="c">
            {{ c }}
          </option>
        </select>
      </div>

      <div class="section">
        <div class="label">출판 날짜</div>

        <div class="radio-row">
          <label>
            <input type="radio" value="range" v-model="dateMode" />
            From ~ To
          </label>

          <label>
            <input type="radio" value="recent1y" v-model="dateMode" />
            최근 1년
          </label>

          <label>
            <input type="radio" value="all" v-model="dateMode" />
            모든 날짜
          </label>
        </div>

        <div class="range-row" v-if="dateMode === 'range'">
          <input v-model="yearFrom" placeholder="From (YYYY)" />
          <span class="to">To</span>
          <input v-model="yearTo" placeholder="To (YYYY)" />
        </div>

        <div class="hint" v-else-if="dateMode === 'recent1y'">
          자동 범위: {{ currentYear - 1 }} ~ {{ currentYear }}
        </div>
      </div>

      <div class="section">
        <div class="label">정렬 형태</div>
        <div class="radio-row">
          <label>
            <input type="radio" value="recent" v-model="sort" />
            최신순
          </label>
          <label>
            <input type="radio" value="citation" v-model="sort" />
            인용순
          </label>
        </div>
      </div>

      <div class="actions">
        <button class="ghost" @click="reset">검색값 초기화</button>
        <div class="right">
          <button class="ghost" @click="$emit('close')">닫기</button>
          <button class="primary" @click="search">Search</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.modal {
  width: 680px;
  background: #fff;
  border-radius: 18px;
  padding: 22px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.15);
}

.section {
  margin-top: 14px;
}

.label {
  font-weight: 700;
  margin-bottom: 8px;
}

input, select {
  width: 100%;
  height: 42px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  padding: 0 12px;
  outline: none;
}

.radio-row {
  display: flex;
  gap: 18px;
  align-items: center;
  flex-wrap: wrap;
}

.range-row {
  margin-top: 10px;
  display: flex;
  gap: 10px;
  align-items: center;
}

.range-row input {
  flex: 1;
}

.to {
  font-weight: 600;
}

.hint {
  margin-top: 8px;
  font-size: 13px;
  color: #666;
}

.actions {
  margin-top: 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.right {
  display: flex;
  gap: 10px;
}

button {
  height: 40px;
  border-radius: 999px;
  padding: 0 14px;
  border: 1px solid #e5e7eb;
  cursor: pointer;
  background: #fff;
}

button.primary {
  border: none;
  background: #111827;
  color: white;
  padding: 0 18px;
}

button.ghost:hover {
  background: #f3f4f6;
}
</style>
