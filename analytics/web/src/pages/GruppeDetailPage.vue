<template>
  <div class="page">
    <template v-if="group">
      <PageHeader :title="group.name" icon="mdi-folder-multiple-outline">
        <template #title-append><span class="color-dot" :style="{ background: form.color || '#B8C4CC' }" /></template>
        <template #subtitle>{{ group.description || describe }}</template>
        <template #actions>
          <v-btn variant="tonal" :prepend-icon="group.pinned ? 'mdi-pin' : 'mdi-pin-outline'" @click="pin">{{ group.pinned ? 'Angeheftet' : 'Anheften' }}</v-btn>
          <v-btn variant="tonal" prepend-icon="mdi-compass-outline" @click="explore">In Erkunden öffnen</v-btn>
          <v-btn variant="tonal" prepend-icon="mdi-compare-horizontal" @click="compareDialog = true">Vergleichen</v-btn>
          <v-btn variant="tonal" color="secondary" prepend-icon="mdi-robot-happy-outline" @click="askAgent">Agent fragen</v-btn>
          <v-btn variant="text" prepend-icon="mdi-arrow-left" to="/gruppen">Alle Gruppen</v-btn>
        </template>
      </PageHeader>

      <v-row>
        <v-col cols="12" md="5" lg="4">
          <v-card class="pa-5">
            <div class="d-flex align-center mb-3">
              <div class="card-title mb-0">Festlegung</div>
              <v-spacer />
              <v-chip v-if="dirty" size="small" color="warning" variant="tonal">nicht gespeichert</v-chip>
            </div>
            <v-text-field v-model="form.name" label="Name" class="mb-3" hide-details />
            <v-textarea v-model="form.description" label="Worum geht es? (optional)" rows="2" auto-grow class="mb-3" hide-details />
            <div class="section-label">Farbe (für Vergleiche)</div>
            <div class="d-flex flex-wrap ga-2 mb-4">
              <button v-for="c in COLORS" :key="c" type="button" class="swatch" :class="{ active: form.color === c }" :style="{ background: c }" :title="c" @click="form.color = c" />
              <button type="button" class="swatch none" :class="{ active: !form.color }" title="Keine Farbe" @click="form.color = null">×</button>
            </div>
            <v-combobox v-model="form.tags" label="Schlagwörter (Eingabe mit Enter)" multiple chips closable-chips hide-details class="mb-4" />

            <div class="section-label">Art der Gruppe</div>
            <v-btn-toggle v-model="form.scope" mandatory class="vr-toggle mb-2">
              <v-btn value="sightings" prepend-icon="mdi-binoculars">Sichtungen</v-btn>
              <v-btn value="birds" prepend-icon="mdi-bird">Vögel</v-btn>
            </v-btn-toggle>
            <div class="muted mb-4" style="font-size: 12.5px">
              <template v-if="form.scope === 'birds'">Alle Einträge der Vögel, auf die die Bedingung mindestens einmal zutrifft – also auch, wo diese Vögel sonst noch gesehen wurden.</template>
              <template v-else>Nur die Einträge, die die Bedingung erfüllen.</template>
            </div>

            <div class="section-label">Filter</div>
            <FilterPanel v-model="form.filters" source="sightings" />

            <div class="section-label mt-4">Ringliste (optional)</div>
            <v-combobox v-model="form.ring_list" label="Nur diese Ringnummern (Eingabe mit Enter oder Komma)" multiple chips closable-chips hide-details clearable @update:model-value="splitRings" />
            <div class="muted mt-1" style="font-size: 12.5px">Für Gruppen, die aus einer festen Liste von Vögeln bestehen. Wird mit den Filtern kombiniert.</div>

            <div class="muted mt-4" style="font-size: 13px"><strong>Bedeutet:</strong> {{ describe }}</div>
            <v-alert v-if="error" type="warning" variant="tonal" class="mt-3" :text="error" />
            <div class="d-flex ga-2 mt-4">
              <v-btn color="primary" prepend-icon="mdi-content-save" :loading="saving" :disabled="!form.name.trim()" @click="save">Speichern</v-btn>
              <v-btn variant="text" :disabled="!dirty" @click="resetForm">Verwerfen</v-btn>
              <v-spacer />
              <v-btn variant="text" color="error" icon="mdi-delete-outline" title="Gruppe löschen" @click="remove" />
            </div>
          </v-card>
        </v-col>

        <v-col cols="12" md="7" lg="8">
          <v-card class="pa-5 mb-6">
            <div class="d-flex align-center mb-3">
              <div class="card-title mb-0">Zahlen</div>
              <v-spacer />
              <v-btn size="small" variant="text" prepend-icon="mdi-refresh" :loading="statsLoading" @click="loadStats">Neu berechnen</v-btn>
            </div>
            <template v-if="stats">
              <div class="d-flex flex-wrap ga-6 mb-4">
                <div class="kpi"><div class="kpi-v">{{ fmtInt.format(stats.sightings) }}</div><div class="kpi-l">Sichtungen</div></div>
                <div class="kpi"><div class="kpi-v">{{ fmtInt.format(stats.birds) }}</div><div class="kpi-l">Vögel</div></div>
                <div class="kpi"><div class="kpi-v">{{ fmtInt.format(stats.places) }}</div><div class="kpi-l">Orte</div></div>
                <div v-if="stats.scope === 'birds' && stats.matching_sightings != null" class="kpi"><div class="kpi-v">{{ fmtInt.format(stats.matching_sightings) }}</div><div class="kpi-l">Sichtungen, die die Bedingung selbst erfüllen</div></div>
                <div class="kpi"><div class="kpi-v">{{ stats.first ? `${fmtDate(stats.first)} – ${fmtDate(stats.last)}` : '–' }}</div><div class="kpi-l">Zeitraum</div></div>
              </div>
              <div v-if="stats.years.length" class="years mb-4">
                <div v-for="y in stats.years" :key="y.year" class="year" :title="`${y.year}: ${fmtInt.format(y.sightings)} Sichtungen`">
                  <div class="bar" :style="{ height: `${Math.max(3, (y.sightings / maxYear) * 70)}px`, background: form.color || '#228096' }" />
                  <div class="yl">{{ String(y.year).slice(2) }}</div>
                </div>
              </div>
              <div class="d-flex flex-wrap ga-6">
                <div v-if="stats.species.length" style="flex: 1; min-width: 220px">
                  <div class="section-label">Arten</div>
                  <div v-for="s in stats.species" :key="s.label" class="d-flex justify-space-between" style="font-size: 13.5px"><span>{{ s.label }}</span><span class="muted">{{ fmtInt.format(s.sightings) }} · {{ fmtInt.format(s.birds) }} Vögel</span></div>
                </div>
                <div v-if="stats.status.length" style="flex: 1; min-width: 180px">
                  <div class="section-label">Status</div>
                  <div v-for="s in stats.status" :key="s.label" class="d-flex justify-space-between" style="font-size: 13.5px"><span>{{ STATUS[s.label] || s.label }}</span><span class="muted">{{ fmtInt.format(s.sightings) }}</span></div>
                </div>
              </div>
              <div class="muted mt-3" style="font-size: 12px">Stand {{ fmtDateTime(stats.computed_at) }} · live aus der Vogelring-Datenbank (nur lesend)</div>
            </template>
            <div v-else-if="statsError" class="muted">{{ statsError }}</div>
            <div v-else class="d-flex justify-center pa-6"><v-progress-circular indeterminate color="secondary" /></div>
          </v-card>

          <v-card class="pa-5">
            <div class="d-flex align-center flex-wrap ga-2 mb-3">
              <div class="card-title mb-0">Einträge</div>
              <v-spacer />
              <v-switch v-model="withExcluded" label="Ausgeschlossene mit anzeigen" hide-details density="compact" color="warning" @update:model-value="reloadPreview" />
            </div>
            <div class="muted mb-3" style="font-size: 13px">Einzelne Einträge kannst du von Hand ausschließen – etwa Fehlablesungen. Sie bleiben in Vogelring unverändert und werden nur in dieser Gruppe nicht mitgezählt.</div>
            <div v-if="preview?.scope === 'birds'" class="muted mb-3" style="font-size: 12.5px"><span class="match-dot match-dot--on" /> erfüllt die Bedingung selbst · <span class="match-dot" /> weitere Sichtung desselben Vogels</div>
            <v-table v-if="preview" density="compact" class="preview-table">
              <thead>
                <tr><th v-if="preview.scope === 'birds'" style="width: 28px"></th><th>Datum</th><th>Ring</th><th>Art</th><th>Ort</th><th>Status</th><th>Melder</th><th>Beringungsort</th><th></th></tr>
              </thead>
              <tbody>
                <tr v-for="r in preview.rows" :key="r.id" :class="{ excluded: r.excluded }">
                  <td v-if="preview.scope === 'birds'" :title="r.matches ? 'Erfüllt die Bedingung selbst' : 'Weitere Sichtung desselben Vogels'"><span class="match-dot" :class="{ 'match-dot--on': r.matches }" /></td>
                  <td>{{ fmtDate(r.date) }}</td>
                  <td class="font-weight-bold">{{ r.ring }}</td>
                  <td>{{ r.species }}</td>
                  <td>{{ r.place }}</td>
                  <td>{{ r.status || '' }}</td>
                  <td>{{ r.melder || '' }}</td>
                  <td class="muted">{{ r.ringing_place || '' }}</td>
                  <td class="text-right" style="white-space: nowrap">
                    <v-btn v-if="!r.excluded" size="x-small" variant="text" color="warning" prepend-icon="mdi-eye-off-outline" :loading="busyId === r.id" @click="exclude(r, true)">Ausschließen</v-btn>
                    <v-btn v-else size="x-small" variant="text" color="success" prepend-icon="mdi-eye-outline" :loading="busyId === r.id" @click="exclude(r, false)">Wieder aufnehmen</v-btn>
                  </td>
                </tr>
              </tbody>
            </v-table>
            <div v-if="preview" class="d-flex align-center mt-2">
              <v-btn variant="text" :disabled="offset === 0" prepend-icon="mdi-chevron-left" @click="page(-1)">Zurück</v-btn>
              <span class="muted" style="font-size: 13px">{{ preview.total ? `Zeilen ${offset + 1}–${Math.min(offset + limit, preview.total)} von ${fmtInt.format(preview.total)}` : 'Keine Einträge' }}</span>
              <v-btn variant="text" :disabled="offset + limit >= preview.total" append-icon="mdi-chevron-right" @click="page(1)">Weiter</v-btn>
            </div>
            <div v-else-if="previewError" class="muted">{{ previewError }}</div>
            <div v-else class="d-flex justify-center pa-6"><v-progress-circular indeterminate color="secondary" /></div>
          </v-card>
        </v-col>
      </v-row>

      <GroupCompareDialog v-model="compareDialog" :groups="allGroups" :preselect="[group.id]" />
    </template>
    <EmptyState v-else-if="error" icon="mdi-alert-circle-outline" :text="error">
      <v-btn variant="tonal" to="/gruppen">Alle Gruppen</v-btn>
    </EmptyState>
    <div v-else class="d-flex justify-center pa-10"><v-progress-circular indeterminate color="secondary" /></div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, type GroupPreview, type GroupScope, type GroupStats, type GroupSummary } from '@/api/client'
