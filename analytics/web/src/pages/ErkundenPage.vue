<template>
  <div class="erkunden">
    <aside class="panel">
      <div class="d-flex align-center mb-4">
        <span class="text-h6 font-weight-bold text-primary">{{ b.viewId ? 'Ansicht bearbeiten' : 'Daten erkunden' }}</span>
        <v-spacer />
        <v-btn size="small" variant="text" prepend-icon="mdi-restart" @click="reset">Neu</v-btn>
      </div>

      <div class="group">
        <div class="section-label">1 · Datenquelle</div>
        <v-btn-toggle v-model="f.source" mandatory class="vr-toggle vr-toggle--wrap" :divided="false" @update:model-value="changed">
          <v-btn v-for="s in sources" :key="s.key" :value="s.key" :prepend-icon="SRC_ICON[s.key]">{{ s.label }}</v-btn>
        </v-btn-toggle>
      </div>

      <div class="group">
        <div class="section-label">2 · Filter</div>
        <FilterPanel v-model="f.filters" :source="f.source" @vue:updated="noop" />
      </div>

      <div class="group">
        <div class="section-label">3 · Darstellung</div>
        <v-btn-toggle v-model="f.kind" mandatory class="vr-toggle mb-4" @update:model-value="changed">
          <v-btn value="chart" prepend-icon="mdi-chart-bar">Diagramm</v-btn>
          <v-btn value="map" prepend-icon="mdi-map">Karte</v-btn>
          <v-btn value="table" prepend-icon="mdi-table">Tabelle</v-btn>
        </v-btn-toggle>

      <template v-if="f.kind === 'chart'">
        <v-select v-model="f.chart_kind" :items="CHART_KINDS" item-title="label" item-value="value" label="Diagrammtyp" hide-details class="mb-3">
          <template #item="{ props: ip, item }"><v-list-item v-bind="ip" :prepend-icon="item.raw.icon" /></template>
        </v-select>
        <template v-if="!isRaw">
          <v-select v-model="f.metric_kind" :items="metrics" item-title="label" item-value="key" label="Was zählen?" hide-details class="mb-3" />
          <v-select v-if="metricNeedsColumn" v-model="f.metric_column" :items="numericColumns" item-title="label" item-value="name" label="Spalte" hide-details class="mb-3" />
          <v-select v-model="f.dimension" :items="dims" item-title="label" item-value="key" label="Aufteilen nach" hide-details class="mb-3" />
          <v-select v-model="f.color" :items="dims" item-title="label" item-value="key" label="Farbe nach (optional)" hide-details clearable class="mb-3" />
          <v-select v-model="f.facet" :items="dims" item-title="label" item-value="key" label="Kacheln nach (optional)" hide-details clearable class="mb-3" />
        </template>
        <template v-else>
          <v-select v-if="['timeline', 'calendar', 'histogram', 'scatter', 'boxplot'].includes(f.chart_kind)" v-model="f.x_column" :items="columns" item-title="label" item-value="name" :label="f.chart_kind === 'histogram' || f.chart_kind === 'scatter' ? 'Wert (x)' : 'Datum'" hide-details class="mb-3" />
          <v-select v-if="f.chart_kind === 'timeline'" v-model="f.series_column" :items="columns" item-title="label" item-value="name" label="Eine Zeile je" hide-details class="mb-3" />
          <v-select v-if="f.chart_kind === 'timeline'" v-model="f.color_column" :items="columns" item-title="label" item-value="name" label="Farbe nach (optional)" hide-details clearable class="mb-3" />
          <v-select v-if="['scatter', 'boxplot'].includes(f.chart_kind)" v-model="f.y_column" :items="numericColumns" item-title="label" item-value="name" label="Wert (y)" hide-details class="mb-3" />
          <template v-if="['sankey', 'graph'].includes(f.chart_kind)">
            <v-select v-model="f.source_column" :items="columns" item-title="label" item-value="name" label="Von" hide-details class="mb-3" />
            <v-select v-model="f.target_column" :items="columns" item-title="label" item-value="name" label="Nach" hide-details class="mb-3" />
          </template>
          <v-select v-if="f.chart_kind === 'calendar'" v-model="f.metric_kind" :items="metrics.filter((m) => ['sightings', 'birds'].includes(m.key))" item-title="label" item-value="key" label="Was zählen?" hide-details class="mb-3" />
        </template>
        <div class="d-flex ga-2">
          <v-select v-model="f.sort" :items="SORTS" item-title="label" item-value="value" label="Sortierung" hide-details class="mb-3" />
          <v-text-field v-model.number="f.limit" type="number" label="Nur die ersten …" hide-details clearable class="mb-3" style="max-width: 150px" />
        </div>
        <div class="d-flex flex-column">
          <v-checkbox v-model="f.show_values" label="Werte anzeigen" hide-details />
          <v-checkbox v-if="f.chart_kind === 'stacked_bar'" v-model="f.show_totals" label="Summen über den Balken" hide-details />
          <v-checkbox v-if="f.dimension === 'month' && !isRaw" v-model="f.annotate_moult" label="Mauserzeit markieren" hide-details />
        </div>
      </template>

      <template v-else-if="f.kind === 'map'">
        <v-select v-model="f.map.color_mode" :items="MAP_COLORS" item-title="label" item-value="value" label="Farbe nach" hide-details class="mb-3" />
        <v-select v-if="f.map.color_mode === 'category'" v-model="f.map.color_column" :items="columns" item-title="label" item-value="name" label="Spalte" hide-details class="mb-3" />
        <v-checkbox v-model="f.map.show_ringing_sites" label="Beringungsorte (Dreiecke) zeigen" hide-details />
        <v-checkbox v-model="f.map.tracks" label="Bewegungen je Vogel" hide-details />
        <v-checkbox v-model="f.map.bubbles_by_place" label="Ein Kreis je Ort (Größe = Vögel)" hide-details />
        <v-checkbox v-model="f.map.labels" label="Ortsnamen beschriften" hide-details />
        <v-select v-model="f.map.basemap" :items="BASEMAPS" item-title="label" item-value="value" label="Hintergrundkarte" hide-details class="mt-3" />
      </template>

      <template v-else>
        <v-select v-model="f.columns" :items="columns" item-title="label" item-value="name" label="Spalten (leer = Standard)" multiple chips closable-chips hide-details class="mb-3" />
        <v-select v-model="f.group_by" :items="dims" item-title="label" item-value="key" label="Zusammenfassen nach (optional)" multiple chips closable-chips hide-details class="mb-3" />
        <v-select v-if="f.group_by.length" v-model="f.metric_kind" :items="metrics" item-title="label" item-value="key" label="Was zählen?" hide-details class="mb-3" />
        <div class="d-flex ga-2">
          <v-select v-model="f.sort_by" :items="tableSortItems" item-title="label" item-value="name" label="Sortieren nach" hide-details clearable class="mb-3" />
          <v-checkbox v-model="f.sort_desc" label="absteigend" hide-details />
        </div>
        <v-checkbox v-model="f.totals_row" label="Summenzeile" hide-details />
      </template>
      </div>

      <div class="group">
        <div class="section-label">4 · Beschriftung</div>
        <v-text-field v-model="f.title" label="Titel (optional)" hide-details class="mb-3" />
        <v-text-field v-model="f.subtitle" label="Untertitel (optional, sonst Datengrundlage)" hide-details />
      </div>
    </aside>

    <section class="stage">
      <div class="d-flex align-center ga-2 mb-3 flex-wrap">
        <v-btn color="primary" prepend-icon="mdi-content-save" :loading="saving" @click="askSave">{{ b.viewId ? 'Speichern' : 'Als Ansicht speichern' }}</v-btn>
        <v-btn v-if="b.viewId" variant="tonal" prepend-icon="mdi-content-save-plus" @click="askSave(true)">Als Kopie speichern</v-btn>
        <v-menu>
          <template #activator="{ props: mp }"><v-btn v-bind="mp" variant="tonal" prepend-icon="mdi-download">Herunterladen</v-btn></template>
          <v-list density="compact">
            <v-list-item prepend-icon="mdi-image" title="Bild (PNG)" @click="download('png')" />
            <v-list-item prepend-icon="mdi-file-pdf-box" title="PDF" @click="download('pdf')" />
            <v-list-item prepend-icon="mdi-file-excel" title="Excel (Daten)" @click="download('xlsx')" />
            <v-list-item prepend-icon="mdi-open-in-new" title="Interaktive Seite" @click="download('open')" />
          </v-list>
        </v-menu>
        <v-btn variant="tonal" prepend-icon="mdi-view-dashboard-outline" :disabled="!b.viewId" title="Zuerst speichern" @click="addToWorkbook">Zur Mappe</v-btn>
        <v-btn variant="tonal" color="secondary" prepend-icon="mdi-robot-happy-outline" @click="askAgent">Agent fragen</v-btn>
        <v-spacer />
        <v-progress-circular v-if="b.loading" indeterminate size="22" width="3" color="secondary" />
      </div>

      <v-alert v-if="b.error" type="warning" variant="tonal" class="mb-3" :text="b.error" />
      <template v-if="b.preview">
        <VisualStage :kind="b.preview.kind" :model="b.preview.model" :height="stageHeight" footer-right="Vorschau" />
        <div class="muted mt-2" style="font-size: 13.5px"><strong>Datengrundlage:</strong> {{ b.preview.description }} <span v-if="b.preview.row_count !== undefined">· {{ fmtInt.format(b.preview.row_count) }} Zeilen</span></div>
        <div v-for="n in b.preview.notes" :key="n" class="muted" style="font-size: 13px">{{ n }}</div>
      </template>
      <EmptyState v-else-if="!b.loading" icon="mdi-compass-outline" text="Wähle links Datenquelle, Filter und Darstellung – die Vorschau erscheint hier." />
    </section>

    <v-dialog v-model="saveDialog" max-width="520">
      <v-card class="pa-6">
        <div class="card-title">Ansicht speichern</div>
        <v-text-field v-model="saveTitle" label="Titel" autofocus @keyup.enter="doSave" />
        <div class="muted mb-3" style="font-size: 13px">{{ b.preview?.describe }}</div>
        <div class="d-flex justify-end ga-2"><v-btn variant="text" @click="saveDialog = false">Abbrechen</v-btn><v-btn color="primary" :loading="saving" @click="doSave">Speichern</v-btn></div>
      </v-card>
    </v-dialog>

    <v-dialog v-model="wbDialog" max-width="520">
      <v-card class="pa-6">
        <div class="card-title">Zur Mappe hinzufügen</div>
        <v-select v-model="wbTarget" :items="workbooks" item-title="title" item-value="id" label="Mappe" />
        <v-text-field v-model="wbNew" label="… oder neue Mappe anlegen (Titel)" />
        <div class="d-flex justify-end ga-2"><v-btn variant="text" @click="wbDialog = false">Abbrechen</v-btn><v-btn color="primary" :loading="saving" @click="doAddToWorkbook">Hinzufügen</v-btn></div>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import EmptyState from '@/components/EmptyState.vue'
