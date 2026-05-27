<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { NCard, NGrid, NGi, NSpace, NTag, NStatistic, NButton, useMessage } from 'naive-ui'
import dayjs from 'dayjs'
import { useUserStore } from '@/stores/user'
import { reportApi, type MonthlyOverview } from '@/api/reports'

const message = useMessage()
const user = useUserStore()
const overview = ref<MonthlyOverview | null>(null)
const ready = ref(false)

onMounted(async () => {
  if (!user.profile) await user.fetchMe()
  try {
    overview.value = await reportApi.monthly(dayjs().format('YYYY-MM'))
  } catch (e) {
    message.warning((e as Error).message)
  } finally {
    ready.value = true
  }
})
</script>

<template>
  <n-space vertical size="large">
    <n-card title="欢迎">
      <template v-if="ready && user.profile">
        当前用户：<strong>{{ user.profile.nickname || user.profile.email }}</strong>
        <n-tag v-if="user.profile.is_admin" type="warning" style="margin-left: 8px">admin</n-tag>
      </template>
    </n-card>

    <n-card :title="`本月概览（${dayjs().format('YYYY-MM')}）`">
      <n-grid v-if="overview" :cols="5" x-gap="16">
        <n-gi><n-statistic label="本月支出" :value="overview.bill_expense" /></n-gi>
        <n-gi><n-statistic label="账单收入" :value="overview.bill_income" /></n-gi>
        <n-gi><n-statistic label="申报收入" :value="overview.declared_income" /></n-gi>
        <n-gi><n-statistic label="月末资产" :value="overview.asset_total" /></n-gi>
        <n-gi><n-statistic label="净值变化" :value="overview.net_worth_change" /></n-gi>
      </n-grid>
    </n-card>

    <n-card title="下一步建议">
      <n-space>
        <n-button @click="$router.push('/settings/categories')">建分类</n-button>
        <n-button @click="$router.push('/settings/ai/credentials')">配 AI 凭据</n-button>
        <n-button @click="$router.push('/settings/ai/strategies')">写 AI 策略</n-button>
        <n-button @click="$router.push('/settings/pipeline')">编排 Pipeline</n-button>
        <n-button type="primary" @click="$router.push('/bills/upload')">上传账单</n-button>
      </n-space>
    </n-card>
  </n-space>
</template>
