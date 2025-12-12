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
        <router-link to="/activity" class="nav-item">연구달력</router-link>
        <router-link to="/reading" class="nav-item">연구현황</router-link>
      </nav>

      <!-- 오른쪽: 로그아웃 -->
      <div class="nav-right">
        <span class="logout-btn" @click="logout">Logout</span>
      </div>

    </header>

    <!-- 본문 -->
    <main class="main-content">
      <!-- ★ slot 대신 router-view 를 반드시 사용해야 한다 -->
      <router-view />
    </main>

  </div>
</template>

<script setup>
import { useRouter } from "vue-router";
const router = useRouter();

const goHome = () => router.push("/home");

const logout = () => {
  localStorage.removeItem("user");
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
  gap: 150px;
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

/* 오른쪽: 로그아웃 */
.nav-right {
  font-size: 14px;
}

.logout-btn {
  cursor: pointer;
  color: #666;
  font-weight: 500;
}

.logout-btn:hover {
  color: #000;
}

/* 본문영역 */
.main-content {
  padding-top: 100px; /* navbar 공간 확보 */
  width: 100%;
}
</style>