import { computed, onActivated, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, type CatalogItem } from '@/api/client'
import FilterPanel from '@/components/FilterPanel.vue'
import VisualStage from '@/components/VisualStage.vue'
import { CHART_KINDS, fmtInt, friendlyError } from '@/lib/format'
import { useBuilderStore } from '@/stores/builder'
import { useMetaStore } from '@/stores/meta'

defineOptions({ name: 'ErkundenPage' })

const b = useBuilderStore()
const meta = useMetaStore()
const route = useRoute()
const router = useRouter()
const f = computed(() => b.form)
const saving = ref(false)
const saveDialog = ref(false)
const saveTitle = ref('')
const saveAsCopy = ref(false)
const wbDialog = ref(false)
const wbTarget = ref<string | null>(null)
const wbNew = ref('')
const workbooks = ref<CatalogItem[]>([])
const noop = () => {}

const SRC_ICON: Record<string, string> = { sightings: 'mdi-binoculars', ringings: 'mdi-ring', birds: 'mdi-bird', relationships: 'mdi-family-tree' }
const SORTS = [
  { value: 'none', label: 'Natürlich' },
  { value: 'desc', label: 'Größte zuerst' },
  { value: 'asc', label: 'Kleinste zuerst' },
  { value: 'x', label: 'Alphabetisch / nach Achse' },
]
const MAP_COLORS = [
  { value: 'season', label: 'Jahreszeit (Ingos Farben)' },
  { value: 'species', label: 'Art' },
  { value: 'individual', label: 'Vogel (je Ring eine Farbe)' },
  { value: 'year', label: 'Jahr' },
  { value: 'category', label: 'Andere Spalte …' },
  { value: 'fixed', label: 'Einfarbig' },
]
const BASEMAPS = [
  { value: 'light', label: 'Hell' },
  { value: 'voyager', label: 'Voyager (mit Straßennamen)' },
  { value: 'dark', label: 'Dunkel' },
  { value: 'osm', label: 'OpenStreetMap' },
]

