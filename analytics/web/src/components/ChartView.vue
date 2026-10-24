<template>
  <div ref="el" class="chart-box" />
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { buildChartOption, type ChartModel } from '@/lib/chartOption'
import { isDark } from '@/lib/theme'

const props = defineProps<{ model: ChartModel }>()
const el = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null
let ro: ResizeObserver | null = null

function render() {
  if (!el.value) return
  if (!chart) chart = echarts.init(el.value, undefined, { renderer: 'canvas' })
  try {
    chart.clear()
    chart.setOption(buildChartOption(props.model, true), true)
  } catch (e) {
    console.error('chart option failed', e)
  }
}

onMounted(() => {
  render()
  ro = new ResizeObserver(() => chart?.resize())
  if (el.value) ro.observe(el.value)
})
watch(() => props.model, render, { deep: false })
watch(isDark, render)
onBeforeUnmount(() => {
  ro?.disconnect()
  chart?.dispose()
  chart = null
})
</script>
