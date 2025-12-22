<template>
  <div class="mypage-wrapper">

    <!-- =========================
         좌측 사이드바
    ========================= -->
    <aside class="sidebar">
      <h2 class="sidebar-title">My Page</h2>

      <div
        class="sidebar-item"
        :class="{ active: activeMenu === 'profile' }"
        @click="activeMenu = 'profile'"
      >
        개인정보 수정
      </div>

      <div
        class="sidebar-item"
        :class="{ active: activeMenu === 'bookmarks' }"
        @click="activeMenu = 'bookmarks'"
      >
        즐겨찾기한 논문
      </div>

      <div
        class="sidebar-item"
        :class="{ active: activeMenu === 'topics' }"
        @click="activeMenu = 'topics'"
      >
        관심있는 주제 추천
      </div>
    </aside>

    <!-- =========================
         우측 컨텐츠
    ========================= -->
    <main class="content-area">

      <!-- =========================
           1. 개인정보 수정
      ========================= -->
      <section v-if="activeMenu === 'profile'" class="section">
        <h2 class="section-title">내 정보</h2>

        <div class="profile-card">
          <label>아이디</label>
          <input v-model="profile.guestname" type="text" />

          <label>비밀번호</label>
          <input
            v-model="profile.password"
            type="password"
            placeholder="새 비밀번호 입력"
          />

          <label>관심 주제 1</label>
          <div class="readonly">{{ profile.interest_1 || "-" }}</div>

          <label>관심 주제 2</label>
          <div class="readonly">{{ profile.interest_2 || "-" }}</div>

          <label>관심 주제 3</label>
          <div class="readonly">{{ profile.interest_3 || "-" }}</div>

          <button class="save-btn" @click="saveProfile">
            저장하기
          </button>
        </div>
      </section>

      <!-- =========================
           2. 즐겨찾기한 논문
           👉 ReadingBoardView 그대로 사용
      ========================= -->
      <section v-if="activeMenu === 'bookmarks'" class="section">
        <ReadingBoardView :key="activeMenu" />
      </section>

      <!-- =========================
           3. 관심 주제 추천 (미구현)
      ========================= -->
      <section v-if="activeMenu === 'topics'" class="section">
        <h2 class="section-title">관심있는 주제 기반 추천</h2>

        <div class="empty-box">
          🚧 추천 기능은 추후 구현 예정입니다.
        </div>
      </section>

    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import api from "@/api";
import ReadingBoardView from "@/views/ReadingBoardView.vue";

/* =========================
   상태
========================= */
const activeMenu = ref("profile");
const guestId = localStorage.getItem("guest_id");

/* =========================
   프로필
========================= */
const profile = ref({
  guestname: "",
  password: "",
  interest_1: null,
  interest_2: null,
  interest_3: null,
});

const loadProfile = async () => {
  if (!guestId) return;

  const res = await api.get(`/guests/${guestId}/`);
  profile.value.guestname = res.data.guestname;
  profile.value.interest_1 = res.data.interest_1;
  profile.value.interest_2 = res.data.interest_2;
  profile.value.interest_3 = res.data.interest_3;
};

const saveProfile = async () => {
  if (!profile.value.guestname || !profile.value.password) {
    alert("아이디와 비밀번호를 모두 입력해주세요.");
    return;
  }

  await api.put(`/guests/${guestId}/update/`, {
    guestname: profile.value.guestname,
    password: profile.value.password,
  });

  alert("프로필이 수정되었습니다.");
  profile.value.password = "";
};

onMounted(loadProfile);
</script>

<style scoped>
/* =========================
   전체 레이아웃
========================= */
.mypage-wrapper {
  display: flex;
  height: 100vh;
  background: #fafbfe;
  font-family: "Pretendard", sans-serif;
}

/* =========================
   사이드바
========================= */
.sidebar {
  width: 240px;
  background: white;
  padding: 30px;
  border-right: 1px solid #eee;
  box-shadow: 2px 0 10px rgba(0,0,0,0.04);
}

.sidebar-title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 30px;
}

.sidebar-item {
  padding: 14px 10px;
  margin-bottom: 6px;
  font-size: 15px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.25s, color 0.25s;
}

.sidebar-item:hover {
  background: #f2f4f8;
}

.sidebar-item.active {
  background: black;
  color: white;
}

/* =========================
   메인 영역
========================= */
.content-area {
  flex: 1;
  padding: 45px 60px;
  overflow-y: auto;
}

.section-title {
  font-size: 26px;
  font-weight: 700;
  margin-bottom: 25px;
}

/* =========================
   프로필 카드
========================= */
.profile-card {
  background: white;
  padding: 30px;
  border-radius: 14px;
  box-shadow: 0 4px 14px rgba(0,0,0,0.06);
  max-width: 380px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.profile-card input {
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 10px;
  font-size: 15px;
}

.save-btn {
  margin-top: 14px;
  padding: 12px;
  width: 100%;
  background: black;
  color: white;
  border-radius: 10px;
  cursor: pointer;
}

/* =========================
   기타
========================= */
.readonly {
  padding: 12px;
  border-radius: 10px;
  background: #f3f4f6;
  font-size: 15px;
  color: #555;
}

.empty-box {
  background: white;
  padding: 30px;
  border-radius: 12px;
  text-align: center;
  color: #777;
  font-size: 15px;
}
</style>
