<template>
  <div class="page page--wide">
    <PageHeader v-if="wb" :title="wb.title" icon="mdi-view-dashboard-outline" :subtitle="wb.description || 'Mappe'">
      <template #actions>
      <v-btn variant="tonal" prepend-icon="mdi-plus" @click="openAdd">Ansicht hinzufügen</v-btn>
      <v-btn variant="tonal" prepend-icon="mdi-filter-variant" @click="filterDialog = true">Gemeinsame Filter</v-btn>
      <v-btn variant="tonal" prepend-icon="mdi-refresh" :loading="rendering" @click="render(true)">Neu berechnen</v-btn>
      <v-btn color="primary" prepend-icon="mdi-file-document" :loading="busy === 'report'" @click="makeReport">Bericht (PDF/Word)</v-btn>
      <v-btn variant="tonal" prepend-icon="mdi-presentation" :loading="busy === 'deck'" @click="makeDeck">Präsentation</v-btn>
      <v-btn variant="text" icon="mdi-robot-happy-outline" title="Agent fragen" @click="meta.openChat(`Schau dir die Mappe „${wb.title}“ (${wb.id}) an und fasse die wichtigsten Erkenntnisse in einfachen Worten zusammen.`)" />
      <v-menu>
        <template #activator="{ props: mp }"><v-btn v-bind="mp" variant="text" icon="mdi-dots-vertical" /></template>
        <v-list density="compact">
          <v-list-item prepend-icon="mdi-pencil" title="Umbenennen" @click="rename" />
          <v-list-item prepend-icon="mdi-pin-outline" :title="wb.pinned ? 'Loslösen' : 'Anheften'" @click="pin" />
          <v-list-item prepend-icon="mdi-delete-outline" title="Löschen" @click="remove" />
        </v-list>
      </v-menu>
      </template>
    </PageHeader>

    <v-alert v-if="result?.report" type="success" variant="tonal" class="mb-3">
      Bericht fertig: <a :href="result.report.html" target="_blank">Ansehen</a> · <a :href="result.report.pdf">PDF</a> · <a :href="result.report.docx">Word</a>
    </v-alert>
    <v-alert v-if="result?.deck" type="success" variant="tonal" class="mb-3">Präsentation fertig: <a :href="result.deck.pptx_url">PowerPoint herunterladen</a></v-alert>
    <v-alert v-if="error" type="warning" variant="tonal" class="mb-3">{{ error }}</v-alert>

    <div v-if="wb && activeFilters.length" class="d-flex flex-wrap ga-1 mb-3">
      <span class="muted mr-1 text-xs">Gemeinsame Filter:</span>
      <v-chip v-for="c in activeFilters" :key="c" size="small">{{ c }}</v-chip>
    </div>

    <div v-if="wb" class="grid">
      <v-card v-for="(t, i) in tiles" :key="i" class="tile" :style="{ gridColumn: `span ${t.tile.w || 6}` }">
        <div class="d-flex align-center px-4 pt-3 pb-1">
          <span class="font-weight-medium text-truncate">{{ t.title || t.tile.title || 'Kachel' }}</span>
          <v-spacer />
          <v-btn size="x-small" variant="text" icon="mdi-arrow-left" :disabled="i === 0" @click="move(i, -1)" />
          <v-btn size="x-small" variant="text" icon="mdi-arrow-right" :disabled="i === tiles.length - 1" @click="move(i, 1)" />
          <v-btn size="x-small" variant="text" :icon="(t.tile.w || 6) >= 12 ? 'mdi-arrow-collapse-horizontal' : 'mdi-arrow-expand-horizontal'" @click="toggleWidth(i)" />
          <v-btn v-if="t.tile.view_id" size="x-small" variant="text" icon="mdi-pencil" :to="`/erkunden/${t.tile.view_id}`" />
          <v-btn size="x-small" variant="text" icon="mdi-note-edit-outline" @click="editNote(i)" />
          <v-btn size="x-small" variant="text" icon="mdi-close" @click="removeTile(i)" />
        </div>
        <div v-if="t.error" class="pa-4 text-error">{{ t.error }}</div>
        <VisualStage v-else-if="t.model" :kind="t.kind" :model="t.model" :height="(t.tile.h || 1) * 380" />
        <div v-else class="pa-6 muted text-center">{{ rendering ? 'Wird berechnet …' : 'Noch nicht berechnet' }}</div>
        <div v-if="t.description" class="muted px-4 pb-2 text-xs">Datengrundlage: {{ t.description }}</div>
        <div v-if="t.tile.note" class="md px-4 pb-3" v-html="md(t.tile.note)" />
      </v-card>
    </div>
    <v-card v-if="wb && !tiles.length" class="pa-8 text-center text-small" style="color: rgb(var(--text-secondary))">Diese Mappe ist leer. Füge gespeicherte Ansichten hinzu oder bitte den Assistenten darum.</v-card>

    <v-dialog v-model="addDialog" max-width="560">
      <v-card class="pa-4">
        <div class="card-title">Ansicht hinzufügen</div>
        <v-autocomplete v-model="addId" :items="views" item-title="title" item-value="id" label="Gespeicherte Ansicht" />
        <div class="d-flex justify-end ga-2"><v-btn variant="text" @click="addDialog = false">Abbrechen</v-btn><v-btn color="primary" :disabled="!addId" @click="addTile">Hinzufügen</v-btn></div>
      </v-card>
    </v-dialog>

    <v-dialog v-model="filterDialog" max-width="560">
      <v-card class="pa-4">
        <div class="card-title">Gemeinsame Filter</div>
        <p class="muted text-small">Gelten zusätzlich zu den Filtern jeder Ansicht (z. B. ein Jahr für die ganze Mappe).</p>
        <FilterPanel v-model="sharedFilters" source="sightings" />
        <div class="d-flex justify-end ga-2 mt-3"><v-btn variant="text" @click="filterDialog = false">Abbrechen</v-btn><v-btn color="primary" @click="saveFilters">Übernehmen</v-btn></div>
      </v-card>
    </v-dialog>

    <v-dialog v-model="noteDialog" max-width="560">
      <v-card class="pa-4">
        <div class="card-title">Text zur Kachel</div>
        <v-textarea v-model="noteText" label="Einordnung für den Leser (erscheint im Bericht)" rows="5" />
        <div class="d-flex justify-end ga-2"><v-btn variant="text" @click="noteDialog = false">Abbrechen</v-btn><v-btn color="primary" @click="saveNote">Speichern</v-btn></div>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import PageHeader from '@/components/PageHeader.vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { marked } from 'marked'