const sources = computed(() => meta.sources?.sources || [])
const src = computed(() => meta.sourceByKey(f.value.source))
const columns = computed(() => (src.value?.columns || []).filter((c) => c.role !== 'meta'))
const numericColumns = computed(() => columns.value.filter((c) => c.type === 'int' || c.type === 'number'))
const dims = computed(() => (meta.sources?.dimensions || []).filter((d) => src.value?.dimensions.includes(d.key)).map((d) => ({ key: d.key, label: d.label })))
const metrics = computed(() => (meta.sources?.metrics || []).filter((m) => src.value?.metrics.includes(m.key)))
const metricNeedsColumn = computed(() => metrics.value.find((m) => m.key === f.value.metric_kind)?.needs_column)
const isRaw = computed(() => !!CHART_KINDS.find((k) => k.value === f.value.chart_kind)?.raw)
const tableSortItems = computed(() => (f.value.group_by.length ? [{ name: 'value', label: 'Wert' }, ...dims.value.map((d) => ({ name: d.key, label: d.label }))] : columns.value))
const stageHeight = computed(() => Math.max(420, Math.min(760, window.innerHeight - 220)))

function changed() {
  if (f.value.source !== 'sightings' && f.value.dimension === 'month' && !dims.value.some((d) => d.key === 'month')) f.value.dimension = dims.value[0]?.key || 'species'
}

