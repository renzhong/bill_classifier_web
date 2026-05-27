<script setup lang="ts">
import { computed, h, onMounted, ref } from 'vue'
import {
  NCard, NSpace, NButton, NList, NListItem, NThing, NSwitch, NPopconfirm,
  NModal, NInput, NText, NTag, useMessage,
} from 'naive-ui'
import { pipelineApi, type PipelineStep, type StrategyTypeMeta } from '@/api/pipeline'
import { aiApi, type AiStrategy } from '@/api/ai'
import StrategyParamForm from '@/components/StrategyParamForm.vue'

const message = useMessage()
const strategyTypes = ref<StrategyTypeMeta[]>([])
const steps = ref<PipelineStep[]>([])
const aiStrategies = ref<AiStrategy[]>([])
const loading = ref(false)

const editorOpen = ref(false)
const editorMode = ref<'create' | 'edit'>('create')
const editorTypeKey = ref('')
const editorTypeMeta = computed(() => strategyTypes.value.find((t) => t.type_key === editorTypeKey.value))
const editorStep = ref<Partial<PipelineStep>>({})

async function loadAll() {
  loading.value = true
  try {
    const [types, list, strats] = await Promise.all([
      pipelineApi.strategyTypes(),
      pipelineApi.listSteps(),
      aiApi.listStrategies(),
    ])
    strategyTypes.value = types
    steps.value = list.sort((a, b) => a.sort_order - b.sort_order || a.id - b.id)
    aiStrategies.value = strats
  } catch (e) {
    message.error((e as Error).message)
  } finally {
    loading.value = false
  }
}

function openCreate(t: StrategyTypeMeta) {
  editorMode.value = 'create'
  editorTypeKey.value = t.type_key
  editorStep.value = {
    strategy_type: t.type_key,
    display_name: t.display_name,
    params: {},
    sort_order: steps.value.length,
    enabled: true,
  }
  editorOpen.value = true
}

function openEdit(s: PipelineStep) {
  editorMode.value = 'edit'
  editorTypeKey.value = s.strategy_type
  editorStep.value = { ...s, params: { ...s.params } }
  editorOpen.value = true
}

async function saveEditor() {
  try {
    if (editorMode.value === 'create') {
      await pipelineApi.createStep({
        strategy_type: editorStep.value.strategy_type!,
        display_name: editorStep.value.display_name!,
        params: editorStep.value.params || {},
        sort_order: editorStep.value.sort_order ?? steps.value.length,
        enabled: editorStep.value.enabled ?? true,
      })
    } else if (editorStep.value.id) {
      await pipelineApi.patchStep(editorStep.value.id, {
        display_name: editorStep.value.display_name,
        params: editorStep.value.params,
        sort_order: editorStep.value.sort_order,
        enabled: editorStep.value.enabled,
      })
    }
    editorOpen.value = false
    await loadAll()
    message.success('已保存')
  } catch (e) {
    message.error((e as Error).message)
  }
}

async function removeStep(s: PipelineStep) {
  try {
    await pipelineApi.deleteStep(s.id)
    await loadAll()
    message.success('已删除')
  } catch (e) {
    message.error((e as Error).message)
  }
}

async function toggle(s: PipelineStep) {
  try {
    await pipelineApi.patchStep(s.id, { enabled: !s.enabled })
    await loadAll()
  } catch (e) {
    message.error((e as Error).message)
  }
}

async function move(s: PipelineStep, delta: number) {
  const idx = steps.value.findIndex((x) => x.id === s.id)
  if (idx < 0) return
  const j = idx + delta
  if (j < 0 || j >= steps.value.length) return
  const a = steps.value[idx]; const b = steps.value[j]
  try {
    await pipelineApi.reorder([
      { id: a.id, sort_order: b.sort_order },
      { id: b.id, sort_order: a.sort_order },
    ])
    await loadAll()
  } catch (e) {
    message.error((e as Error).message)
  }
}

onMounted(loadAll)
</script>

<template>
  <n-space :wrap="false" align="start" style="width: 100%">
    <n-card title="可用策略类型" style="width: 360px; flex-shrink: 0">
      <n-text depth="3" style="font-size: 12px">点击 “添加到 Pipeline”，按 sort_order 顺序执行。</n-text>
      <n-list bordered style="margin-top: 12px">
        <n-list-item v-for="t in strategyTypes" :key="t.type_key">
          <n-thing>
            <template #header>{{ t.display_name }}</template>
            <template #header-extra>
              <n-button size="tiny" type="primary" @click="openCreate(t)">添加</n-button>
            </template>
            <n-text depth="3" style="font-size: 12px">{{ t.description }}</n-text>
          </n-thing>
        </n-list-item>
      </n-list>
    </n-card>

    <n-card title="我的 Pipeline" style="flex: 1; min-width: 600px">
      <template #header-extra>
        <n-button size="small" @click="loadAll" :loading="loading">刷新</n-button>
      </template>
      <n-list v-if="steps.length" bordered>
        <n-list-item v-for="(s, idx) in steps" :key="s.id">
          <n-thing>
            <template #header>
              <n-space align="center">
                <n-tag>{{ idx + 1 }}</n-tag>
                <strong>{{ s.display_name }}</strong>
                <n-tag size="small" :type="s.enabled ? 'success' : 'default'">
                  {{ s.strategy_type }}
                </n-tag>
              </n-space>
            </template>
            <template #header-extra>
              <n-space>
                <n-switch :value="s.enabled" size="small" @update:value="() => toggle(s)" />
                <n-button size="tiny" @click="move(s, -1)">↑</n-button>
                <n-button size="tiny" @click="move(s, 1)">↓</n-button>
                <n-button size="tiny" @click="openEdit(s)">编辑</n-button>
                <n-popconfirm @positive-click="() => removeStep(s)">
                  <template #trigger><n-button size="tiny" type="error">删除</n-button></template>
                  确认删除？
                </n-popconfirm>
              </n-space>
            </template>
            <n-text depth="3" style="font-size: 12px">
              {{ JSON.stringify(s.params) }}
            </n-text>
          </n-thing>
        </n-list-item>
      </n-list>
      <n-text v-else depth="3">尚未添加任何策略。先在左侧点 “添加”。</n-text>
    </n-card>
  </n-space>

  <n-modal v-model:show="editorOpen" preset="card" style="width: 560px"
    :title="editorMode === 'create' ? `添加策略：${editorTypeMeta?.display_name}` : `编辑：${editorStep.display_name}`">
    <n-space vertical>
      <n-text depth="3" style="font-size: 12px">{{ editorTypeMeta?.description }}</n-text>
      <div>
        <div style="margin-bottom: 4px">名称</div>
        <n-input v-model:value="editorStep.display_name" placeholder="给这条步骤起个名字" />
      </div>
      <div v-if="editorTypeMeta">
        <div style="margin-bottom: 4px">参数</div>
        <strategy-param-form
          :schema="editorTypeMeta.param_schema"
          v-model="editorStep.params as Record<string, any>"
          :ai-strategies="aiStrategies"
        />
      </div>
    </n-space>
    <template #footer>
      <n-space justify="end">
        <n-button @click="editorOpen = false">取消</n-button>
        <n-button type="primary" @click="saveEditor">保存</n-button>
      </n-space>
    </template>
  </n-modal>
</template>
