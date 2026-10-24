<template>
  <div>
    <div v-for="e in items" :key="e.seq" class="activity-item">
      <span class="time">{{ fmtTime(e.at) }}</span>
      <v-icon size="18" :color="iconColor(e.type)" :class="{ muted: !iconColor(e.type) }">{{ icon(e.type) }}</v-icon>
      <div style="flex: 1; min-width: 0">
        <div>{{ e.title }}</div>
        <div class="d-flex ga-2 flex-wrap mt-1">
          <router-link v-if="link(e)" :to="link(e)!">Öffnen</router-link>
          <a v-if="e.interactive_url || e.urls?.interactive_url" :href="e.interactive_url || e.urls?.interactive_url" target="_blank">Interaktiv</a>
          <a v-if="e.pdf" :href="e.pdf" target="_blank">PDF</a>
          <a v-if="e.docx" :href="e.docx">Word</a>
          <a v-if="e.pptx_url" :href="e.pptx_url">PowerPoint</a>
        </div>
      </div>
    </div>
    <div v-if="!items.length" class="muted pa-3 text-small">Noch keine Aktivität.</div>
  </div>
</template>

<script setup lang="ts">
import { fmtTime } from '@/lib/format'

defineProps<{ items: any[] }>()

const ICONS: Record<string, string> = { visual: 'mdi-chart-box', view: 'mdi-eye', workbook: 'mdi-view-dashboard', pipeline: 'mdi-play-box-multiple', report: 'mdi-file-document', deck: 'mdi-presentation', note: 'mdi-note-text', group: 'mdi-folder-multiple-outline', definition: 'mdi-book-open-variant', navigate: 'mdi-cursor-default-click', log: 'mdi-information' }
const icon = (t: string) => ICONS[t.split('.')[0]] || 'mdi-circle-small'
const iconColor = (t: string) => (t.endsWith('.deleted') ? 'error' : t.includes('finished') ? 'success' : undefined)
function link(e: any): string | null {
  const t = e.type.split('.')[0]
  if (t === 'view' && (e.view_id || e.id)) return `/erkunden/${e.view_id || e.id}`
  if (t === 'group') return e.type.endsWith('.deleted') ? '/gruppen' : `/gruppen/${e.group_id || e.id}`
  if (t === 'visual' && e.visual_id) return `/live?visual=${e.visual_id}`
  if (t === 'workbook' && (e.workbook_id || e.id)) return `/mappen/${e.workbook_id || e.id}`
  if (t === 'pipeline' && e.pipeline_id) return `/auswertungen/${e.pipeline_id}`
  if (t === 'pipeline' && e.run_id) return `/live?run=${e.run_id}`
  if (t === 'report' || t === 'deck') return '/berichte'
  if (t === 'note') return '/notizen'
  if (t === 'definition') return '/begriffe'
  return null
}
</script>
