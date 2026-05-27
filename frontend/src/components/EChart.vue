<script setup lang="ts">
/**
 * ECharts 极简封装：按需注册图表类型，避免完整包打入 bundle。
 * 父组件直接传 option，自动负责 init / resize / dispose。
 */
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart, PieChart, LineChart } from 'echarts/charts'
import {
  GridComponent, TooltipComponent, TitleComponent, LegendComponent, DatasetComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  BarChart, PieChart, LineChart,
  GridComponent, TooltipComponent, TitleComponent, LegendComponent, DatasetComponent,
  CanvasRenderer,
])

const props = defineProps<{ option: object; height?: string }>()

const root = ref<HTMLDivElement>()
let inst: echarts.ECharts | null = null

function refresh() {
  if (!inst && root.value) {
    inst = echarts.init(root.value)
  }
  inst?.setOption(props.option, { notMerge: true })
}

function onResize() { inst?.resize() }

onMounted(() => {
  refresh()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  inst?.dispose()
  inst = null
})

watch(() => props.option, refresh, { deep: true })
</script>

<template>
  <div ref="root" :style="{ width: '100%', height: props.height || '320px' }" />
</template>
