<script setup lang="ts">
import { useRoute } from 'vue-router'
import { NCard, NEmpty } from 'naive-ui'

const route = useRoute()
</script>

<template>
  <n-card :title="(route.meta.title as string) || '页面'">
    <n-empty description="该页面将在后续 milestone 实现" />
  </n-card>
</template>
