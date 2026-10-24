<template>
  <div class="filters">
    <v-select v-if="has('groups') && groups.length" v-model="f.groups" :items="groups" item-title="label" item-value="value" label="Gruppe (gespeicherte Auswahl)" multiple chips closable-chips clearable hide-details>
      <template #chip="{ props: cp, item }"><v-chip v-bind="cp" :prepend-icon="undefined"><span class="dot" :style="{ background: item.raw.color || '#8aa' }" />{{ item.raw.name }}</v-chip></template>
      <template #item="{ props: ip, item }"><v-list-item v-bind="ip" :title="item.raw.name" :subtitle="item.raw.describe"><template #prepend><span class="dot mr-3" :style="{ background: item.raw.color || '#8aa' }" /></template></v-list-item></template>
    </v-select>
    <ChoiceSelect v-if="has('species')" v-model="f.species" :source="source" column="species" label="Art" />
    <ChoiceSelect v-if="has('places')" v-model="f.places" :source="source" column="place" label="Ort (Namensteil genügt)" free-text />
    <v-select v-if="has('place_groups') && placeGroups.length" v-model="f.place_groups" :items="placeGroups" item-title="label" item-value="value" label="Ortsgruppe" multiple chips closable-chips clearable hide-details />
    <div v-if="has('date_from')" class="d-flex ga-2">
      <v-text-field v-model="f.date_from" type="date" label="Datum von" hide-details clearable />
      <v-text-field v-model="f.date_to" type="date" label="Datum bis" hide-details clearable />
    </div>
    <ChoiceSelect v-if="has('years')" v-model="f.years" :source="source" column="year" label="Jahre" />
    <v-select v-if="has('months')" v-model="f.months" :items="monthItems" item-title="label" item-value="value" label="Monate" multiple chips closable-chips clearable hide-details />
    <v-select v-if="has('seasons')" v-model="f.seasons" :items="seasonItems" item-title="label" item-value="value" label="Jahreszeit" multiple chips closable-chips clearable hide-details />
    <v-select v-if="has('periods') && periods.length" v-model="f.periods" :items="periods" item-title="label" item-value="value" label="Zeitraum (gespeichert)" multiple chips closable-chips clearable hide-details />
    <v-expansion-panels v-model="more" variant="accordion" class="mt-1">
      <v-expansion-panel title="Weitere Filter" elevation="0">
        <v-expansion-panel-text>
          <div class="filters">
            <ChoiceSelect v-if="has('rings')" v-model="f.rings" :source="source" column="ring" label="Ringnummer" free-text />
            <v-combobox v-if="has('ring_contains')" v-model="f.ring_contains" label="Ring enthält (z. B. W)" multiple chips closable-chips clearable hide-details />
            <v-select v-if="has('ring_groups') && ringGroups.length" v-model="f.ring_groups" :items="ringGroups" item-title="label" item-value="value" label="Vogelgruppe" multiple chips closable-chips clearable hide-details />
            <v-select v-if="has('status')" v-model="f.status" :items="opts('status')" item-title="label" item-value="value" label="Status" multiple chips closable-chips clearable hide-details />
            <v-select v-if="has('age')" v-model="f.age" :items="opts('age')" item-title="label" item-value="value" label="Alter" multiple chips closable-chips clearable hide-details />
            <v-select v-if="has('sex')" v-model="f.sex" :items="opts('sex')" item-title="label" item-value="value" label="Geschlecht" multiple chips closable-chips clearable hide-details />
            <ChoiceSelect v-if="has('melder')" v-model="f.melder" :source="source" column="melder" label="Melder" />
            <ChoiceSelect v-if="has('ringing_places')" v-model="f.ringing_places" :source="source" column="ringing_place" label="Beringungsort (Namensteil)" free-text />
            <v-select v-if="has('ringing_age')" v-model="f.ringing_age" :items="opts('ringing_age')" item-title="label" item-value="value" label="Alter bei Beringung" multiple chips closable-chips clearable hide-details />
            <ChoiceSelect v-if="has('exclude_places')" v-model="f.exclude_places" :source="source" column="place" label="Orte ausschließen" free-text />
            <div v-if="has('around_place')" class="d-flex ga-2 align-center">
              <v-text-field v-model="f.around_place" label="Umkreis um Ort" hide-details clearable />
              <v-text-field v-model.number="f.around_place_km" type="number" label="km" hide-details style="max-width: 90px" />
            </div>
            <v-checkbox v-if="has('only_with_coords')" v-model="f.only_with_coords" label="Nur Einträge mit Koordinaten" hide-details density="compact" />
            <v-checkbox v-if="has('only_exact_location')" v-model="f.only_exact_location" label="Nur exakte Koordinaten" hide-details density="compact" />
          </div>
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { api, type GroupSummary } from '@/api/client'
import { useLiveStore } from '@/stores/live'
import { useMetaStore } from '@/stores/meta'
import type { Filters } from '@/stores/builder'
import { MONTHS_DE_LONG } from '@/lib/format'
import ChoiceSelect from './ChoiceSelect.vue'

const props = defineProps<{ modelValue: Filters; source: string }>()
const meta = useMetaStore()
const live = useLiveStore()
const groupItems = ref<GroupSummary[]>([])
const groups = computed(() => groupItems.value.map((g) => ({ value: g.id, label: g.name, name: g.name, describe: g.describe, color: g.color })))
async function loadGroups() {
  try {
    groupItems.value = (await api.groups()).items
  } catch {
    groupItems.value = []
  }
}
onMounted(loadGroups)
watch(() => live.version.groups, loadGroups)
const more = ref<number | null>(null)
const f = computed(() => props.modelValue)
const supported = computed(() => new Set(meta.sourceByKey(props.source)?.filters || []))
const has = (name: string) => supported.value.has(name)
const opts = (name: string) => meta.sources?.filters.find((x) => x.name === name)?.options || []
const monthItems = MONTHS_DE_LONG.map((label, i) => ({ value: i + 1, label }))
const seasonItems = computed(() => (meta.sources?.seasons || []).map((s) => ({ value: s.key, label: s.label })))
const placeGroups = computed(() => meta.definitionsOf('place_group').map((d) => ({ value: d.name, label: `${d.name} – ${d.description || d.values.join(', ')}` })))
const ringGroups = computed(() => meta.definitionsOf('ring_group').map((d) => ({ value: d.name, label: `${d.name} (${d.values.length} Ringe)` })))
const periods = computed(() => meta.definitionsOf('period').map((d) => ({ value: d.name, label: `${d.name} – ${d.description || d.values.join(', ')}` })))
</script>

<style scoped>
.filters { display: flex; flex-direction: column; gap: 14px; }
.filters :deep(.v-expansion-panel-text__wrapper) { padding: 12px 0 4px 0; }
.filters :deep(.v-expansion-panel-title) { padding-left: 4px; padding-right: 4px; min-height: 44px; }
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; flex: none; }
</style>
