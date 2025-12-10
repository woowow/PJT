<template>
  <div class="home-container">


    <!-- 로고 -->
    <div class="logo-wrapper">
      <img src="@/assets/main_image.png" class="logo-img" />
    </div>

    <!-- 검색 영역 -->
    <div class="search-area">
      <div class="search-box">
        <input
          v-model="keyword"
          type="text"
          placeholder="검색어 입력"
          class="search-input"
          @keyup.enter="goSearch"
        />

        <img
          src="@/assets/search-icon.png"
          class="search-icon"
          @click="goSearch"
        />
      </div>

      <div class="detail-search" @click="isDetailSearchOpen = true">
        상세검색
      </div>
    </div>

    <!-- 상세 검색 모달 -->
    <div v-if="isDetailSearchOpen" class="modal-overlay">
      <div class="modal-box">

        <!-- 상단 -->
        <div class="modal-header">
          <h2>상세 검색</h2>
          <div class="close-btn" @click="isDetailSearchOpen = false">⨉</div>
        </div>

        <div class="modal-section">

          <!-- 검색어 -->
          <label class="modal-label">검색어 입력</label>
          <input type="text" class="modal-input" v-model="detail.keyword" />
          <hr />

          <!-- 주제 -->
          <label class="modal-label">주제 검색</label>
          <div class="dropdown-box">
            <input
              type="text"
              v-model="subjectSearch"
              placeholder="주제 검색"
              class="dropdown-main-input"
              @focus="openSubject"
              @blur="onBlur"
            />

            <span class="arrow" @click.stop="toggleSubject">▼</span>

            <div v-if="isSubjectOpen" class="dropdown-list-container">
              <ul class="dropdown-list">
                <li
                  v-for="item in filteredSubjects"
                  :key="item"
                  class="dropdown-item"
                  @click="selectSubject(item)"
                >
                  {{ item }}
                </li>
              </ul>
            </div>
          </div>

          <hr />

          <!-- 국가 코드 -->
          <label class="modal-label">국가 코드</label>
          <div class="dropdown-box">
            <input
              type="text"
              v-model="countrySearch"
              placeholder="국가 검색"
              class="dropdown-main-input"
              @focus="openCountry"
              @blur="onCountryBlur"
            />

            <span class="arrow" @click.stop="toggleCountry">▼</span>

            <div v-if="isCountryOpen" class="dropdown-list-container">
              <ul class="dropdown-list">
                <li
                  v-for="item in filteredCountries"
                  :key="item"
                  class="dropdown-item"
                  @click="selectCountry(item)"
                >
                  {{ item }}
                </li>
              </ul>
            </div>
          </div>

          <hr />

          <!-- 출판 날짜 -->
          <label class="modal-label">출판 날짜</label>

          <div class="date-container">
            <div class="date-row">
              <label>
                <input type="radio" v-model="detail.dateType" value="range" />
                From
              </label>
              <input type="text" class="modal-date" v-model="detail.from" placeholder="YYYY" />
              <span>To</span>
              <input type="text" class="modal-date" v-model="detail.to" placeholder="YYYY" />
            </div>

            <div class="date-options">
              <label><input type="radio" v-model="detail.dateType" value="1year" /> 최근 1년</label>
              <label><input type="radio" v-model="detail.dateType" value="all" /> 모든 날짜</label>
            </div>
          </div>

          <hr />

          <!-- 정렬 -->
          <label class="modal-label">정렬 형태</label>
          <div class="sort-options">
            <label><input type="checkbox" v-model="detail.sortRecent" /> 최신순</label>
            <label><input type="checkbox" v-model="detail.sortCitation" /> 인용순</label>
          </div>
        </div>

        <div class="modal-footer">
          <button class="reset-btn" @click="resetDetail">↺ 검색값 초기화</button>
          <button class="modal-search-btn" @click="submitDetailSearch">Search</button>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import ProfileIcon from "@/components/ProfileIcon.vue";

const router = useRouter();
const keyword = ref("");

const goSearch = () => {
  if (!keyword.value.trim()) return;
  router.push(`/search?keyword=${keyword.value}`);
};

// 상세 검색 값들
const isDetailSearchOpen = ref(false);

const detail = ref({
  keyword: "",
  subject: "",
  country: "",
  from: "",
  to: "",
  dateType: "null",
  sortRecent: false,
  sortCitation: false,
});

// 초기화
const resetDetail = () => {
  detail.value = {
    keyword: "",
    subject: "",
    country: "",
    from: "",
    to: "",
    dateType: "null",
    sortRecent: false,
    sortCitation: false,
  };

  subjectSearch.value = "";
  countrySearch.value = "";
  isSubjectOpen.value = false;
  isCountryOpen.value = false;
};

// 검색 실행
const submitDetailSearch = () => {
  const query = new URLSearchParams({
    keyword: detail.value.keyword,
    subject: detail.value.subject,
    country: detail.value.country,
    from: detail.value.from,
    to: detail.value.to,
    dateType: detail.value.dateType,
    sortRecent: detail.value.sortRecent,
    sortCitation: detail.value.sortCitation,
  });

  isDetailSearchOpen.value = false;
  router.push(`/search?${query.toString()}`);
};