import { api, type CatalogItem, type ViewSummary } from '@/api/client'
import FilterPanel from '@/components/FilterPanel.vue'
import VisualStage from '@/components/VisualStage.vue'
import { friendlyError } from '@/lib/format'
import { cleanFilters, emptyFilters, toFilterForm, type Filters } from '@/stores/builder'
import { useLiveStore } from '@/stores/live'
import { useMetaStore } from '@/stores/meta'

const route = useRoute()
const router = useRouter()
const meta = useMetaStore()
const live = useLiveStore()
const wb = ref<CatalogItem | null>(null)
const tiles = ref<any[]>([])
const rendering = ref(false)
const busy = ref('')
const error = ref('')
const result = ref<{ report?: any; deck?: any } | null>(null)
const addDialog = ref(false)
const addId = ref<string | null>(null)
const views = ref<ViewSummary[]>([])
const filterDialog = ref(false)
const sharedFilters = ref<Filters>(emptyFilters())
const noteDialog = ref(false)
const noteIndex = ref(0)
const noteText = ref('')
const md = (s: string) => marked.parse(s || '') as string

const activeFilters = computed(() => {
  const f = wb.value?.doc.filters || {}
  return Object.entries(f)
    .filter(([, v]) => (Array.isArray(v) ? v.length : v))
    .map(([k, v]) => `${meta.sources?.filters.find((x) => x.name === k)?.label || k}: ${Array.isArray(v) ? v.join(', ') : v}`)
})

