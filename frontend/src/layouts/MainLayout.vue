<template>
  <div class="layout">

    <!-- 최상단 네비게이션바 -->
    <header class="navbar">

      <!-- 왼쪽: 로고 -->
      <div class="nav-left" @click="goHome">
        <img src="@/assets/archivinator-text-logo.png" class="logo" />
      </div>

      <!-- 가운데: 메뉴 -->
      <nav class="nav-center">
        <router-link to="/trend" class="nav-item">트렌드</router-link>
        <router-link to="/recommend" class="nav-item">추천</router-link>
        <router-link to="/mypage" class="nav-item">마이페이지</router-link>
      </nav>

      <!-- 오른쪽: Login / Logout -->
      <div class="nav-right">
        <span
          v-if="!isLoggedIn"
          class="auth-btn"
          @click="goLogin"
        >
          Login
        </span>

        <span
          v-else
          class="auth-btn"
          @click="logout"
        >
          Logout
        </span>
      </div>

    </header>

    <!-- 본문 -->
    <main class="main-content">
      <router-view />
    </main>

  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();

/* =========================
   로그인 상태 (반응형)
========================= */
const isLoggedIn = ref(false);

const syncLoginState = () => {
  isLoggedIn.value = !!localStorage.getItem("guest_id");
};

onMounted(syncLoginState);

/* =========================
   Actions
========================= */
const goHome = () => {
  router.push("/");
};

const goLogin = () => {
  router.push("/login");
};

const logout = () => {
  localStorage.removeItem("guest_id");
  alert("로그아웃 되었습니다.");
  syncLoginState();      // ⭐ 핵심
  router.push("/");
};
</script>

<style scoped>
/* 전체 레이아웃 */
.layout {
  width: 100%;
}

/* 네비바 */
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 100px;

  background: white;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);

  display: flex;
  align-items: center;
  justify-content: space-between;

  padding: 0 40px;
  z-index: 50;
}

/* 로고 */
.logo {
  height: 120px;
  cursor: pointer;
}

/* 메뉴 */
.nav-center {
  display: flex;
  justify-content: center;
  gap: 120px; /* 메뉴 3개라 기존 150px는 너무 넓을 수 있어 적당히 조정 */
  flex-grow: 1;
}

.nav-item {
  text-decoration: none;
  font-weight: 600;
  color: #333;
  font-size: 20px;
}
.nav-item:hover {
  color: #000;
}

/* 오른쪽: 인증 버튼 */
.nav-right {
  font-size: 14px;
}

.auth-btn {
  cursor: pointer;
  color: #666;
  font-weight: 500;
}

.auth-btn:hover {
  color: #000;
}

/* 본문영역 */
.main-content {
  padding-top: 100px; /* navbar 공간 확보 */
  width: 100%;
}
</style>
