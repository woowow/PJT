// import { defineStore } from "pinia";

// export const useBookmarkStore = defineStore("bookmark", {
//   state: () => ({
//     bookmarks: [
//       {
//         id: 1,
//         title: "Reinforcement Learning Survey",
//         author: "Kim",
//         year: 2024,
//         citation: 88,
//         institution: "Stanford",
//         bookmarkedAt: "2025-12-10"
//       },
//       {
//         id: 2,
//         title: "Efficient LLM Inference",
//         author: "Lee",
//         year: 2023,
//         citation: 55,
//         institution: "KAIST",
//         bookmarkedAt: "2025-12-12"
//       },
//       {
//         id: 3,
//         title: "Attention Is All You Need",
//         author: "Vaswani",
//         year: 2017,
//         citation: 150000,
//         institution: "Google",
//         bookmarkedAt: "2025-12-12"
//       }
//     ]   // { id, title, bookmarkedAt, ... }
//   }),

//   getters: {
//     isBookmarked: (state) => (paperId) =>
//       state.bookmarks.some(b => b.id === paperId),

//     bookmarksByDate: (state) => {
//       const map = {};
//       state.bookmarks.forEach(b => {
//         const date = b.bookmarkedAt;
//         if (!map[date]) map[date] = [];
//         map[date].push(b);
//       });
//       return map;
//     }
//   },

//   actions: {
//     toggleBookmark(paper) {
//       const idx = this.bookmarks.findIndex(b => b.id === paper.id);

//       if (idx > -1) {
//         // ❌ 즐겨찾기 해제
//         this.bookmarks.splice(idx, 1);
//       } else {
//         // ⭐ 즐겨찾기 추가
//         this.bookmarks.push({
//           ...paper,
//           bookmarkedAt: new Date().toISOString().slice(0, 10)
//         });
//       }
//     }
//   }
// });
