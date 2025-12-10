import { createRouter, createWebHistory } from "vue-router";

import MainLayout from "../layouts/MainLayout.vue";

// 개별 페이지
import LoginView from "@/views/LoginView.vue";
import RegisterView from "@/views/RegisterView.vue";
import HomeView from "@/views/HomeView.vue";
import SearchResultView from "@/views/SearchResultView.vue";
import PaperDetailView from "@/views/PaperDetailView.vue";
import MyPageView from "@/views/MyPageView.vue";
import AuthorView from "@/views/AuthorView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),

  routes: [
    // 로그인 & 회원가입은 레이아웃 제외
    {
      path: "/",
      name: "login",
      component: LoginView,
    },
    {
      path: "/register",
      name: "register",
      component: RegisterView,
    },

    // 로그인 이후는 모두 MainLayout 안에서 렌더링
    {
      path: "/",
      component: MainLayout,
      children: [
        {
          path: "home",
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
          path: "mypage",
          name: "mypage",
          component: MyPageView,
        },
        {
          path: "author/:id",
          name: "author",
          component: AuthorView,
          props: true,
        },
      ],
    },
  ],
});

export default router;
