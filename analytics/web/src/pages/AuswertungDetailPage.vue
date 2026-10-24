<template>
  <div class="page">
    <template v-if="p">
      <PageHeader :title="p.title" :icon="p.icon || 'mdi-play-box-multiple-outline'" :subtitle="p.description">
        <template #actions>
          <v-btn variant="tonal" prepend-icon="mdi-pin-outline" @click="pin">{{ p.pinned ? 'Angeheftet' : 'Anheften' }}</v-btn>
          <v-btn variant="tonal" prepend-icon="mdi-robot-happy-outline" @click="meta.openChat(`Erkläre mir die Auswertung „${p.title}“ (${p.id}) und was ich damit herausfinden kann.`)">Agent fragen</v-btn>
          <v-btn variant="text" to="/auswertungen" prepend-icon="mdi-arrow-left">Alle Auswertungen</v-btn>
        </template>
      </PageHeader>

      <v-row>
        <v-col cols="12" md="4">
          <v-card class="pa-5">
            <div class="card-title">Angaben</div>
            <ParamForm v-model="params" :parameters="p.parameters" />
            <v-btn color="primary" block class="mt-4" prepend-icon="mdi-play" :loading="running" @click="run">Auswertung starten</v-btn>
            <div class="muted mt-3 text-xs">{{ p.describe }}</div>
          </v-card>
          <v-card class="pa-5 mt-6">
            <div class="card-title">Frühere Ergebnisse</div>
            <v-list density="compact">
              <v-list-item v-for="r in runs" :key="r.id" :title="r.title" :subtitle="r.description" :prepend-icon="r.doc.status === 'ok' ? 'mdi-check-circle' : 'mdi-alert-circle'" @click="result = r.doc" />
            </v-list>
            <div v-if="!runs.length" class="muted">Noch nicht ausgeführt.</div>
          </v-card>
        </v-col>
        <v-col cols="12" md="8">
          <v-card v-if="progress" class="pa-4 mb-4 run-panel">
            <div class="d-flex align-center">
              <v-progress-circular v-if="progress.status === 'running'" indeterminate size="22" width="3" class="mr-3" />
              <v-icon v-else :color="progress.status === 'ok' ? 'success' : 'error'" class="mr-3">{{ progress.status === 'ok' ? 'mdi-check-circle' : 'mdi-alert-circle' }}</v-icon>
              <span class="font-weight-bold text-primary">{{ progress.status === 'running' ? 'Läuft …' : progress.status === 'ok' ? 'Fertig' : 'Abgebrochen' }}</span>
              <v-spacer />
              <span class="muted">Schritt {{ progress.index }} / {{ progress.total || '?' }}</span>
            </div>
            <v-progress-linear v-if="progress.total" :model-value="(progress.index / progress.total) * 100" class="my-2" />
            <div v-for="s in progress.steps" :key="s.index" class="text-small"><v-icon size="16" :color="s.status === 'ok' ? 'success' : 'error'">{{ s.status === 'ok' ? 'mdi-check' : 'mdi-close' }}</v-icon> {{ s.title }}</div>
          </v-card>
          <v-alert v-if="error" type="warning" variant="tonal" class="mb-3">{{ error }}</v-alert>
          <v-card v-if="result" class="pa-5">
            <div class="card-title">Ergebnis</div>
            <RunResultView :run="result" />
          </v-card>
          <EmptyState v-else-if="!running" icon="mdi-play-circle-outline" text="Mach links deine Angaben und starte die Auswertung – das Ergebnis erscheint hier." />
        </v-col>
      </v-row>
    </template>
  </div>
</template>

<script setup lang="ts">
import EmptyState from '@/components/EmptyState.vue'
import PageHeader from '@/components/PageHeader.vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api, type CatalogItem, type PipelineSummary, type RunResult } from '@/api/client'
import ParamForm from '@/components/ParamForm.vue'
import RunResultView from '@/components/RunResultView.vue'
import { friendlyError } from '@/lib/format'
import { useLiveStore } from '@/stores/live'
import { useMetaStore } from '@/stores/meta'

const route = useRoute()
const meta = useMetaStore()
const live = useLiveStore()
const p = ref<PipelineSummary | null>(null)
const params = ref<Record<string, any>>({})
const running = ref(false)
const result = ref<RunResult | null>(null)
const runs = ref<CatalogItem<RunResult>[]>([])
const error = ref('')
const runId = ref('')
const progress = computed(() => (runId.value ? live.progress[runId.value] : Object.values(live.progress).find((x) => x.pipeline === p.value?.title && x.status === 'running')) || null)

async function load() {
  const id = route.params.id as string
  const all = (await api.pipelines()).items
  p.value = all.find((x) => x.id === id) || null
  runs.value = (await api.runs(id)).items
}
async function run() {
  if (!p.value) return
  running.value = true
  error.value = ''
  result.value = null
  try {
    const clean: Record<string, any> = {}
    for (const [k, v] of Object.entries(params.value)) if (v !== null && v !== '' && !(Array.isArray(v) && !v.length)) clean[k] = v
    const r = await api.runPipeline(p.value.id, clean)
    runId.value = r.run_id
    result.value = r
    if (r.status === 'error') error.value = r.error || 'Die Auswertung ist fehlgeschlagen.'
    runs.value = (await api.runs(p.value.id)).items
  } catch (e) {
    error.value = friendlyError(e)
  } finally {
    running.value = false
  }
}
async function pin() {
  if (!p.value) return
  await api.pin('pipeline', p.value.id, !p.value.pinned)
  await load()
}
onMounted(load)
watch(() => route.params.id, load)
</script>
