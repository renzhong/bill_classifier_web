<script setup lang="ts">
import { h, onMounted, ref } from 'vue'
import {
  NButton, NCard, NDataTable, NDatePicker, NForm, NFormItem, NInputNumber,
  NModal, NPopconfirm, NSpace, NTag, useMessage, type DataTableColumns,
} from 'naive-ui'
import { authApi, type Invitation } from '@/api/auth'

const message = useMessage()
const invitations = ref<Invitation[]>([])
const loading = ref(false)
const showCreate = ref(false)
const maxUses = ref(1)
const expiresAt = ref<number | null>(null)

async function load() {
  loading.value = true
  try {
    invitations.value = await authApi.listInvitations()
  } catch (e) {
    message.error((e as Error).message)
  } finally {
    loading.value = false
  }
}

async function create() {
  try {
    await authApi.createInvitation({
      max_uses: maxUses.value,
      expires_at: expiresAt.value == null ? null : new Date(expiresAt.value).toISOString(),
    })
    showCreate.value = false
    maxUses.value = 1
    expiresAt.value = null
    await load()
    message.success('邀请码已创建')
  } catch (e) {
    message.error((e as Error).message)
  }
}

async function revoke(row: Invitation) {
  try {
    await authApi.revokeInvitation(row.id)
    await load()
    message.success('邀请码已撤销')
  } catch (e) {
    message.error((e as Error).message)
  }
}

function status(row: Invitation) {
  if (row.revoked_at) return '已撤销'
  if (row.used_count >= row.max_uses) return '已用尽'
  if (row.expires_at && new Date(row.expires_at).getTime() < Date.now()) return '已过期'
  return '可使用'
}

const columns: DataTableColumns<Invitation> = [
  { title: '邀请码', key: 'code' },
  { title: '使用次数', key: 'used_count', render: (row) => `${row.used_count} / ${row.max_uses}` },
  { title: '过期时间', key: 'expires_at', render: (row) => row.expires_at || '无' },
  {
    title: '状态', key: 'status', render: (row) =>
      h(NTag, { type: status(row) === '可使用' ? 'success' : 'default', size: 'small' },
        { default: () => status(row) }),
  },
  {
    title: '操作', key: 'actions', render: (row) =>
      status(row) === '可使用'
        ? h(NPopconfirm, { onPositiveClick: () => revoke(row) }, {
            trigger: () => h(NButton, { size: 'small', type: 'error', text: true }, () => '撤销'),
            default: () => '撤销后将不能用于注册，确认？',
          })
        : null,
  },
]

onMounted(load)
</script>

<template>
  <n-card title="邀请码管理">
    <template #header-extra>
      <n-space>
        <n-button size="small" :loading="loading" @click="load">刷新</n-button>
        <n-button size="small" type="primary" @click="showCreate = true">创建邀请码</n-button>
      </n-space>
    </template>
    <n-data-table :columns="columns" :data="invitations" :loading="loading" :row-key="(row) => row.id" />

    <n-modal v-model:show="showCreate" preset="card" title="创建邀请码" style="width: 420px">
      <n-form label-placement="left" label-width="90">
        <n-form-item label="最多使用">
          <n-input-number :value="maxUses" :min="1" :max="1000"
            @update:value="(value: number | null) => { maxUses = value ?? 1 }" />
        </n-form-item>
        <n-form-item label="过期时间">
          <n-date-picker v-model:value="expiresAt" type="datetime" clearable />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreate = false">取消</n-button>
          <n-button type="primary" @click="create">创建</n-button>
        </n-space>
      </template>
    </n-modal>
  </n-card>
</template>
