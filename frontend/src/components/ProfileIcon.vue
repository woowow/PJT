<template>
  <img 
    src="@/assets/profile-icon.png" 
    class="profile-icon"
    @click="goMyPage"
  />
</template>

<script setup>
import { useRouter } from "vue-router";

const router = useRouter();

const goMyPage = () => {
  router.push("/mypage");
};
</script>

<style scoped>
.profile-icon {
  width: 40px;
  position: fixed;     /* 화면 우측 상단 고정 */
  top: 36px;
  right: 40px;
  cursor: pointer;
  z-index: 999;
}
</style>