import EmptyState from '@/components/EmptyState.vue'
import FilterPanel from '@/components/FilterPanel.vue'
import GroupCompareDialog from '@/components/GroupCompareDialog.vue'
import PageHeader from '@/components/PageHeader.vue'
import { fmtDate, fmtDateTime, fmtInt, friendlyError } from '@/lib/format'
import { cleanFilters, emptyFilters, toFilterForm, type Filters } from '@/stores/builder'
import { useLiveStore } from '@/stores/live'
import { useMetaStore } from '@/stores/meta'

const route = useRoute()
const router = useRouter()
const meta = useMetaStore()
const live = useLiveStore()

const COLORS = ['#00436C', '#228096', '#37906D', '#D07B4D', '#8E6C8A', '#C9A227', '#5B7DB1', '#A64D79']
const STATUS: Record<string, string> = { BV: 'Brutvogel', MG: 'Mausergast', NB: 'Nichtbrüter', RV: 'Reviervogel', TF: 'Totfund', ohne: 'ohne Status' }

const group = ref<(GroupSummary & { doc: any }) | null>(null)
const allGroups = ref<GroupSummary[]>([])
const error = ref('')
const saving = ref(false)
const compareDialog = ref(false)
const form = reactive<{ name: string; description: string; color: string | null; tags: string[]; scope: GroupScope; filters: Filters; ring_list: string[] }>({ name: '', description: '', color: null, tags: [], scope: 'sightings', filters: emptyFilters(), ring_list: [] })
let saved = ''

