<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import api from "@/api";

const router = useRouter();
const emit = defineEmits(["close"]);

const keyword = ref("");
const subject = ref("");
const country = ref("");
const yearFrom = ref("");
const yearTo = ref("");
const sort = ref("recent");

/* 🔥 옵션 상태 */
const subjects = ref([]);
const countries = ref([]);

/* 🔥 옵션 로딩 */
const loadOptions = async () => {
  try {
    const res = await api.get("/papers/search/options/");
    subjects.value = res.data.subjects;
    countries.value = res.data.countries;
  } catch (e) {
    console.error("옵션 로딩 실패", e);
  }
};

onMounted(loadOptions);

const search = () => {
  router.push({
    name: "search",
    query: {
      ...(keyword.value && { keyword: keyword.value }),
      ...(subject.value && { subject: subject.value }),
      ...(country.value && { country: country.value }),
      ...(yearFrom.value && { year_from: yearFrom.value }),
      ...(yearTo.value && { year_to: yearTo.value }),
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

      <input v-model="keyword" placeholder="검색어" />

      <select v-model="subject">
        <option value="">주제 선택</option>
        <option v-for="s in subjects" :key="s" :value="s">
          {{ s }}
        </option>
      </select>

      <select v-model="country">
        <option value="">국가 선택</option>
        <option v-for="c in countries" :key="c" :value="c">
          {{ c }}
        </option>
      </select>

      <div>
        <input v-model="yearFrom" placeholder="From (YYYY)" />
        <input v-model="yearTo" placeholder="To (YYYY)" />
      </div>

      <div>
        <label>
          <input type="radio" value="recent" v-model="sort" /> 최신순
        </label>
        <label>
          <input type="radio" value="citation" v-model="sort" /> 인용순
        </label>
      </div>

      <button @click="search">검색</button>
      <button @click="$emit('close')">닫기</button>
    </div>
  </div>
</template>
