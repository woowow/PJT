<template>
  <div class="login-container">

    <!-- 왼쪽 상단 ARCHIVINATOR 텍스트 로고 -->
    <div class="brand-top">
      <img src="@/assets/archivinator-text-logo.png" class="brand-text" />
    </div>

    <!-- 왼쪽 로그인 카드 -->
    <div class="login-card">
      <h2>Welcome !</h2>

      <div class="subtitle">Sign in to</div>
      <p class="desc">Access the world of academic search</p>

      <label class="input-label">User name</label>
      <input type="text" v-model="username" class="input-box" placeholder="Enter your user name" />

      <label class="input-label">Password</label>
      <div class="password-wrapper">
        <input
          type="password"
          v-model="password"
          class="input-box"
          placeholder="Enter your Password"
        />
      </div>

      <div class="options-row">
        <label class="remember">
          <input type="checkbox" /> Remember me
        </label>
        <span class="forgot">Forgot Password ?</span>
      </div>

      <button class="login-btn" @click="doLogin">Login</button>

      <div class="register-row">
        Don’t have an Account ?
        <span class="register-link" @click="goRegister">Register</span>
      </div>
    </div>

    <!-- 오른쪽 로고 -->
    <div class="right-hero">
      <img src="@/assets/main_image.png" class="hero-logo" />
    </div>

  </div>
</template>


<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";   // 추가!
import api from "@/api";

const router = useRouter();
const username = ref("");
const password = ref("");

const doLogin = async () => {
  if (!username.value || !password.value) {
    alert("Please enter your ID and password.");
    return;
  }

  try {
    const res = await api.post("/auth/login/", {
      username: username.value,
      password: password.value,
    });

    // 로그인 성공
    localStorage.setItem("guest_id", res.data.guest_id);
    window.location.href = "/";
    router.push("/");
  } catch (err) {
    alert("아이디 또는 비밀번호가 틀렸습니다.");
  }
};

const goRegister = () => {
  router.push("/register");
};

</script>


<style scoped>
.login-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100vh;
  padding: 40px 120px;
  background: #f7f8fc;
}

/* 왼쪽 상단 텍스트 로고 */
.brand-top {
  position: absolute;
  top: 40px;
  left: 120px;
}

.brand-text {
  width: 200px;
}


/* 로그인 카드 박스 */
.login-card {
  width: 600px;
  padding: 40px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.06);
}

.login-card h2 {
  font-size: 28px;
  margin-bottom: 8px;
}

.subtitle {
  font-size: 20px;
  font-weight: 600;
}

.desc {
  font-size: 14px;
  color: #666;
  margin-bottom: 25px;
}

.input-label {
  margin-top: 18px;
  display: inline-block;
  font-size: 14px;
  font-weight: 600;
}

.input-box {
  width: 100%;
  height: 45px;
  border: 1px solid #ddd;
  border-radius: 10px;
  padding: 0 12px;
  margin-top: 6px;
  outline: none;
  background: #fafafa;
}

.input-box:focus {
  border-color: #000;
}

/* 패스워드 영역 */
.password-wrapper {
  position: relative;
}

.options-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  margin: 10px 0 20px;
}

.remember input {
  margin-right: 5px;
}

.forgot {
  color: #444;
  cursor: pointer;
}

.login-btn {
  width: 100%;
  height: 48px;
  background: black;
  color: white;
  border-radius: 10px;
  border: none;
  margin-top: 10px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
}

.register-row {
  margin-top: 18px;
  font-size: 14px;
  text-align: center;
}

.register-link {
  margin-left: 6px;
  font-weight: 600;
  cursor: pointer;
}


/* 오른쪽 히어로 이미지 영역 */
.right-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.hero-logo {
  width: 1000px;         /* 기존보다 크게 확대 */
  margin-bottom: 10px;
}

.hero-text {
  font-size: 38px;
  font-weight: 900;
  letter-spacing: 2px;
  color: #d29e42;
  text-shadow: 0px 2px 3px rgba(0,0,0,0.15);
}
</style>