const stats = ref<GroupStats | null>(null)
const statsLoading = ref(false)
const statsError = ref('')
const preview = ref<GroupPreview | null>(null)
const previewError = ref('')
const withExcluded = ref(false)
const offset = ref(0)
const limit = 50
const busyId = ref('')

const maxYear = computed(() => Math.max(1, ...(stats.value?.years.map((y) => y.sightings) || [1])))
const describe = computed(() => group.value?.describe || '')

function toSpec() {
  return {
    name: form.name.trim(),
    description: form.description.trim(),
    color: form.color,
    tags: form.tags,
    scope: form.scope,
    filters: cleanFilters(form.filters),
    ring_list: form.ring_list,
    excluded_ids: group.value?.doc?.excluded_ids || [],
  }
}
const dirty = computed(() => JSON.stringify(toSpec()) !== saved)

function fillForm(g: GroupSummary & { doc: any }) {
  form.name = g.doc.name || g.name
  form.description = g.doc.description || ''
  form.color = g.doc.color || null
  form.tags = [...(g.doc.tags || [])]
  form.scope = g.doc.scope || 'sightings'
  form.filters = toFilterForm(g.doc.filters)
  form.ring_list = [...(g.doc.ring_list || [])]
  saved = JSON.stringify(toSpec())
}
function resetForm() {
  if (group.value) fillForm(group.value)
}
function splitRings(v: any) {
  const out: string[] = []
  for (const x of (v as any[]) || []) for (const part of String(x).split(/[,;\s]+/)) if (part && !out.includes(part)) out.push(part)
  form.ring_list = out
}

