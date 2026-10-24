<template>
  <div>
    <v-skeleton-loader v-if="loading" type="image" height="360" />
    <v-alert v-else-if="error" type="warning" variant="tonal">{{ error }}</v-alert>
    <VisualStage v-else-if="info" :kind="info.kind" :model="info.model" :height="height" :footer-right="'vogelring.com · ' + fmtDate(info.updated_at)" />
    <div v-if="info && showLinks" class="d-flex flex-wrap ga-2 mt-2">
      <v-btn size="small" variant="text" :href="info.interactive_url" target="_blank" prepend-icon="mdi-open-in-new">Interaktiv</v-btn>
      <v-btn size="small" variant="text" :href="info.png_url" prepend-icon="mdi-image">Bild</v-btn>
      <v-btn size="small" variant="text" :href="info.pdf_url" prepend-icon="mdi-file-pdf-box">PDF</v-btn>
      <v-btn size="small" variant="text" :href="info.xlsx_url" prepend-icon="mdi-file-excel">Excel</v-btn>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { api, type VisualInfo } from '@/api/client'
import { fmtDate, friendlyError } from '@/lib/format'
import VisualStage from './VisualStage.vue'

const props = withDefaults(defineProps<{ visualId: string; height?: number; showLinks?: boolean }>(), { height: 0, showLinks: true })
const info = ref<VisualInfo | null>(null)
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    info.value = await api.visual(props.visualId)
  } catch (e) {
    error.value = friendlyError(e)
  } finally {
    loading.value = false
  }
}
watch(() => props.visualId, load, { immediate: true })
defineExpose({ reload: load })
</script>
