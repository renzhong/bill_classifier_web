<script setup lang="ts">
/**
 * 按 StrategyType.param_schema (JSONSchema) 动态渲染参数表单。
 * MVP 只需支持 ai_classify 的字段类型（integer / boolean）+ 特殊的 strategy_id 下拉。
 * 后续若新增策略类型，按需扩展类型映射即可。
 */
import { computed } from 'vue'
import { NForm, NFormItem, NInputNumber, NSwitch, NSelect, NText } from 'naive-ui'
import type { AiStrategy } from '@/api/ai'

const props = defineProps<{
  schema: Record<string, any>
  modelValue: Record<string, any>
  aiStrategies?: AiStrategy[]
}>()
const emit = defineEmits<{ 'update:modelValue': [Record<string, any>] }>()

const properties = computed<Record<string, any>>(() => props.schema?.properties || {})
const required = computed<string[]>(() => props.schema?.required || [])

function update(key: string, val: any) {
  emit('update:modelValue', { ...props.modelValue, [key]: val })
}
</script>

<template>
  <n-form label-placement="left" label-width="150" :model="modelValue">
    <template v-for="(spec, key) in properties" :key="key">
      <n-form-item
        :label="(spec.title as string) || (key as string)"
        :required="required.includes(key as string)"
      >
        <!-- 业务约定：strategy_id 字段渲染为 AI 策略下拉 -->
        <n-select
          v-if="key === 'strategy_id'"
          :value="modelValue[key]"
          :options="(aiStrategies || []).map((s) => ({ label: `#${s.id} ${s.name}${s.active ? ' (active)' : ''}`, value: s.id }))"
          placeholder="选择 AI 策略"
          @update:value="(v) => update(key as string, v)"
        />
        <n-input-number
          v-else-if="spec.type === 'integer' || spec.type === 'number'"
          :value="modelValue[key] ?? spec.default ?? null"
          :min="spec.minimum"
          :max="spec.maximum"
          @update:value="(v) => update(key as string, v)"
        />
        <n-switch
          v-else-if="spec.type === 'boolean'"
          :value="modelValue[key] ?? spec.default ?? false"
          @update:value="(v) => update(key as string, v)"
        />
        <n-text v-else depth="3">不支持的类型: {{ spec.type }}</n-text>
      </n-form-item>
      <n-form-item v-if="spec.description" :show-label="false">
        <n-text depth="3" style="font-size: 12px">{{ spec.description }}</n-text>
      </n-form-item>
    </template>
  </n-form>
</template>