async function load() {
  const id = route.params.id as string
  error.value = ''
  try {
    group.value = await api.group(id)
    fillForm(group.value)
    loadStats()
    reloadPreview()
    api.groups().then((r) => (allGroups.value = r.items)).catch(() => {})
  } catch (e) {
    group.value = null
    error.value = 'Die Gruppe konnte nicht geladen werden: ' + friendlyError(e)
  }
}
async function loadStats() {
  if (!group.value) return
  statsLoading.value = true
  statsError.value = ''
  try {
    stats.value = await api.groupSummary(group.value.id)
  } catch (e) {
    stats.value = null
    statsError.value = friendlyError(e)
  } finally {
    statsLoading.value = false
  }
}
async function reloadPreview() {
  if (!group.value) return
  previewError.value = ''
  try {
    preview.value = await api.groupPreview(group.value.id, limit, offset.value, withExcluded.value)
  } catch (e) {
    preview.value = null
    previewError.value = friendlyError(e)
  }
}
function page(d: number) {
  offset.value = Math.max(0, offset.value + d * limit)
  reloadPreview()
}
async function save() {
  if (!group.value) return
  saving.value = true
  error.value = ''
  try {
    group.value = await api.updateGroup(group.value.id, toSpec())
    fillForm(group.value)
    meta.notify('Gruppe gespeichert.')
    offset.value = 0
    loadStats()
    reloadPreview()
  } catch (e) {
    error.value = friendlyError(e)
  } finally {
    saving.value = false
  }
}
async function exclude(r: any, excluded: boolean) {
  if (!group.value) return
  busyId.value = r.id
  try {
    group.value = await api.groupExclude(group.value.id, [r.id], excluded)
    saved = JSON.stringify({ ...JSON.parse(saved), excluded_ids: group.value.doc.excluded_ids })
    if (withExcluded.value) r.excluded = excluded
    else preview.value = await api.groupPreview(group.value.id, limit, offset.value, false)
    loadStats()
  } catch (e) {
    meta.notify(friendlyError(e), 'error')
  } finally {
    busyId.value = ''
  }
}
async function pin() {
  if (!group.value) return
  await api.pin('group', group.value.id, !group.value.pinned)
  group.value = await api.group(group.value.id)
}
async function remove() {
  if (!group.value || !confirm(`Gruppe „${group.value.name}“ wirklich löschen?`)) return
  await api.remove('group', group.value.id)
  meta.notify('Gruppe gelöscht.')
  router.push('/gruppen')
}
function explore() {
  if (group.value) router.push({ path: '/erkunden', query: { group: group.value.id } })
}
function askAgent() {
  if (!group.value) return
  meta.openChat(`Schau dir meine Gruppe „${group.value.name}“ an (${describe.value}) und sag mir in einfacher Sprache, was darin steckt und was daran auffällig ist. Gruppen-ID: ${group.value.id}`)
}

