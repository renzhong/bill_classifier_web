<script setup lang="ts">
import { h, onMounted, ref } from 'vue'
import {
  NCard, NDataTable, NSpace, NButton, NInput, NPopconfirm, NModal,
  NForm, NFormItem, NColorPicker, NInputNumber, useMessage, type DataTableColumns,
} from 'naive-ui'
import { categoryApi, type Category } from '@/api/meta'
import { useMetaStore } from '@/stores/meta'

const message = useMessage()
const meta = useMetaStore()
const list = ref<Category[]>([])
const showModal = ref(false)
const editing = ref<Partial<Category>>({})

async function load() {
  list.value = await categoryApi.list()
}

function openCreate() {
  editing.value = { name: '', display_name: '', color: '#1f6feb', sort_order: 0 }
  showModal.value = true
}

function openEdit(row: Category) {
  editing.value = { ...row }
  showModal.value = true
}

async function save() {
  try {
    if (editing.value.id) {
      await categoryApi.patch(editing.value.id, editing.value)
    } else {
      await categoryApi.create({
        name: editing.value.name!,
        display_name: editing.value.display_name ?? null,
        color: editing.value.color ?? null,
        sort_order: editing.value.sort_order ?? 0,
      })
    }
    showModal.value = false
    await load()
    await meta.reloadCategories()
    message.success('已保存')
  } catch (e) {
    message.error((e as Error).message)
  }
}

async function remove(row: Category) {
  try {
    await categoryApi.remove(row.id)
    message.success('已删除')
    await load()
    await meta.reloadCategories()
  } catch (e) {
    message.error((e as Error).message)
  }
}

async function moveDelta(row: Category, delta: number) {
  await categoryApi.patch(row.id, { sort_order: (row.sort_order ?? 0) + delta })
  await load()
  await meta.reloadCategories()
}

const columns: DataTableColumns<Category> = [
  { title: 'ID', key: 'id', width: 70 },
  { title: '名称', key: 'name' },
  { title: '展示名', key: 'display_name' },
  {
    title: '颜色',
    key: 'color',
    width: 120,
    render: (r) => h('span', { style: `display:inline-block;width:18px;height:18px;border-radius:3px;background:${r.color || '#ccc'}` }),
  },
  { title: '排序', key: 'sort_order', width: 90 },
  {
    title: '操作',
    key: 'actions',
    width: 280,
    render: (row) =>
      h(NSpace, {}, () => [
        h(NButton, { size: 'tiny', onClick: () => moveDelta(row, -1) }, () => '↑'),
        h(NButton, { size: 'tiny', onClick: () => moveDelta(row, 1) }, () => '↓'),
        h(NButton, { size: 'tiny', onClick: () => openEdit(row) }, () => '编辑'),
        h(NPopconfirm, { onPositiveClick: () => remove(row) }, {
          trigger: () => h(NButton, { size: 'tiny', type: 'error' }, () => '删除'),
          default: () => `确认删除 ${row.name}？`,
        }),
      ]),
  },
]

onMounted(load)
</script>

<template>
  <n-card title="类别管理">
    <template #header-extra>
      <n-button size="small" type="primary" @click="openCreate">新增类别</n-button>
    </template>
    <n-data-table :columns="columns" :data="list" :row-key="(r) => r.id" />

    <n-modal v-model:show="showModal" preset="card" :title="editing.id ? '编辑类别' : '新增类别'" style="width: 480px">
      <n-form :model="editing" label-placement="left" label-width="80">
        <n-form-item label="名称">
          <n-input v-model:value="editing.name" />
        </n-form-item>
        <n-form-item label="展示名">
          <n-input v-model:value="editing.display_name" />
        </n-form-item>
        <n-form-item label="颜色">
          <n-color-picker v-model:value="editing.color" />
        </n-form-item>
        <n-form-item label="排序">
          <n-input-number :value="editing.sort_order" :precision="0" @update:value="editing.sort_order = $event ?? 0" />
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
