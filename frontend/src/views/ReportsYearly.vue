<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { NCard, NSpace, NDatePicker, NGrid, NGi, NStatistic, useMessage } from 'naive-ui'
import dayjs from 'dayjs'
import { reportApi, type YearlyReport } from '@/api/reports'
import EChart from '@/components/EChart.vue'

const message = useMessage()
const yearTs = ref<number>(dayjs().startOf('year').valueOf())
const data = ref<YearlyReport | null>(null)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    data.value = await reportApi.yearly(dayjs(yearTs.value).year())
  } catch (e) {
    message.error((e as Error).message)
  } finally {
    loading.value = false
  }
}

watch(yearTs, load)
onMounted(load)

const chartOption = computed(() => {
  const buckets = data.value?.buckets || []
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['账单收入', '账单支出', '收支差额'] },
    xAxis: { type: 'category', data: buckets.map((b) => b.year_month.slice(5)) },
    yAxis: { type: 'value' },
    series: [
      { name: '账单收入', type: 'bar', data: buckets.map((b) => Number(b.income)), itemStyle: { color: '#52c41a' } },
      { name: '账单支出', type: 'bar', data: buckets.map((b) => Number(b.expense)), itemStyle: { color: '#f5222d' } },
      { name: '收支差额', type: 'line', data: buckets.map((b) => Number(b.balance)), itemStyle: { color: '#1f6feb' } },
    ],
  }
})
</script>

<template>
  <n-space vertical size="large">
    <n-card title="全年收支">
      <template #header-extra>
        <n-date-picker v-model:value="yearTs" type="year" />
      </template>
      <n-grid v-if="data" :cols="3" x-gap="16">
        <n-gi><n-statistic label="年度账单收入" :value="data.total_income" /></n-gi>
        <n-gi><n-statistic label="年度账单支出" :value="data.total_expense" /></n-gi>
        <n-gi><n-statistic label="账单收支差额" :value="data.total_balance" /></n-gi>
      </n-grid>
    </n-card>
    <n-card title="逐月对比">
      <e-chart v-if="data" :option="chartOption" height="380px" />
    </n-card>
  </n-space>
</template>
