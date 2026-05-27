<script setup lang="ts">
import { h, onMounted, ref, watch } from 'vue'
import {
  NCard, NDataTable, NSpace, NButton, NInput, NPopconfirm,
  NModal, NForm, NFormItem, NDatePicker, useMessage,
  type DataTableColumns,
} from 'naive-ui'
import dayjs from 'dayjs'
import { incomeApi, type Income } from '@/api/finance'

const message = useMessage()
const yearTs = ref<number>(dayjs().startOf('year').valueOf())
const yearStr = () => dayjs(yearTs.value).format('YYYY')
const list = ref<Income[]>([])
const showModal = ref(false)
const editing = ref<Partial<Income>>({})

async function load() {
  list.value = await incomeApi.list({ year: yearStr() })
}

watch(yearTs, load)

function openCreate() {
  editing.value = { year_month: dayjs().format('YYYY-MM'), source: '', amount: '0.00', remark: '' }
  showModal.value = true
}

function openEdit(row: Income) {
  editing.value = { ...row }
  showModal.value = true
}

async function save() {
  try {
    if (editing.value.id) {
      await incomeApi.patch(editing.value.id, editing.value)
    } else {
      await incomeApi.create({
        year_month: editing.value.year_month!,
        source: editing.value.source!,
        amount: editing.value.amount!,
        remark: editing.value.remark ?? null,
      })
    }
    showModal.value = false
    await load()
    message.success('已保存')
  } catch (e) {
    message.error((e as Error).message)
  }
}

async function remove(row: Income) {
  try {
    await incomeApi.remove(row.id)
    await load()
    message.success('已删除')
  } catch (e) {
    message.error((e as Error).message)
  }
}

const columns: DataTableColumns<Income> = [
  { title: '年月', key: 'year_month', width: 100 },
  { title: '来源', key: 'source' },
  { title: '金额', key: 'amount', align: 'right' },
  { title: '备注', key: 'remark' },
  {
    title: '操作',
    key: 'actions',
    width: 160,
    render: (row) =>
      h(NSpace, {}, () => [
        h(NButton, { size: 'tiny', onClick: () => openEdit(row) }, () => '编辑'),
        h(NPopconfirm, { onPositiveClick: () => remove(row) }, {
          trigger: () => h(NButton, { size: 'tiny', type: 'error' }, () => '删除'),
          default: () => '确认删除？',
        }),
      ]),
  },
]

onMounted(load)
</script>

<template>
  <n-card title="收入录入">
    <template #header-extra>
      <n-space>
        <n-date-picker v-model:value="yearTs" type="year" />
        <n-button size="small" type="primary" @click="openCreate">新增</n-button>
      </n-space>
    </template>
    <n-data-table :columns="columns" :data="list" :row-key="(r) => r.id" />

    <n-modal v-model:show="showModal" preset="card" :title="editing.id ? '编辑收入' : '新增收入'" style="width: 440px">
      <n-form label-placement="left" label-width="80">
        <n-form-item label="年月">
          <n-input v-model:value="editing.year_month" placeholder="YYYY-MM" />
        </n-form-item>
        <n-form-item label="来源">
          <n-input v-model:value="editing.source" placeholder="工资 / 理财 / 奖金 ..." />
        </n-form-item>
        <n-form-item label="金额">
          <n-input v-model:value="editing.amount" />
        </n-form-item>
        <n-form-item label="备注">
          <n-input v-model:value="editing.remark" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" @click="save">保存</n-button>
        </n-space>
      </template>
    </n-modal>
  </n-card>
</template>
