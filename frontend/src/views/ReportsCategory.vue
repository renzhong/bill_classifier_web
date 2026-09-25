<script setup lang="ts">
import { computed, h, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NSpace, NDatePicker, NDataTable, NButton, useMessage, type DataTableColumns } from 'naive-ui'
import dayjs from 'dayjs'
import { reportApi, type CategorySummary, type CategoryBucket } from '@/api/reports'
import EChart from '@/components/EChart.vue'

const router = useRouter()
const message = useMessage()
const monthTs = ref<number>(dayjs().startOf('month').valueOf())
const data = ref<CategorySummary | null>(null)

async function load() {
  try {
    data.value = await reportApi.categorySummary(dayjs(monthTs.value).format('YYYY-MM'))
  } catch (e) {
    message.error((e as Error).message)
  }
}

watch(monthTs, load)
onMounted(load)

const chartOption = computed(() => ({
  color: ['#a6c8ff', '#9ef0f0', '#d4bbff', '#ffb3b8', '#ffdfad', '#c6c6c6'],
  tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
  legend: { type: 'scroll', orient: 'vertical', left: 10, top: 10, bottom: 10 },
  series: [
    {
      type: 'pie',
      radius: ['35%', '70%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
      label: { formatter: '{b}\n{d}%' },
      data: (data.value?.buckets || []).map((b) => ({ name: b.category_name || '(未分类)', value: Number(b.amount) })),
    },
  ],
}))

function jumpDetail(row: CategoryBucket) {
  if (!data.value) return
  router.push({ path: '/bills', query: { month: data.value.year_month,
    report_expense: '1',
    ...(row.category_id === null ? { unclassified: '1' } : { category_id: row.category_id }) } })
}

const columns = computed<DataTableColumns<CategoryBucket>>(() => [
  { title: '分类', key: 'category_name', render: (r) => r.category_name || '(未分类)' },
  { title: '金额', key: 'amount', align: 'right' },
  { title: '占比', key: 'percent', width: 100, render: (r) => `${r.percent}%` },
  { title: '条数', key: 'count', width: 80 },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render: (row) => h(NButton, { size: 'tiny', text: true, onClick: () => jumpDetail(row) }, () => '看明细'),
  },
])
</script>

<template>
  <n-space vertical size="large">
    <n-card title="分类汇总">
      <template #header-extra>
        <n-date-picker v-model:value="monthTs" type="month" />
      </template>
      <div v-if="data">
        <div style="margin-bottom: 12px"><strong>总支出：{{ data.total_expense }}</strong></div>
        <n-space :wrap="false" align="start">
          <e-chart :option="chartOption" height="380px" style="flex: 1; min-width: 360px" />
          <div style="flex: 1; min-width: 360px">
            <n-data-table :columns="columns" :data="data.buckets" :row-key="(r) => `${r.category_id}`" />
          </div>
        </n-space>
      </div>
    </n-card>
  </n-space>
</template>
