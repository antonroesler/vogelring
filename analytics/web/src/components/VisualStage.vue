<template>
  <div class="vr-stage" :style="{ height: height ? height + 'px' : undefined }">
    <div v-if="model.title || model.subtitle" class="head">
      <h2 v-if="model.title">{{ model.title }}</h2>
      <p v-if="model.subtitle">{{ model.subtitle }}</p>
    </div>
    <div class="body" :style="{ height: bodyHeight }">
      <ChartView v-if="kind === 'chart'" :model="model" />
      <MapView v-else-if="kind === 'map'" ref="mapRef" :model="model" />
      <TableView v-else-if="kind === 'table'" :model="model" />
    </div>
    <div v-if="model.footnote || footerRight" class="foot">
      <span style="white-space: pre-wrap">{{ model.footnote || '' }}</span>
      <span>{{ footerRight }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import ChartView from './ChartView.vue'
import MapView from './MapView.vue'
import TableView from './TableView.vue'

const mapRef = ref<InstanceType<typeof MapView> | null>(null)
defineExpose({ mapBounds: () => mapRef.value?.getBounds() || null })

const props = withDefaults(defineProps<{ kind: 'chart' | 'map' | 'table'; model: any; height?: number; footerRight?: string }>(), { height: 0, footerRight: '' })
const bodyHeight = computed(() => {
  if (props.kind === 'table') return 'auto'
  const h = props.height || Math.min(720, Math.max(380, props.model?.height || 600))
  const head = props.model?.title || props.model?.subtitle ? 58 : 0
  const foot = props.model?.footnote || props.footerRight ? 32 : 0
  return `${h - head - foot}px`
})
</script>

<style scoped>
.body { position: relative; }
</style>
