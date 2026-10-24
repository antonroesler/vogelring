<template>
  <v-dialog v-model="open" max-width="1040" scrollable>
    <v-card class="pa-6">
      <div class="card-title">Gruppen vergleichen</div>
      <div class="d-flex flex-wrap ga-3 align-end mb-4">
        <v-autocomplete v-model="ids" :items="options" item-title="name" item-value="id" label="Gruppen" multiple chips closable-chips hide-details style="min-width: 320px; flex: 2">
          <template #chip="{ props: cp, item }"><v-chip v-bind="cp"><span class="dot" :style="{ background: item.raw.color || '#8aa' }" />{{ item.raw.name }}</v-chip></template>
        </v-autocomplete>
        <v-select v-model="metric" :items="METRICS" item-title="label" item-value="value" label="Was zählen?" hide-details style="flex: 1; min-width: 170px" />
        <v-select v-model="dimension" :items="DIMENSIONS" item-title="label" item-value="value" label="Aufteilen nach" hide-details style="flex: 1; min-width: 190px" />
        <v-select v-model="chartKind" :items="kinds" item-title="label" item-value="value" label="Diagramm" hide-details style="flex: 1; min-width: 160px" />
      </div>
      <v-alert v-if="error" type="warning" variant="tonal" class="mb-3" :text="error" />
      <div class="stage-wrap">
        <VisualStage v-if="preview" :kind="preview.kind" :model="preview.model" :height="440" footer-right="Vorschau" />
        <div v-else-if="loading" class="d-flex justify-center pa-10"><v-progress-circular indeterminate color="secondary" /></div>
        <EmptyState v-else icon="mdi-compare-horizontal" text="Wähle mindestens eine Gruppe – die Vorschau erscheint hier." />
      </div>
      <div v-if="preview?.description" class="muted mt-2" style="font-size: 13px"><strong>Datengrundlage:</strong> {{ preview.description }}</div>
      <div class="d-flex justify-end ga-2 mt-4 flex-wrap">
        <v-btn variant="text" @click="open = false">Schließen</v-btn>
        <v-btn variant="tonal" color="secondary" prepend-icon="mdi-robot-happy-outline" :disabled="!ids.length" @click="askAgent">Agent fragen</v-btn>
        <v-btn color="primary" prepend-icon="mdi-content-save" :disabled="!preview" :loading="saving" @click="save">Als Ansicht speichern</v-btn>
      </div>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api, type GroupSummary } from '@/api/client'
import EmptyState from '@/components/EmptyState.vue'
import VisualStage from '@/components/VisualStage.vue'
import { friendlyError } from '@/lib/format'
import { useMetaStore } from '@/stores/meta'

const props = defineProps<{ modelValue: boolean; groups: GroupSummary[]; preselect?: string[] }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: boolean): void }>()
const router = useRouter()
const meta = useMetaStore()

const METRICS = [
  { value: 'sightings', label: 'Sichtungen' },
  { value: 'birds', label: 'Vögel (verschiedene Ringe)' },
  { value: 'observation_days', label: 'Beobachtungstage' },
  { value: 'places', label: 'Orte' },
]
const DIMENSIONS = [
  { value: 'group', label: 'Nur je Gruppe (Summen)' },
  { value: 'year', label: 'Jahr' },
  { value: 'month', label: 'Monat' },
  { value: 'season', label: 'Jahreszeit' },
  { value: 'status', label: 'Status' },
  { value: 'age', label: 'Alter' },
  { value: 'place', label: 'Ort' },
  { value: 'ringing_place', label: 'Beringungsort' },
  { value: 'distance_class', label: 'Entfernung zum Beringungsort' },
  { value: 'year_month', label: 'Jahr-Monat' },
]
const ALL_KINDS = [
  { value: 'bar', label: 'Balken' },
  { value: 'stacked_bar', label: 'Gestapelte Balken' },
  { value: 'line', label: 'Linie' },
  { value: 'area', label: 'Fläche' },
  { value: 'pie', label: 'Kreis', onlyGroup: true },
  { value: 'heatmap', label: 'Heatmap', notGroup: true },
]

const open = computed({ get: () => props.modelValue, set: (v) => emit('update:modelValue', v) })
const options = computed(() => props.groups)
const ids = ref<string[]>([])
const metric = ref('sightings')
const dimension = ref('year')
const chartKind = ref('bar')
const kinds = computed(() => ALL_KINDS.filter((k) => (dimension.value === 'group' ? !k.notGroup : !k.onlyGroup)))
const preview = ref<any>(null)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
let timer: any = null
let seq = 0

watch(open, (v) => {
  if (v) {
    ids.value = props.preselect?.length ? [...props.preselect] : props.groups.slice(0, 2).map((g) => g.id)
    preview.value = null
    error.value = ''
    schedule()
  }
})
watch([ids, metric, dimension, chartKind], () => {
  if (!kinds.value.some((k) => k.value === chartKind.value)) chartKind.value = 'bar'
  schedule()
})

function schedule() {
  clearTimeout(timer)
  timer = setTimeout(run, 300)
}
async function run() {
  if (!open.value) return
  if (!ids.value.length) {
    preview.value = null
    return
  }
  const my = ++seq
  loading.value = true
  error.value = ''
  try {
    const p = await api.compareGroups(ids.value, metric.value, dimension.value, chartKind.value, false)
    if (my === seq) preview.value = p
  } catch (e) {
    if (my === seq) {
      preview.value = null
      error.value = friendlyError(e)
    }
  } finally {
    if (my === seq) loading.value = false
  }
}
async function save() {
  saving.value = true
  try {
    const res = await api.compareGroups(ids.value, metric.value, dimension.value, chartKind.value, true)
    meta.notify('Vergleich als Ansicht gespeichert.')
    open.value = false
    router.push(`/erkunden/${res.id}`)
  } catch (e) {
    meta.notify(friendlyError(e), 'error')
  } finally {
    saving.value = false
  }
}
function askAgent() {
  const names = ids.value.map((id) => props.groups.find((g) => g.id === id)?.name || id)
  meta.openChat(`Vergleiche die Gruppen ${names.map((n) => `„${n}“`).join(' und ')} miteinander (${METRICS.find((m) => m.value === metric.value)?.label} je ${DIMENSIONS.find((d) => d.value === dimension.value)?.label}) und erkläre mir die Unterschiede in einfacher Sprache.`)
}
</script>

<style scoped>
.stage-wrap { min-height: 300px; }
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; flex: none; }
</style>
