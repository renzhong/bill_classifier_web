<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import {
  NCard, NSpace, NList, NListItem, NThing, NButton, NInput, NSelect, NSwitch,
  NPopconfirm, NModal, NForm, NFormItem, NText, useMessage,
} from 'naive-ui'
import { aiApi, type AiCredential, type AiStrategy } from '@/api/ai'

const message = useMessage()
const list = ref<AiStrategy[]>([])
const credentials = ref<AiCredential[]>([])
const selectedId = ref<number | null>(null)
const editing = ref<AiStrategy | null>(null)
const previewText = ref('')
const showCreate = ref(false)
const createForm = ref({ name: '', strategy_text: '', credential_id: null as number | null })

async function load() {
  const [s, c] = await Promise.all([aiApi.listStrategies(), aiApi.listCredentials()])
  list.value = s
  credentials.value = c
  if (!selectedId.value && s.length) selectedId.value = s[0].id
}

const selected = computed(() => list.value.find((x) => x.id === selectedId.value) || null)

watch(selected, (s) => {
  editing.value = s ? { ...s } : null
  if (s) refreshPreview(s.strategy_text)
})

async function refreshPreview(text: string) {
  try {
    const res = await aiApi.preview(text)
    previewText.value = res.prompt
  } catch {
    previewText.value = ''
  }
}

async function save() {
  if (!editing.value) return
  try {
    const e = editing.value
    await aiApi.patchStrategy(e.id, {
      name: e.name,
      strategy_text: e.strategy_text,
      active: e.active,
      credential_id: e.credential_id,
    })
    await load()
    message.success('已保存')
    refreshPreview(e.strategy_text)
  } catch (err) {
    message.error((err as Error).message)
  }
}

async function remove(s: AiStrategy) {
  try {
    await aiApi.deleteStrategy(s.id)
    if (selectedId.value === s.id) selectedId.value = null
    await load()
    message.success('已删除')
  } catch (e) {
    message.error((e as Error).message)
  }
}

async function createOne() {
  try {
    const created = await aiApi.createStrategy({
      name: createForm.value.name,
      strategy_text: createForm.value.strategy_text,
      credential_id: createForm.value.credential_id,
      active: false,
    })
    showCreate.value = false
    createForm.value = { name: '', strategy_text: '', credential_id: null }
    await load()
    selectedId.value = created.id
    message.success('已新增')
  } catch (e) {
    message.error((e as Error).message)
  }
}

onMounted(load)
</script>

<template>
  <n-space :wrap="false" align="start" style="width: 100%">
    <n-card title="策略列表" style="width: 280px; flex-shrink: 0">
      <template #header-extra>
        <n-button size="tiny" type="primary" @click="showCreate = true">新增</n-button>
      </template>
      <n-list bordered>
        <n-list-item v-for="s in list" :key="s.id"
          :style="{ cursor: 'pointer', background: selectedId === s.id ? '#eef5ff' : '' }"
          @click="selectedId = s.id">
          <n-thing>
            <template #header>{{ s.name }} <n-text v-if="s.active" type="success">·active</n-text></template>
            <template #header-extra>
              <n-popconfirm @positive-click="remove(s)">
                <template #trigger><n-button size="tiny" type="error" text>删除</n-button></template>
                确认删除 {{ s.name }}？
              </n-popconfirm>
            </template>
            <n-text depth="3" style="font-size: 12px">cred: #{{ s.credential_id ?? '-' }}</n-text>
          </n-thing>
        </n-list-item>
      </n-list>
    </n-card>

    <n-card title="编辑策略" style="flex: 1; min-width: 480px" v-if="editing">
      <n-form label-placement="left" label-width="80">
        <n-form-item label="名称">
          <n-input v-model:value="editing.name" />
        </n-form-item>
        <n-form-item label="绑定凭据">
          <n-select
            v-model:value="editing.credential_id"
            clearable
            :options="credentials.map((c) => ({ label: `#${c.id} ${c.provider}/${c.model_name}`, value: c.id }))"
          />
        </n-form-item>
        <n-form-item label="active">
          <n-switch v-model:value="editing.active" />
        </n-form-item>
        <n-form-item label="规则文本">
          <n-input
            v-model:value="editing.strategy_text"
            type="textarea"
            :rows="14"
            placeholder="每行一条规则，例如：&#10;看到 “高德/滴滴/出租车” 归到 交通&#10;看到 “盒马/超市” 归到 日用&#10;以 # 开头的行视为注释"
            @update:value="(v) => refreshPreview(v)"
          />
        </n-form-item>
        <n-space justify="end">
          <n-button type="primary" @click="save">保存</n-button>
        </n-space>
      </n-form>
    </n-card>
    <n-text v-else depth="3" style="padding: 24px">左侧选择一条策略以编辑</n-text>

    <n-card title="prompt 预览" style="flex: 1; min-width: 480px">
      <pre style="white-space: pre-wrap; background: #f5f7fa; padding: 12px; max-height: 600px; overflow: auto; font-size: 12px">{{ previewText }}</pre>
    </n-card>
  </n-space>

  <n-modal v-model:show="showCreate" preset="card" title="新增策略" style="width: 520px">
    <n-form label-placement="left" label-width="80">
      <n-form-item label="名称">
        <n-input v-model:value="createForm.name" />
      </n-form-item>
      <n-form-item label="绑定凭据">
        <n-select
          v-model:value="createForm.credential_id"
          clearable
          :options="credentials.map((c) => ({ label: `#${c.id} ${c.provider}/${c.model_name}`, value: c.id }))"
        />
      </n-form-item>
      <n-form-item label="规则文本">
        <n-input v-model:value="createForm.strategy_text" type="textarea" :rows="8" />
      </n-form-item>
    </n-form>
    <template #footer>
      <n-space justify="end">
        <n-button @click="showCreate = false">取消</n-button>
        <n-button type="primary" @click="createOne">保存</n-button>
      </n-space>
    </template>
  </n-modal>
</template>
