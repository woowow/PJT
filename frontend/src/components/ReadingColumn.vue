<template>
  <div class="column">
    <h3 class="column-title">{{ title }}</h3>

    <draggable
      :list="list"
      group="papers"
      item-key="id"
      class="column-list"
    >
      <template #item="{ element }">
        <PaperCard :paper="element" />
      </template>
    </draggable>
  </div>
</template>

<script setup>
import draggable from "vuedraggable";
import PaperCard from "@/components/PaperCard.vue";

defineProps({
  title: String,
  list: Array,
});
</script>

<style scoped>
.column {
  background: #f6f7fb;
  border-radius: 14px;
  padding: 16px;
  min-height: 500px;
}

.column-title {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 14px;
}

.column-list {
  min-height: 300px;
}
</style>
