<script setup lang="ts">
import { h, onMounted, onUnmounted, ref } from 'vue'
import { NCard, NDataTable, NTag, NButton, useMessage, type DataTableColumns } from 'naive-ui'
import { uploadTaskApi, type UploadTask } from '@/api/bills'

const message = useMessage()
const tasks = ref<UploadTask[]>([])
const loading = ref(false)
let timer: number | null = null

async function load() {
  loading.value = true
  try {
    tasks.value = await uploadTaskApi.list()
  } catch (e) {
    message.error((e as Error).message)
  } finally {
    loading.value = false
  }
}

const statusTagType: Record<string, 'default' | 'info' | 'success' | 'warning' | 'error'> = {
  pending: 'default',
  parsing: 'info',
  classifying: 'info',
  done: 'success',
  failed: 'error',
}

const columns: DataTableColumns<UploadTask> = [
  { title: 'ID', key: 'id', width: 80 },
  { title: '来源', key: 'source', width: 90 },
  { title: '文件', key: 'filename' },
  {
    title: '状态',
    key: 'status',
    width: 120,
    render: (row) => h(NTag, { type: statusTagType[row.status] || 'default', size: 'small' }, { default: () => row.status }),
  },
  { title: '总行数', key: 'total_rows', width: 90 },
  { title: '已分类', key: 'classified_rows', width: 90 },
  { title: '错误/备注', key: 'error_msg', ellipsis: { tooltip: true } },
  { title: '创建于', key: 'created_at', width: 180 },
]

onMounted(() => {
  load()
  timer = window.setInterval(load, 4000)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <n-card title="上传任务">
    <template #header-extra>
      <n-button size="small" @click="load" :loading="loading">刷新</n-button>
    </template>
    <n-data-table :columns="columns" :data="tasks" :bordered="false" :row-key="(r) => r.id" />
  </n-card>
</template>