// 드롭다운 데이터
const countryList = ref(["KR", "US", "JP", "CN", "DE", "FR", "UK"]);
const subjectList = ref(["AI", "Physics", "Chemistry", "Biology", "Math", "Economics"]);

// dropdown states
const isCountryOpen = ref(false);
const isSubjectOpen = ref(false);

const countrySearch = ref("");
const subjectSearch = ref("");

// 필터링
const filteredCountries = computed(() =>
  countrySearch.value
    ? countryList.value.filter(item =>
        item.toLowerCase().includes(countrySearch.value.toLowerCase())
      )
    : countryList.value
);

const filteredSubjects = computed(() =>
  subjectSearch.value
    ? subjectList.value.filter(item =>
        item.toLowerCase().includes(subjectSearch.value.toLowerCase())
      )
    : subjectList.value
);

// subject dropdown
const openSubject = () => {
  isSubjectOpen.value = true;
};

const toggleSubject = () => {
  isSubjectOpen.value = !isSubjectOpen.value;
};

const onBlur = () => {
  setTimeout(() => (isSubjectOpen.value = false), 150);
};

const selectSubject = (item) => {
  detail.value.subject = item;
  subjectSearch.value = item;
  isSubjectOpen.value = false;
};

// country dropdown
const openCountry = () => {
  isCountryOpen.value = true;
};

const toggleCountry = () => {
  isCountryOpen.value = !isCountryOpen.value;
};

const onCountryBlur = () => {
  setTimeout(() => (isCountryOpen.value = false), 150);
};

const selectCountry = (item) => {
  detail.value.country = item;
  countrySearch.value = item;
  isCountryOpen.value = false;
};
</script>

<style scoped>
/* 기존 스타일 그대로 유지 */

.home-container {
  width: 100%;
  min-height: 100vh;
  background: white;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}

.logo-wrapper {
  margin-top: 80px;
  margin-bottom: 40px;
}

.logo-img {
  width: 700px;
}

.search-area {
  width: 70%;
  max-width: 900px;
  display: flex;
  align-items: center;
  gap: 20px;
  position: relative;
  flex-direction: column;
}

.search-box {
  width: 100%;
  background: #f5f7fb;
  border-radius: 35px;
  height: 70px;
  display: flex;
  align-items: center;
  padding: 0 30px;
  justify-content: space-between;
  box-shadow: rgba(0, 0, 0, 0.05) 0px 4px 12px;
}

.search-input {
  flex: 1;
  border: none;
  background: none;
  font-size: 18px;
  outline: none;
}

.search-icon {
  width: 26px;
  opacity: 0.6;
  cursor: pointer;
}

.detail-search {
  font-size: 15px;
  margin-top: 6px;
  margin-left: auto;
  margin-right: 10px;
  cursor: pointer;
  color: #333;
}

.dropdown-box {
  position: relative;
  width: 90%;
  background: #f2f4f7;
  border-radius: 15px;
  height: 45px;
  padding: 0 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
}

.dropdown-main-input {
  flex: 1;
  height: 100%;
  border: none;
  background: transparent;
  font-size: 15px;
  outline: none;
}

.dropdown-list-container {
  position: absolute;
  top: 50px;
  left: 0;
  width: 100%;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 14px rgba(0,0,0,0.15);
  max-height: 200px;
  overflow-y: auto;
  padding: 10px 0;
  z-index: 9999;
}

.dropdown-item {
  padding: 10px 12px;
  font-size: 15px;
  cursor: pointer;
  border-radius: 8px;
}

.dropdown-item:hover {
  background: #f2f4f7;
}

.arrow {
  font-size: 12px;
  opacity: 0.6;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 200;
}

.modal-box {
  background: white;
  width: 600px;
  padding: 30px;
  border-radius: 25px;
  box-shadow: rgba(0, 0, 0, 0.2) 0px 6px 30px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.close-btn {
  font-size: 32px;
  cursor: pointer;
}

hr {
  margin: 15px 0;
  width: 95%;
  border: none;
  border-bottom: 1px solid #ddd;
}

.modal-label {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 6px;
  display: block;
}

.modal-input {
  width: 90%;
  height: 45px;
  background: #f2f4f7;
  border: none;
  border-radius: 15px;
  padding: 0 15px;
  outline: none;
}

.date-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.modal-date {
  width: 100px;
  height: 35px;
  background: #f2f4f7;
  border-radius: 10px;
  border: none;
  outline: none;
  padding: 0 10px;
}

.date-options {
  margin-top: 10px;
  display: flex;
  gap: 15px;
}

.sort-options {
  display: flex;
  gap: 20px;
  margin-top: 10px;
}

.modal-footer {
  margin-top: 25px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.reset-btn {
  color: #aaa;
  background: none;
  border: none;
  cursor: pointer;
}

.modal-search-btn {
  background: black;
  color: white;
  width: 120px;
  height: 45px;
  border-radius: 20px;
  border: none;
  cursor: pointer;
}
</style>
