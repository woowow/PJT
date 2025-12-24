<template>
  <div class="chat-wrap">
    <div class="chat-header">
      <h2>Archivinator 🧞</h2>
      <p class="sub">
        논문/주제/키워드/트렌드 질문을 해보세요. (예: “이번 주 트렌드 TOP5”, “내 관심 주제로 추천해줘”)
      </p>
    </div>

    <div class="chat-box" ref="chatBox">
      <div v-if="messages.length === 0" class="empty">
        당신이 생각하는 논문을 맞춰보죠💬.
      </div>

      <div
        v-for="(m, idx) in messages"
        :key="idx"
        class="msg"
        :class="m.role"
      >
        <div class="bubble">
          <div class="role">{{ m.role === "user" ? "나" : "챗봇" }}</div>
          <div class="content" v-text="m.content"></div>
        </div>
      </div>

      <div v-if="loading" class="msg assistant">
        <div class="bubble">
          <div class="role">챗봇</div>
          <div class="content">답변 생성 중…</div>
        </div>
      </div>
    </div>

    <div class="input-row">
      <input
        v-model="input"
        class="input"
        type="text"
        placeholder="질문을 입력하세요"
        @keyup.enter="send"
        :disabled="loading"
      />
      <button class="btn" @click="send" :disabled="loading || !input.trim()">
        전송
      </button>
    </div>

    <div class="quick">
      <button class="qbtn" @click="fill('이번 주 트렌드 논문 TOP 5 알려줘')">트렌드 TOP5</button>
      <button class="qbtn" @click="fill('내 관심 주제로 추천해줘')">내 관심 추천</button>
    </div>

    <div v-if="error" class="error">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from "vue";
import api from "@/api.js";

const input = ref("");
const loading = ref(false);
const error = ref("");
const messages = ref([]);
const chatBox = ref(null);

const scrollToBottom = async () => {
  await nextTick();
  if (chatBox.value) {
    chatBox.value.scrollTop = chatBox.value.scrollHeight;
  }
};

const fill = (text) => {
  input.value = text;
};

const send = async () => {
  const text = input.value.trim();
  if (!text || loading.value) return;

  error.value = "";

  // push user message
  messages.value.push({ role: "user", content: text });
  input.value = "";
  await scrollToBottom();

  loading.value = true;

  try {
    const guest_id = localStorage.getItem("guest_id");

    // history는 최소화(최근 10개)해서 전달
    const history = messages.value.slice(-10).map((m) => ({
      role: m.role,
      content: m.content,
    }));

    const res = await api.post("/chatbot/", {
      message: text,
      guest_id: guest_id ? Number(guest_id) : null,
      history,
    });

    const reply = res?.data?.reply ?? "응답을 받지 못했습니다.";
    messages.value.push({ role: "assistant", content: reply });
    await scrollToBottom();
  } catch (e) {
    const msg =
      e?.response?.data?.error ||
      e?.message ||
      "챗봇 호출 중 오류가 발생했습니다.";
    error.value = msg;
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.chat-wrap {
  max-width: 980px;
  margin: 0 auto;
  padding: 24px 24px 40px;
}

.chat-header h2 {
  margin: 0;
  font-size: 24px;
}
.sub {
  margin-top: 8px;
  color: #666;
  font-size: 14px;
}

.chat-box {
  margin-top: 16px;
  height: 520px;
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 12px;
  padding: 16px;
  overflow-y: auto;
  background: #fff;
}

.empty {
  color: #888;
  padding: 12px;
}

.msg {
  display: flex;
  margin: 10px 0;
}

.msg.user {
  justify-content: flex-end;
}
.msg.assistant {
  justify-content: flex-start;
}

.bubble {
  max-width: 72%;
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 12px;
  padding: 10px 12px;
  background: #fafafa;
}

.msg.user .bubble {
  background: #f3f6ff;
}

.role {
  font-size: 12px;
  color: #666;
  margin-bottom: 6px;
}

.content {
  white-space: pre-wrap;
  line-height: 1.5;
  color: #222;
  font-size: 14px;
}

.input-row {
  margin-top: 14px;
  display: flex;
  gap: 10px;
}

.input {
  flex: 1;
  padding: 12px 12px;
  border-radius: 10px;
  border: 1px solid rgba(0,0,0,0.15);
  outline: none;
}

.btn {
  padding: 12px 16px;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  background: #111;
  color: #fff;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.quick {
  margin-top: 12px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.qbtn {
  border: 1px solid rgba(0,0,0,0.15);
  background: #fff;
  border-radius: 999px;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 13px;
}

.qbtn:hover {
  background: #f7f7f7;
}

.error {
  margin-top: 12px;
  color: #b00020;
  font-size: 13px;
}
</style>
