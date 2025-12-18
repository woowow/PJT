<template>
  <div class="register-container">

    <!-- 왼쪽 상단 ARCHIVINATOR 텍스트 로고 -->
    <div class="brand-top">
      <img src="@/assets/archivinator-text-logo.png" class="brand-text" />
    </div>

    <!-- 왼쪽 회원가입 카드 -->
    <div class="register-card">
      <h2>Welcome !</h2>

      <div class="subtitle">Sign up to</div>
      <p class="desc">Lorem Ipsum is simply</p>

      <!-- Email -->
      <label class="input-label">Email</label>
      <input 
        type="email"
        v-model="email"
        class="input-box"
        placeholder="Enter your email"
      />

      <!-- User name -->
      <label class="input-label">User name</label>
      <input 
        type="text"
        v-model="username"
        class="input-box"
        placeholder="Enter your user name"
      />

      <!-- Password -->
      <label class="input-label">Password</label>
      <div class="password-wrapper">
        <input
          :type="passwordVisible ? 'text' : 'password'"
          v-model="password"
          class="input-box password-input"
          placeholder="Enter your Password"
        />

        <!-- eye icon -->
        <span class="eye-icon" @click="passwordVisible = !passwordVisible">
          {{ passwordVisible ? "🙈" : "👁" }}
        </span>
      </div>

      <!-- Confirm Password -->
      <label class="input-label">Confirm Password</label>
      <div class="password-wrapper">
        <input
          :type="confirmVisible ? 'text' : 'password'"
          v-model="confirmPassword"
          class="input-box password-input"
          placeholder="Confirm your Password"
        />
        <span class="eye-icon" @click="confirmVisible = !confirmVisible">
          {{ confirmVisible ? "🙈" : "👁" }}
        </span>
      </div>

      <!-- Register Button -->
      <button class="register-btn" @click="doRegister">
        Register
      </button>

      <div class="login-row">
        Already have an Account ?
        <span class="login-link" @click="goLogin">Login</span>
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
import { useRouter } from "vue-router";
import api from "@/api";

const router = useRouter();

const email = ref("");
const username = ref("");
const password = ref("");
const confirmPassword = ref("");

const passwordVisible = ref(false);
const confirmVisible = ref(false);

const doRegister = async () => {
  if (!email.value || !username.value || !password.value || !confirmPassword.value) {
    alert("Please fill in all fields.");
    return;
  }

  if (password.value !== confirmPassword.value) {
    alert("Passwords do not match.");
    return;
  }

  try {
    await api.post("/auth/register/", {
      username: username.value,
      password: password.value,
    });

    alert("Registered successfully!");
    router.push("/");   // 로그인 화면
  } catch (err) {
    alert("이미 존재하는 아이디입니다.");
  }
};

const goLogin = () => router.push("/");
</script>


<style scoped>
.register-container {
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

/* 회원가입 카드 */
.register-card {
  width: 600px;
  padding: 40px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.06);
}

.register-card h2 {
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
  width: 95%;
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

/* password wrapper */
.password-wrapper {
  position: relative;
}

.password-input {
  height: 45px;
  padding-right: 12px;
}

/* eye icon (unicode icon) */
.eye-icon {
  position: absolute;
  right: 25px;
  top: 50%;
  transform: translateY(-50%);
  cursor: pointer;
  font-size: 20px;
  opacity: 0.7;
}

.eye-icon:hover {
  opacity: 1;
}

/* Register Button */
.register-btn {
  width: 100%;
  height: 48px;
  background: black;
  color: white;
  border-radius: 10px;
  border: none;
  margin-top: 20px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
}

.login-row {
  margin-top: 18px;
  font-size: 14px;
  text-align: center;
}

.login-link {
  margin-left: 6px;
  font-weight: 600;
  cursor: pointer;
}

/* 오른쪽 히어로 이미지 */
.right-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.hero-logo {
  width: 1000px;
}
</style>