onMounted(load)
watch(() => route.params.id, load)
watch(
  () => live.version.groups,
  async () => {
    // the agent may have changed this group – pick it up unless the user is mid-edit
    if (group.value && !dirty.value) {
      const fresh = await api.group(group.value.id).catch(() => null)
      if (fresh && fresh.updated_at !== group.value.updated_at) {
        group.value = fresh
        fillForm(fresh)
        loadStats()
        reloadPreview()
      }
    }
  },
)
</script>

<style scoped>
.color-dot { display: inline-block; width: 16px; height: 16px; border-radius: 50%; }
.section-label { font-size: 12.5px; font-weight: 600; letter-spacing: 0.02em; color: #5b6b76; margin-bottom: 8px; }
.swatch { width: 28px; height: 28px; border-radius: 50%; border: 2px solid transparent; cursor: pointer; }
.swatch.active { border-color: #00436C; box-shadow: 0 0 0 2px #fff inset; }
.swatch.none { background: #fff; border: 1px dashed #9aa; color: #678; font-size: 14px; }
.kpi-v { font-size: 22px; font-weight: 700; color: #00436C; line-height: 1.2; }
.kpi-l { font-size: 12.5px; color: #5b6b76; }
.years { display: flex; align-items: flex-end; gap: 4px; height: 92px; overflow-x: auto; padding-bottom: 2px; }
.year { display: flex; flex-direction: column; align-items: center; justify-content: flex-end; min-width: 22px; height: 100%; }
.bar { width: 16px; border-radius: 3px 3px 0 0; }
.yl { font-size: 10.5px; color: #5b6b76; margin-top: 3px; }
.preview-table tr.excluded td { color: #9aa; text-decoration: line-through; }
.match-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; border: 1.5px solid rgb(var(--border-heavy)); vertical-align: middle; }
.match-dot--on { background: rgb(var(--brand)); border-color: rgb(var(--brand)); }
.preview-table td, .preview-table th { font-size: 13px !important; }
</style>
