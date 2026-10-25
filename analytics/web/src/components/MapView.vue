<template>
  <div class="map-wrap">
    <div ref="el" class="map-box" />
    <div v-if="basemapSwitch" class="basemap-select">
      <select v-model="basemap" @change="pickBasemap">
        <option value="light">Hell</option>
        <option value="voyager">Voyager</option>
        <option value="dark">Dunkel</option>
        <option value="osm">OpenStreetMap</option>
      </select>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { renderMap, type MapHandle, type MapModel } from '@/lib/mapRender'
import { isDark } from '@/lib/theme'

const props = withDefaults(defineProps<{ model: MapModel; basemapSwitch?: boolean }>(), { basemapSwitch: true })
const emit = defineEmits<{ (e: 'basemap', name: string): void }>()
function pickBasemap() {
  handle?.setBasemap(basemap.value)
  emit('basemap', basemap.value) // the builder stores it, so exports use the same basemap
}
const el = ref<HTMLElement | null>(null)
const defaultBasemap = () => (isDark.value && (props.model.basemap_name || 'light') === 'light' ? 'dark' : props.model.basemap_name || 'light')
const basemap = ref(defaultBasemap())
let handle: MapHandle | null = null

function render() {
  handle?.destroy()
  handle = null
  if (!el.value) return
  el.value.innerHTML = ''
  handle = renderMap(el.value, props.model, { interactive: true })
  basemap.value = defaultBasemap()
  if (basemap.value !== props.model.basemap_name) handle.setBasemap(basemap.value)
}

onMounted(() => nextTick(render))
watch(() => props.model, () => nextTick(render))
watch(isDark, () => {
  basemap.value = defaultBasemap()
  handle?.setBasemap(basemap.value)
})
onBeforeUnmount(() => handle?.destroy())
defineExpose({ getBounds: () => handle?.getBounds() || null })
</script>

<style scoped>
.map-wrap { position: relative; width: 100%; height: 100%; min-height: 360px; }
.map-box { position: absolute; inset: 0; }
.basemap-select { position: absolute; left: 10px; top: 80px; z-index: 800; }
</style>
