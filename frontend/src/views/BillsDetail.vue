<script setup lang="ts">
import { computed, h, onMounted, reactive, ref } from 'vue'
import {
  NCard, NDataTable, NSpace, NSelect, NInput, NButton, NPagination,
  NDatePicker, NTag, NPopconfirm, useMessage, type DataTableColumns,
} from 'naive-ui'
import dayjs from 'dayjs'
import { billApi, type Bill, type BillListQuery } from '@/api/bills'
import { useMetaStore } from '@/stores/meta'

const message = useMessage()
const meta = useMetaStore()

const monthTs = ref<number | null>(dayjs().startOf('month').valueOf())
const filter = reactive<BillListQuery>({
  source: undefined,
  category_id: undefined,
  tag_id: undefined,
  keyword: undefined,
  page: 1,
  page_size: 50,
})

const data = ref<Bill[]>([])
const total = ref(0)
const loading = ref(false)

const sourceOptions = [
  { label: '全部', value: undefined as unknown as string },
  { label: '支付宝', value: 'alipay' },
  { label: '微信', value: 'wechat' },
]

async function load() {
  loading.value = true
  try {
    const q: BillListQuery = { ...filter }
    if (monthTs.value) q.month = dayjs(monthTs.value).format('YYYY-MM')
    const res = await billApi.list(q)
    data.value = res.items
    total.value = res.total
  } catch (e) {
    message.error((e as Error).message)
  } finally {
    loading.value = false
  }
}

function resetAndLoad() {
  filter.page = 1
  load()
}

async function onCategoryChange(row: Bill, newId: number | null) {
  try {
    await billApi.patch(row.id, { category_id: newId })
    message.success('已更新')
    load()
  } catch (e) {
    message.error((e as Error).message)
  }
}

async function reclassify(row: Bill) {
  try {
    const res = await billApi.reclassify(row.id)
    message.info(res.note || (res.queued ? '已入队' : '已完成'))
    load()
  } catch (e) {
    message.error((e as Error).message)
  }
}

const selectedIds = ref<number[]>([])

const columns = computed<DataTableColumns<Bill>>(() => [
  { type: 'selection' },
  { title: '时间', key: 'bill_time', width: 160, render: (r) => dayjs(r.bill_time).format('MM-DD HH:mm') },
  { title: '金额', key: 'amount', width: 100, align: 'right' },
  { title: '收/支', key: 'bill_type', width: 80 },
  {
    title: '分类',
    key: 'category_id',
    width: 160,
    render: (row) =>
      h(NSelect, {
        size: 'small',
        clearable: true,
        value: row.category_id,
        options: meta.categories.map((c) => ({ label: c.name, value: c.id })),
        onUpdateValue: (v: number | null) => onCategoryChange(row, v),
      }),
  },
  { title: '收款方', key: 'payee', ellipsis: { tooltip: true } },
  { title: '商品', key: 'item_name', ellipsis: { tooltip: true } },
  { title: '来源', key: 'source', width: 80 },
  { title: '命中策略', key: 'classify_strategy_type', width: 130 },
  {
    title: '状态',
    key: 'lifecycle',
    width: 100,
    render: (r) => h(NTag, { size: 'small' }, { default: () => r.lifecycle }),
  },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render: (row) => h(NButton, { size: 'tiny', text: true, onClick: () => reclassify(row) }, { default: () => '重分类' }),
  },
])

async function batchSetCategory(catId: number) {
  if (!selectedIds.value.length) return
  try {
    await billApi.batch({ ids: selectedIds.value, action: 'set_category', payload: { category_id: catId } })
    message.success('批量更新完成')
    selectedIds.value = []
    load()
  } catch (e) {
    message.error((e as Error).message)
  }
}

async function batchDelete() {
  if (!selectedIds.value.length) return
  try {
    await billApi.batch({ ids: selectedIds.value, action: 'delete' })
    message.success('批量删除完成')
    selectedIds.value = []
    load()
  } catch (e) {
    message.error((e as Error).message)
  }
}

onMounted(async () => {
  await meta.loadAll()
  load()
})
</script>

<template>
  <n-card title="账单明细">
    <n-space vertical>
      <n-space wrap>
        <n-date-picker v-model:value="monthTs" type="month" clearable @update:value="resetAndLoad" />
        <n-select
          v-model:value="filter.source"
          :options="sourceOptions"
          placeholder="来源"
          clearable
          style="width: 120px"
          @update:value="resetAndLoad"
        />
        <n-select
          v-model:value="filter.category_id"
          :options="meta.categories.map((c) => ({ label: c.name, value: c.id }))"
          placeholder="分类"
          clearable
          style="width: 160px"
          @update:value="resetAndLoad"
        />
        <n-select
          v-model:value="filter.tag_id"
          :options="meta.tags.map((t) => ({ label: t.name, value: t.id }))"
          placeholder="Tag"
          clearable
          style="width: 160px"
          @update:value="resetAndLoad"
        />
        <n-input
          v-model:value="filter.keyword"
          placeholder="关键词（payee / item）"
          clearable
          style="width: 220px"
          @keyup.enter="resetAndLoad"
        />
        <n-button @click="resetAndLoad" :loading="loading">查询</n-button>
      </n-space>

      <n-space v-if="selectedIds.length" wrap>
        <span>已选 {{ selectedIds.length }} 条</span>
        <n-select
          :options="meta.categories.map((c) => ({ label: `设为 ${c.name}`, value: c.id }))"
          placeholder="批量改类"
          style="width: 180px"
          @update:value="batchSetCategory"
        />
        <n-popconfirm @positive-click="batchDelete">
          <template #trigger><n-button type="error" size="small">批量删除</n-button></template>
          确认删除选中的 {{ selectedIds.length }} 条？
        </n-popconfirm>
      </n-space>

      <n-data-table
        :columns="columns"
        :data="data"
        :loading="loading"
        :row-key="(r: Bill) => r.id"
        @update:checked-row-keys="(keys: (string | number)[]) => (selectedIds = keys as number[])"
        :max-height="600"
      />
      <n-pagination
        v-model:page="filter.page"
        v-model:page-size="filter.page_size"
        :item-count="total"
        :page-sizes="[20, 50, 100, 200]"
        show-size-picker
        @update:page="load"
        @update:page-size="resetAndLoad"
      />
    </n-space>
  </n-card>
</template>
