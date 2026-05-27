<script setup lang="ts">
import { h, onMounted, ref, watch } from 'vue'
import {
  NCard, NDataTable, NSpace, NButton, NInput, NSelect, NPopconfirm,
  NModal, NForm, NFormItem, NDatePicker, NInputGroup, useMessage,
  type DataTableColumns,
} from 'naive-ui'
import dayjs from 'dayjs'
import { assetApi, type Asset, type AssetType } from '@/api/finance'

const message = useMessage()
const monthTs = ref<number>(dayjs().startOf('month').valueOf())
const month = () => dayjs(monthTs.value).format('YYYY-MM')
const list = ref<Asset[]>([])
const showModal = ref(false)
const editing = ref<Partial<Asset>>({})

const showCopy = ref(false)
const copyFromMonthTs = ref<number>(dayjs().subtract(1, 'month').startOf('month').valueOf())
const copyOverwrite = ref(false)

const typeOptions: { label: string; value: AssetType }[] = [
  { label: '现金', value: 'cash' },
  { label: '存款', value: 'deposit' },
  { label: '股票', value: 'stock' },
  { label: '基金', value: 'fund' },
  { label: '其他', value: 'other' },
]

async function load() {
  list.value = await assetApi.list(month())
}

watch(monthTs, load)

function openCreate() {
  editing.value = { snapshot_month: month(), asset_type: 'cash', account_name: '', amount: '0.00', remark: '' }
  showModal.value = true
}

function openEdit(row: Asset) {
  editing.value = { ...row }
  showModal.value = true
}

async function save() {
  try {
    if (editing.value.id) {
      await assetApi.patch(editing.value.id, editing.value)
    } else {
      await assetApi.create({
        snapshot_month: editing.value.snapshot_month!,
        asset_type: editing.value.asset_type!,
        account_name: editing.value.account_name!,
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

async function remove(row: Asset) {
  try {
    await assetApi.remove(row.id)
    await load()
    message.success('已删除')
  } catch (e) {
    message.error((e as Error).message)
  }
}

async function doCopy() {
  try {
    const from = dayjs(copyFromMonthTs.value).format('YYYY-MM')
    const res = await assetApi.copy(from, month(), copyOverwrite.value)
    message.success(`已从 ${res.from} 复制 ${res.copied} 条到 ${res.to}`)
    showCopy.value = false
    await load()
  } catch (e) {
    message.error((e as Error).message)
  }
}

const columns: DataTableColumns<Asset> = [
  { title: '类型', key: 'asset_type', width: 90, render: (r) => typeOptions.find((t) => t.value === r.asset_type)?.label || r.asset_type },
  { title: '账户', key: 'account_name' },
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
  <n-card title="资产录入">
    <template #header-extra>
      <n-space>
        <n-date-picker v-model:value="monthTs" type="month" />
        <n-button size="small" @click="showCopy = true">从上月复制</n-button>
        <n-button size="small" type="primary" @click="openCreate">新增</n-button>
      </n-space>
    </template>
    <n-data-table :columns="columns" :data="list" :row-key="(r) => r.id" />

    <n-modal v-model:show="showModal" preset="card" :title="editing.id ? '编辑资产' : '新增资产'" style="width: 480px">
      <n-form label-placement="left" label-width="80">
        <n-form-item label="月份">
          <n-input v-model:value="editing.snapshot_month" />
        </n-form-item>
        <n-form-item label="类型">
          <n-select v-model:value="editing.asset_type" :options="typeOptions" />
        </n-form-item>
        <n-form-item label="账户">
          <n-input v-model:value="editing.account_name" />
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

    <n-modal v-model:show="showCopy" preset="card" title="复制资产快照" style="width: 420px">
      <n-form label-placement="left" label-width="100">
        <n-form-item label="源月份">
          <n-date-picker v-model:value="copyFromMonthTs" type="month" />
        </n-form-item>
        <n-form-item label="目标月份">
          <n-input :value="month()" readonly />
        </n-form-item>
        <n-form-item label="覆盖已有">
          <n-input :value="copyOverwrite ? '是' : '否'" readonly @click="copyOverwrite = !copyOverwrite" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCopy = false">取消</n-button>
          <n-button type="primary" @click="doCopy">执行复制</n-button>
        </n-space>
      </template>
    </n-modal>
  </n-card>
</template>
