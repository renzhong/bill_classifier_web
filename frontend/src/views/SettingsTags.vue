<script setup lang="ts">
import { h, onMounted, ref } from 'vue'
import {
  NCard, NDataTable, NSpace, NButton, NInput, NPopconfirm, NModal,
  NForm, NFormItem, NColorPicker, useMessage, type DataTableColumns,
} from 'naive-ui'
import { tagApi, type Tag } from '@/api/meta'
import { useMetaStore } from '@/stores/meta'

const message = useMessage()
const meta = useMetaStore()
const list = ref<Tag[]>([])
const showModal = ref(false)
const editing = ref<Partial<Tag>>({})

async function load() { list.value = await tagApi.list() }

function openCreate() {
  editing.value = { name: '', color: '#52c41a' }
  showModal.value = true
}

async function save() {
  try {
    await tagApi.create({ name: editing.value.name!, color: editing.value.color ?? null })
    showModal.value = false
    await load()
    await meta.reloadTags()
    message.success('已新增')
  } catch (e) {
    message.error((e as Error).message)
  }
}

async function remove(row: Tag) {
  try {
    await tagApi.remove(row.id)
    await load()
    await meta.reloadTags()
    message.success('已删除')
  } catch (e) {
    message.error((e as Error).message)
  }
}

const columns: DataTableColumns<Tag> = [
  { title: 'ID', key: 'id', width: 70 },
  { title: '名称', key: 'name' },
  {
    title: '颜色',
    key: 'color',
    width: 120,
    render: (r) => h('span', { style: `display:inline-block;width:18px;height:18px;border-radius:3px;background:${r.color || '#ccc'}` }),
  },
  {
    title: '操作',
    key: 'actions',
    width: 140,
    render: (row) =>
      h(NPopconfirm, { onPositiveClick: () => remove(row) }, {
        trigger: () => h(NButton, { size: 'tiny', type: 'error' }, () => '删除'),
        default: () => `确认删除 tag ${row.name}？`,
      }),
  },
]

onMounted(load)
</script>

<template>
  <n-card title="Tag 管理">
    <template #header-extra>
      <n-button size="small" type="primary" @click="openCreate">新增 Tag</n-button>
    </template>
    <n-data-table :columns="columns" :data="list" :row-key="(r) => r.id" />

    <n-modal v-model:show="showModal" preset="card" title="新增 Tag" style="width: 420px">
      <n-form :model="editing" label-placement="left" label-width="60">
        <n-form-item label="名称"><n-input v-model:value="editing.name" /></n-form-item>
        <n-form-item label="颜色"><n-color-picker v-model:value="editing.color" /></n-form-item>
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
