import { createRouter, createWebHistory } from "vue-router";

import MainLayout from "../layouts/MainLayout.vue";

// 인증
import LoginView from "@/views/LoginView.vue";
import RegisterView from "@/views/RegisterView.vue";

// 메인 화면
import HomeView from "@/views/HomeView.vue";
import SearchResultView from "@/views/SearchResultView.vue";
import PaperDetailView from "@/views/PaperDetailView.vue";
import MyPageView from "@/views/MyPageView.vue";
import AuthorView from "@/views/AuthorView.vue";
import RecommendView from "@/views/RecommendView.vue";
import TrendView from "@/views/TrendView.vue";

// ✅ Chatbot
import ChatbotView from "@/views/ChatbotView.vue";

// ❌ 제거: 연구 활동 라우트용 View
// import ActivityCalendarView from "@/views/ActivityCalendarView.vue";
// import ReadingBoardView from "@/views/ReadingBoardView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),

  routes: [
    /* =========================
       Auth (Layout ❌)
    ========================= */
    {
      path: "/login",
      name: "login",
      component: LoginView,
    },
    {
      path: "/register",
      name: "register",
      component: RegisterView,
    },

    /* =========================
       Main (Layout ⭕)
    ========================= */
    {
      path: "/",
      component: MainLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: "",
          name: "home",
          component: HomeView,
        },
        {
          path: "search",
          name: "search",
          component: SearchResultView,
          props: (route) => ({ query: route.query }),
        },
        {
          path: "paper/:id",
          name: "paper-detail",
          component: PaperDetailView,
          props: true,
        },
        {
          path: "author/:id",
          name: "author",
          component: AuthorView,
          props: true,
        },
        {
          path: "mypage",
          name: "mypage",
          component: MyPageView,
        },
        {
          path: "recommend",
          name: "recommend",
          component: RecommendView,
        },
        {
          path: "trend",
          name: "trend",
          component: TrendView,
        },

        // ✅ Chatbot
        {
          path: "chat",
          name: "chat",
          component: ChatbotView,
        },

        // ❌ 제거: 연구달력/연구현황 라우트
        // {
        //   path: "activity",
        //   name: "activity",
        //   component: ActivityCalendarView,
        // },
        // {
        //   path: "reading",
        //   name: "reading",
        //   component: ReadingBoardView,
        // },
      ],
    },

    /* =========================
       Fallback
    ========================= */
    {
      path: "/:pathMatch(.*)*",
      redirect: "/",
    },
  ],
});

/* =========================
   🔐 Global Auth Guard
========================= */
router.beforeEach((to, from, next) => {
  const guestId = localStorage.getItem("guest_id");

  // 로그인 필요 페이지
  if (to.matched.some((r) => r.meta.requiresAuth)) {
    if (!guestId) {
      return next("/login");
    }
  }

  // 이미 로그인 상태에서 login 접근 방지
  if ((to.path === "/login" || to.path === "/register") && guestId) {
    return next("/");
  }

  next();
});

export default router;
