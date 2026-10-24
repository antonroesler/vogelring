<template>
  <div class="page page--wide">
    <v-row>
      <v-col cols="12">
        <PageHeader title="Live" icon="mdi-broadcast" subtitle="Hier erscheint sofort, was der Assistent (oder du) gerade erstellt – ohne Neuladen. Ideal als zweiter Bildschirm neben dem Chat.">
          <template #title-append><v-chip size="small" :color="live.connected ? 'success' : 'grey'" variant="tonal">{{ live.connected ? 'verbunden' : 'getrennt' }}</v-chip></template>
          <template #actions><v-btn v-if="latest" variant="text" prepend-icon="mdi-pin-off" @click="follow = !follow">{{ follow ? 'Automatisch folgen: an' : 'Automatisch folgen: aus' }}</v-btn></template>
        </PageHeader>

        <v-card v-if="activeRun" class="pa-4 mb-4 run-panel">
          <div class="d-flex align-center">
            <v-progress-circular v-if="activeRun.status === 'running'" indeterminate size="22" width="3" class="mr-3" />
            <v-icon v-else :color="activeRun.status === 'ok' ? 'success' : 'error'" class="mr-3">{{ activeRun.status === 'ok' ? 'mdi-check-circle' : 'mdi-alert-circle' }}</v-icon>
            <div class="font-weight-medium">Auswertung „{{ activeRun.pipeline }}“ {{ activeRun.status === 'running' ? 'läuft' : activeRun.status === 'ok' ? 'fertig' : 'abgebrochen' }}</div>
            <v-spacer />
            <span class="muted text-small tabular">Schritt {{ activeRun.index }} / {{ activeRun.total || '?' }}</span>
          </div>
          <v-progress-linear v-if="activeRun.total" :model-value="(activeRun.index / activeRun.total) * 100" class="my-2" />
          <div v-for="s in activeRun.steps" :key="s.index" class="d-flex ga-2 text-small">
            <v-icon size="16" :color="s.status === 'ok' ? 'success' : 'error'">{{ s.status === 'ok' ? 'mdi-check' : 'mdi-close' }}</v-icon>{{ s.title }}
          </div>
          <div v-if="activeRun.error" class="text-error mt-1">{{ activeRun.error }}</div>
        </v-card>

        <template v-if="latest">
          <div class="d-flex align-center mb-2">
            <span class="icon-tile mr-3" aria-hidden="true"><v-icon>{{ KIND_ICON[latest.kind] || 'mdi-star' }}</v-icon></span>
            <div class="card-title mb-0">{{ latest.title }}</div>
            <v-spacer />
            <span class="muted text-xs">{{ fmtTime(latest.at) }}</span>
          </div>
          <VisualById v-if="latest.kind === 'visual'" :key="latest.id" :visual-id="latest.id" :height="640" />
          <v-card v-else-if="latest.kind === 'report'" class="pa-5">
            <div class="card-title">Bericht fertig</div>
            <div class="d-flex ga-2 flex-wrap">
              <v-btn :href="latest.urls?.html" target="_blank" color="primary" prepend-icon="mdi-web">Ansehen</v-btn>
              <v-btn :href="latest.urls?.pdf" variant="tonal" prepend-icon="mdi-file-pdf-box">PDF</v-btn>
              <v-btn :href="latest.urls?.docx" variant="tonal" prepend-icon="mdi-file-word">Word</v-btn>
            </div>
            <iframe v-if="latest.urls?.html" :src="latest.urls.html" class="mt-4" style="width: 100%; height: 70vh; border: 1px solid rgb(var(--border-light)); border-radius: 12px; background: #fff" />
          </v-card>
          <v-card v-else-if="latest.kind === 'deck'" class="pa-5">
            <div class="card-title">Präsentation fertig</div>
            <v-btn :href="latest.urls?.pptx" color="primary" prepend-icon="mdi-presentation">PowerPoint herunterladen</v-btn>
          </v-card>
          <v-card v-else-if="latest.kind === 'workbook'" class="pa-5">
            <div class="card-title">Mappe {{ latest.title }}</div>
            <v-btn :to="`/mappen/${latest.id}`" color="primary" prepend-icon="mdi-view-dashboard">Mappe öffnen</v-btn>
          </v-card>
          <v-card v-else-if="latest.kind === 'run'" class="pa-5">
            <RunResultView v-if="runDoc" :run="runDoc" />
            <div v-else class="muted">Ergebnisse erscheinen, sobald die Auswertung fertig ist.</div>
          </v-card>
        </template>
        <v-card v-else class="pa-8 text-center">
          <v-icon size="40" class="muted">mdi-broadcast</v-icon>
          <div class="mt-2 text-small" style="color: rgb(var(--text-secondary))">Noch nichts zu sehen. Stell dem Assistenten im Chat eine Frage – Diagramme, Karten und Berichte erscheinen hier.</div>
          <v-btn class="mt-4" color="primary" @click="meta.openChat()">Agent fragen</v-btn>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import PageHeader from '@/components/PageHeader.vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api, type RunResult } from '@/api/client'
import RunResultView from '@/components/RunResultView.vue'
import VisualById from '@/components/VisualById.vue'
import { fmtTime, KIND_ICON } from '@/lib/format'
import { useLiveStore, type Artefact } from '@/stores/live'
import { useMetaStore } from '@/stores/meta'

const live = useLiveStore()
const meta = useMetaStore()
const route = useRoute()
const follow = ref(true)
const pinnedArtefact = ref<Artefact | null>(null)
const runDoc = ref<RunResult | null>(null)

const latest = computed(() => (follow.value ? live.latest || pinnedArtefact.value : pinnedArtefact.value || live.latest))
const activeRun = computed(() => {
  const runs = Object.values(live.progress)
  return runs.length ? runs[runs.length - 1] : null
})

async function applyQuery() {
  const v = route.query.visual as string | undefined
  const r = route.query.run as string | undefined
  if (v) {
    pinnedArtefact.value = { kind: 'visual', id: v, title: 'Grafik', at: new Date().toISOString(), event: { seq: 0, type: 'navigate', title: '', at: '' } }
    follow.value = false
  } else if (r) {
    const runs = await api.runs()
    const found = runs.items.find((i) => i.id === r)
    if (found) {
      runDoc.value = found.doc
      pinnedArtefact.value = { kind: 'run', id: r, title: found.title, at: found.updated_at, event: { seq: 0, type: 'navigate', title: '', at: '' } }
      follow.value = false
    }
  }
}

watch(
  () => live.latest,
  async (a) => {
    if (a?.kind === 'run' && a.event.type === 'pipeline.finished') {
      // the run document is stored right after the finished event; poll briefly until it is there
      runDoc.value = null
      for (let attempt = 0; attempt < 6 && !runDoc.value; attempt++) {
        if (attempt) await new Promise((r) => setTimeout(r, 800))
        const runs = await api.runs()
        runDoc.value = runs.items.find((i) => i.id === a.id)?.doc || null
      }
    }
  },
)
watch(() => route.query, applyQuery)
onMounted(applyQuery)
</script>
