<script setup lang="ts">
import { h, onMounted, ref } from 'vue'
import {
  NCard, NDataTable, NSpace, NButton, NInput, NSelect, NSwitch, NPopconfirm,
  NModal, NForm, NFormItem, useMessage, type DataTableColumns,
} from 'naive-ui'
import { aiApi, type AiCredential, type ProviderMeta } from '@/api/ai'

const message = useMessage()
const providers = ref<ProviderMeta[]>([])
const list = ref<AiCredential[]>([])
const showModal = ref(false)
const editing = ref<Partial<AiCredential & { api_key?: string }>>({})
const showTestModal = ref(false)
const testTarget = ref<AiCredential | null>(null)
const testInput = ref({ payee: '高德打车', item_name: '打车费', amount: '18.00', bill_type: 'expense', source: 'alipay' })
const testResult = ref<{ category: string | null; confidence: string | null; raw: string } | null>(null)
const testing = ref(false)

async function load() {
  const [p, c] = await Promise.all([aiApi.providers(), aiApi.listCredentials()])
  providers.value = p
  list.value = c
}

function openCreate() {
  editing.value = { provider: providers.value[0]?.provider_key || 'openai', model_name: '', api_key: '', base_url: '', enabled: true }
  showModal.value = true
}

function openEdit(row: AiCredential) {
  editing.value = { ...row, api_key: '' }   // api_key 留空表示不改
  showModal.value = true
}

async function save() {
  try {
    if (editing.value.id) {
      const body: Record<string, unknown> = {
        model_name: editing.value.model_name,
        base_url: editing.value.base_url,
        enabled: editing.value.enabled,
      }
      if (editing.value.api_key) body.api_key = editing.value.api_key
      await aiApi.patchCredential(editing.value.id, body)
    } else {
      if (!editing.value.api_key) throw new Error('api_key 必填')
      await aiApi.createCredential({
        provider: editing.value.provider!,
        model_name: editing.value.model_name!,
        api_key: editing.value.api_key!,
        base_url: editing.value.base_url || null,
        enabled: editing.value.enabled ?? true,
      })
    }
    showModal.value = false
    await load()
    message.success('已保存')
  } catch (e) {
    message.error((e as Error).message)
  }
}

async function remove(row: AiCredential) {
  try {
    const res = await aiApi.deleteCredential(row.id)
    await load()
    message.success(`已删除（同时解绑 ${res.unbound_strategies ?? 0} 条策略）`)
  } catch (e) {
    message.error((e as Error).message)
  }
}

function openTest(row: AiCredential) {
  testTarget.value = row
  testResult.value = null
  showTestModal.value = true
}

async function runTest() {
  if (!testTarget.value) return
  testing.value = true
  try {
    testResult.value = await aiApi.test({
      credential_id: testTarget.value.id,
      strategy_id: null,
      sample: { ...testInput.value },
    })
  } catch (e) {
    message.error((e as Error).message)
  } finally {
    testing.value = false
  }
}

const columns: DataTableColumns<AiCredential> = [
  { title: 'ID', key: 'id', width: 60 },
  { title: 'Provider', key: 'provider', width: 120 },
  { title: 'Model', key: 'model_name' },
  { title: 'base_url', key: 'base_url', ellipsis: { tooltip: true } },
  {
    title: '启用',
    key: 'enabled',
    width: 70,
    render: (r) => h(NSwitch, { value: r.enabled, onUpdateValue: async (v: boolean) => {
      await aiApi.patchCredential(r.id, { enabled: v })
      await load()
    }}),
  },
  {
    title: '操作',
    key: 'actions',
    width: 240,
    render: (row) => h(NSpace, {}, () => [
      h(NButton, { size: 'tiny', onClick: () => openTest(row) }, () => '测试'),
      h(NButton, { size: 'tiny', onClick: () => openEdit(row) }, () => '编辑'),
      h(NPopconfirm, { onPositiveClick: () => remove(row) }, {
        trigger: () => h(NButton, { size: 'tiny', type: 'error' }, () => '删除'),
        default: () => `确认删除 ${row.provider}/${row.model_name}？`,
      }),
    ]),
  },
]

onMounted(load)
</script>

<template>
  <n-card title="AI 凭据">
    <template #header-extra>
      <n-button size="small" type="primary" @click="openCreate">新增凭据</n-button>
    </template>
    <n-data-table :columns="columns" :data="list" :row-key="(r) => r.id" />

    <n-modal v-model:show="showModal" preset="card" :title="editing.id ? '编辑凭据' : '新增凭据'" style="width: 520px">
      <n-form label-placement="left" label-width="100">
        <n-form-item label="Provider">
          <n-select
            v-model:value="editing.provider"
            :disabled="!!editing.id"
            :options="providers.map((p) => ({ label: p.display_name, value: p.provider_key }))"
          />
        </n-form-item>
        <n-form-item label="Model">
          <n-select
            v-model:value="editing.model_name"
            filterable
            tag
            :options="(providers.find((p) => p.provider_key === editing.provider)?.suggested_models || []).map((m) => ({ label: m, value: m }))"
            placeholder="选择或输入 model_name"
          />
        </n-form-item>
        <n-form-item label="API Key">
          <n-input v-model:value="editing.api_key" type="password" show-password-on="click"
            :placeholder="editing.id ? '留空表示不修改' : '必填'" />
        </n-form-item>
        <n-form-item label="base_url">
          <n-input v-model:value="editing.base_url" :placeholder="providers.find((p) => p.provider_key === editing.provider)?.default_base_url || ''" />
        </n-form-item>
        <n-form-item label="启用">
          <n-switch v-model:value="editing.enabled" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" @click="save">保存</n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal v-model:show="showTestModal" preset="card" title="测试 AI 调用（不依赖策略）" style="width: 560px">
      <n-form label-placement="left" label-width="100">
        <n-form-item label="payee"><n-input v-model:value="testInput.payee" /></n-form-item>
        <n-form-item label="item_name"><n-input v-model:value="testInput.item_name" /></n-form-item>
        <n-form-item label="amount"><n-input v-model:value="testInput.amount" /></n-form-item>
        <n-form-item label="bill_type">
          <n-select v-model:value="testInput.bill_type" :options="[
            { label: 'expense', value: 'expense' },
            { label: 'income', value: 'income' },
            { label: 'other', value: 'other' },
          ]" />
        </n-form-item>
      </n-form>
      <div v-if="testResult" style="margin-top: 12px">
        <div><strong>识别类别：</strong>{{ testResult.category || '（无）' }}</div>
        <div><strong>raw：</strong></div>
        <pre style="background: #f5f7fa; padding: 8px; max-height: 240px; overflow: auto">{{ testResult.raw }}</pre>
      </div>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showTestModal = false">关闭</n-button>
          <n-button type="primary" :loading="testing" @click="runTest">调用</n-button>
        </n-space>
      </template>
    </n-modal>
  </n-card>
</template>