watch(() => b.form, () => { b.dirty = true; b.refresh() }, { deep: true })

async function loadFromRoute() {
  const id = route.params.viewId as string | undefined
  if (id && id !== b.viewId) {
    try {
      const item = await api.item('view', id)
      b.loadSpec(item.doc, id, item.title)
    } catch (e) {
      meta.notify(friendlyError(e), 'error')
    }
  } else if (!id && !b.preview) b.refresh(true)
  const g = route.query.group as string | undefined
  if (g && !id) {
    // „In Erkunden öffnen“ from a group: start from the group as the only filter
    b.reset()
    b.form.filters.groups = [g]
    b.refresh(true)
    router.replace('/erkunden')
  }
}
onMounted(loadFromRoute)
onActivated(loadFromRoute)
watch(() => route.params.viewId, loadFromRoute)

function reset() {
  b.reset()
  router.replace('/erkunden')
  b.refresh(true)
}
function askSave(copy = false) {
  saveAsCopy.value = copy
  saveTitle.value = f.value.title || b.viewTitle || b.preview?.describe || ''
  saveDialog.value = true
}
async function doSave() {
  saving.value = true
  try {
    if (saveAsCopy.value) b.viewId = null
    const res = await b.save(saveTitle.value)
    saveDialog.value = false
    meta.notify('Ansicht gespeichert.')
    if (route.params.viewId !== res.id) router.replace(`/erkunden/${res.id}`)
  } catch (e) {
    meta.notify(friendlyError(e), 'error')
  } finally {
    saving.value = false
  }
}
async function download(what: 'png' | 'pdf' | 'xlsx' | 'open') {
  saving.value = true
  try {
    let vid = b.viewId ? (await api.item('view', b.viewId)).extra?.visual_id : null
    if (!vid || b.dirty) {
      const res = b.viewId ? await api.updateView(b.viewId, b.spec, b.viewTitle || undefined) : await api.createView(b.spec, f.value.title || b.preview?.describe || 'Ansicht')
      b.viewId = res.id
      b.viewTitle = res.title
      b.dirty = false
      vid = res.visual?.visual_id
      if (route.params.viewId !== res.id) router.replace(`/erkunden/${res.id}`)
    }
    if (!vid) throw new Error('Kein Bild vorhanden.')
    window.open(what === 'open' ? `/viz/${vid}` : `/viz/${vid}.${what}`, '_blank')
  } catch (e) {
    meta.notify(friendlyError(e), 'error')
  } finally {
    saving.value = false
  }
}
async function addToWorkbook() {
  workbooks.value = (await api.list('workbook')).items
  wbDialog.value = true
}
async function doAddToWorkbook() {
  if (!b.viewId) return
  saving.value = true
  try {
    if (wbNew.value) {
      const item = await api.saveWorkbook({ title: wbNew.value, tiles: [{ view_id: b.viewId, w: 6 }] })
      router.push(`/mappen/${item.id}`)
    } else if (wbTarget.value) {
      const wb = await api.item('workbook', wbTarget.value)
      const spec = { ...wb.doc, tiles: [...(wb.doc.tiles || []), { view_id: b.viewId, w: 6 }] }
      await api.saveWorkbook(spec, wbTarget.value)
      router.push(`/mappen/${wbTarget.value}`)
    }
    wbDialog.value = false
  } catch (e) {
    meta.notify(friendlyError(e), 'error')
  } finally {
    saving.value = false
  }
}
function askAgent() {
  const d = b.preview?.describe || 'meine aktuelle Ansicht'
  const basis = b.preview?.description ? ` Datengrundlage: ${b.preview.description}.` : ''
  meta.openChat(`Erkläre mir diese Ansicht und was daran auffällig ist: ${d}.${basis}${b.viewId ? ` (Ansicht ${b.viewId})` : ''}`)
}
</script>

<style scoped>
.erkunden { display: grid; grid-template-columns: 400px 1fr; gap: 0; min-height: calc(100vh - 64px); }
.panel { background: #fff; border-right: 1px solid var(--vr-border); padding: 20px 20px 56px 20px; overflow: auto; max-height: calc(100vh - 64px); position: sticky; top: 64px; }
.stage { padding: 20px 28px 56px 28px; min-width: 0; }
.group { padding: 16px 0 20px 0; border-top: 1px solid var(--vr-border); }
.group:first-of-type { border-top: 0; padding-top: 0; }
.group :deep(.v-select), .group :deep(.v-text-field), .group :deep(.v-autocomplete), .group :deep(.v-combobox) { margin-bottom: 0; }
@media (max-width: 1100px) { .erkunden { grid-template-columns: 1fr; } .panel { position: static; max-height: none; } }
</style>
