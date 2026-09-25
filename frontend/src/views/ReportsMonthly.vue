<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { NCard, NSpace, NDatePicker, NGrid, NGi, NStatistic, NDataTable, NText, useMessage, type DataTableColumns } from 'naive-ui'
import dayjs from 'dayjs'
import { reportApi, type BalanceReport, type MonthlyOverview } from '@/api/reports'

const message = useMessage()
const monthTs = ref<number>(dayjs().startOf('month').valueOf())
const overview = ref<MonthlyOverview | null>(null)
const balance = ref<BalanceReport | null>(null)

async function load() {
  const month = dayjs(monthTs.value).format('YYYY-MM')
  try {
    const [o, b] = await Promise.all([reportApi.monthly(month), reportApi.balance(month)])
    overview.value = o
    balance.value = b
  } catch (e) {
    message.error((e as Error).message)
  }
}

watch(monthTs, load)
onMounted(load)

const typeLabel: Record<string, string> = {
  cash: '现金', deposit: '存款', stock: '股票', fund: '基金', other: '其他',
  manual: '自定义资产', investment: '投资估值',
}
const balanceColumns: DataTableColumns<{ asset_type: string; amount: string; count: number }> = [
  { title: '资产类型', key: 'asset_type', render: (r) => typeLabel[r.asset_type] || r.asset_type },
  { title: '账户数', key: 'count', width: 100 },
  { title: '金额', key: 'amount', align: 'right' },
]
</script>

<template>
  <n-space vertical size="large">
    <n-card title="单月汇总">
      <template #header-extra>
        <n-date-picker v-model:value="monthTs" type="month" />
      </template>
      <n-grid v-if="overview" :cols="5" x-gap="16">
        <n-gi><n-statistic label="账单支出" :value="overview.bill_expense" /></n-gi>
        <n-gi><n-statistic label="账单收入" :value="overview.bill_income" /></n-gi>
        <n-gi><n-statistic label="已录入收入合计" :value="overview.declared_income" /></n-gi>
        <n-gi><n-statistic label="资产合计" :value="overview.asset_total" /></n-gi>
        <n-gi><n-statistic label="净资产" :value="overview.net_assets" /></n-gi>
      </n-grid>
    </n-card>

    <n-card title="资产结构">
      <n-text v-if="balance && balance.buckets.length === 0" depth="3">本月尚未录入资产。</n-text>
      <template v-else-if="balance">
        <n-data-table :columns="balanceColumns" :data="balance.buckets" :row-key="(r) => r.asset_type" />
        <div style="margin-top: 12px; text-align: right">
          <strong>资产合计：{{ balance.asset_total }}</strong>
        </div>
      </template>
    </n-card>
  </n-space>
</template>