async function load() {
  const id = route.params.id as string
  wb.value = await api.item('workbook', id)
  tiles.value = (wb.value.doc.tiles || []).map((t: any) => ({ tile: t }))
  sharedFilters.value = toFilterForm(wb.value.doc.filters)
  await render(false)
}
async function render(force: boolean) {
  if (!wb.value) return
  rendering.value = true
  error.value = ''
  try {
    const r = await api.renderWorkbook(wb.value.id, force)
    tiles.value = r.tiles
  } catch (e) {
    error.value = friendlyError(e)
  } finally {
    rendering.value = false
  }
}
async function saveSpec(spec: any) {
  if (!wb.value) return
  wb.value = await api.saveWorkbook(spec, wb.value.id)
  await load()
}
async function openAdd() {
  views.value = (await api.views()).items
  addDialog.value = true
}
async function addTile() {
  if (!wb.value || !addId.value) return
  addDialog.value = false
  await saveSpec({ ...wb.value.doc, tiles: [...(wb.value.doc.tiles || []), { view_id: addId.value, w: 6 }] })
}
async function removeTile(i: number) {
  if (!wb.value) return
  const t = [...wb.value.doc.tiles]
  t.splice(i, 1)
  await saveSpec({ ...wb.value.doc, tiles: t })
}
async function move(i: number, d: number) {
  if (!wb.value) return
  const t = [...wb.value.doc.tiles]
  const [x] = t.splice(i, 1)
  t.splice(i + d, 0, x)
  await saveSpec({ ...wb.value.doc, tiles: t })
}
async function toggleWidth(i: number) {
  if (!wb.value) return
  const t = wb.value.doc.tiles.map((x: any, j: number) => (j === i ? { ...x, w: (x.w || 6) >= 12 ? 6 : 12 } : x))
  await saveSpec({ ...wb.value.doc, tiles: t })
}
function editNote(i: number) {
  noteIndex.value = i
  noteText.value = wb.value?.doc.tiles[i]?.note || ''
  noteDialog.value = true
}
async function saveNote() {
  if (!wb.value) return
  const t = wb.value.doc.tiles.map((x: any, j: number) => (j === noteIndex.value ? { ...x, note: noteText.value || undefined } : x))
  noteDialog.value = false
  await saveSpec({ ...wb.value.doc, tiles: t })
}
async function saveFilters() {
  if (!wb.value) return
  const f = cleanFilters(sharedFilters.value)
  filterDialog.value = false
  await saveSpec({ ...wb.value.doc, filters: f })
}
async function makeReport() {
  if (!wb.value) return
  busy.value = 'report'
  try {
    result.value = { ...(result.value || {}), report: await api.workbookReport(wb.value.id) }
  } catch (e) {
    error.value = friendlyError(e)
  } finally {
    busy.value = ''
  }
}
async function makeDeck() {
  if (!wb.value) return
  busy.value = 'deck'
  try {
    result.value = { ...(result.value || {}), deck: await api.workbookDeck(wb.value.id) }
  } catch (e) {
    error.value = friendlyError(e)
  } finally {
    busy.value = ''
  }
}
async function rename() {
  if (!wb.value) return
  const t = prompt('Neuer Titel', wb.value.title)
  if (t) await saveSpec({ ...wb.value.doc, title: t })
}
async function pin() {
  if (!wb.value) return
  await api.pin('workbook', wb.value.id, !wb.value.pinned)
  wb.value = await api.item('workbook', wb.value.id)
}
async function remove() {
  if (!wb.value || !confirm(`Mappe „${wb.value.title}“ wirklich löschen?`)) return
  await api.remove('workbook', wb.value.id)
  router.push('/mappen')
}
onMounted(load)
watch(() => route.params.id, load)
watch(() => live.version.workbooks, async () => {
  if (wb.value) {
    const fresh = await api.item('workbook', wb.value.id)
    if (fresh.updated_at !== wb.value.updated_at) await load()
  }
})
</script>

<style scoped>
.grid { display: grid; grid-template-columns: repeat(12, 1fr); gap: 16px; }
.tile { min-width: 0; overflow: hidden; }
@media (max-width: 1000px) { .tile { grid-column: span 12 !important; } }
</style>
