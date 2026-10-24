<template>
  <div>
    <v-alert v-if="run.status === 'error'" type="error" variant="tonal" class="mb-3">{{ run.error || 'Die Auswertung ist fehlgeschlagen.' }}</v-alert>
    <div v-for="a in run.artifacts" :key="a.step_id" class="mb-5">
      <div class="d-flex align-center mb-1">
        <v-icon class="mr-2 muted">{{ KIND_ICON[a.kind] || 'mdi-file' }}</v-icon>
        <span class="font-weight-bold text-primary">{{ a.title || KIND_LABEL[a.kind] || a.kind }}</span>
      </div>
      <VisualById v-if="a.visual_id" :visual-id="a.visual_id" :height="520" />
      <div v-else-if="a.report_id" class="d-flex ga-2 flex-wrap">
        <v-btn :href="a.urls?.html" target="_blank" color="primary" prepend-icon="mdi-web">Bericht ansehen</v-btn>
        <v-btn :href="a.urls?.pdf" variant="tonal" prepend-icon="mdi-file-pdf-box">PDF</v-btn>
        <v-btn :href="a.urls?.docx" variant="tonal" prepend-icon="mdi-file-word">Word</v-btn>
      </div>
      <v-btn v-else-if="a.deck_id" :href="a.urls?.pptx_url || a.url" color="primary" prepend-icon="mdi-presentation">PowerPoint herunterladen</v-btn>
      <v-btn v-else-if="a.kind === 'export'" :href="a.url || a.urls?.download" variant="tonal" prepend-icon="mdi-file-excel">{{ a.title || 'Excel' }} herunterladen</v-btn>
      <router-link v-else-if="a.dataset_id" :to="`/daten/${a.dataset_id}`">Daten ansehen</router-link>
      <div v-if="a.description" class="muted mt-1 text-xs">Datengrundlage: {{ a.description }}</div>
    </div>
    <v-expansion-panels variant="accordion" class="mt-2">
      <v-expansion-panel title="Protokoll der Auswertung" elevation="0">
        <v-expansion-panel-text>
          <div v-for="(l, i) in run.log" :key="i" class="text-small">{{ l }}</div>
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>
  </div>
</template>

<script setup lang="ts">
import type { RunResult } from '@/api/client'
import VisualById from './VisualById.vue'
import { KIND_ICON, KIND_LABEL } from '@/lib/format'

defineProps<{ run: RunResult }>()
</script>
