<template>
  <nav class="navbar">
    <div class="nav-left">
      <img
        src="@/assets/archivinator-text-logo.png"
        class="logo"
        @click="goHome"
      />

      <router-link to="/trend" class="nav-item">트렌드</router-link>
      <router-link to="/recommend" class="nav-item">추천</router-link>
      <router-link to="/mypage" class="nav-item">마이페이지</router-link>
    </div>
  </nav>
</template>

<script setup>
import { useRouter } from "vue-router";
const router = useRouter();

const goHome = () => {
  router.push({ name: "home" });
};
</script>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 70px;
  background: white;
  display: flex;
  align-items: center;
  padding: 0 40px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  z-index: 100;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 30px;
}

.logo {
  height: 32px;
  cursor: pointer;
}

.nav-item {
  text-decoration: none;
  color: #333;
  font-weight: 600;
}

.nav-item:hover {
  color: #111;
}
</style>
