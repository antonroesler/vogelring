<template>
  <div class="filters">
    <v-select v-if="has('groups') && groups.length" v-model="f.groups" :items="groups" item-title="label" item-value="value" label="Gruppe (in mindestens einer – oder)" multiple chips closable-chips clearable hide-details>
      <template #chip="{ props: cp, item }"><v-chip v-bind="cp" :prepend-icon="undefined"><span class="dot" :style="{ background: item.raw.color || '#8aa' }" />{{ item.raw.name }}</v-chip></template>
      <template #item="{ props: ip, item }"><v-list-item v-bind="ip" :title="item.raw.name" :subtitle="item.raw.describe"><template #prepend><span class="dot mr-3" :style="{ background: item.raw.color || '#8aa' }" /></template></v-list-item></template>
    </v-select>
    <ChoiceSelect v-if="has('species')" v-model="f.species" :source="source" :filters="ctx" column="species" label="Art" />
    <ChoiceSelect v-if="has('places')" v-model="f.places" :source="source" :filters="ctx" column="place" label="Ort (Namensteil genügt)" free-text />
    <v-select v-if="has('place_groups') && placeGroups.length" v-model="f.place_groups" :items="placeGroups" item-title="label" item-value="value" label="Ortsgruppe" multiple chips closable-chips clearable hide-details />
    <div v-if="has('date_from')" class="d-flex ga-2">
      <v-text-field v-model="f.date_from" type="date" label="Datum von" hide-details clearable />
      <v-text-field v-model="f.date_to" type="date" label="Datum bis" hide-details clearable />
    </div>
    <ChoiceSelect v-if="has('years')" v-model="f.years" :source="source" :filters="ctx" column="year" label="Jahre" />
    <v-select v-if="has('months')" v-model="f.months" :items="monthItems" item-title="label" item-value="value" label="Monate" multiple chips closable-chips clearable hide-details />
    <v-select v-if="has('seasons')" v-model="f.seasons" :items="seasonItems" item-title="label" item-value="value" label="Jahreszeit" multiple chips closable-chips clearable hide-details />
    <v-select v-if="has('periods') && periods.length" v-model="f.periods" :items="periods" item-title="label" item-value="value" label="Zeitraum (gespeichert)" multiple chips closable-chips clearable hide-details />

    <v-expansion-panels v-model="open" variant="accordion" multiple class="mt-1">
      <v-expansion-panel value="more" title="Weitere Filter" elevation="0">
        <v-expansion-panel-text>
          <div class="filters">
            <ChoiceSelect v-if="has('rings')" v-model="f.rings" :source="source" :filters="ctx" column="ring" label="Ringnummer" free-text />
            <v-combobox v-if="has('ring_contains')" v-model="f.ring_contains" label="Ring enthält (z. B. W)" multiple chips closable-chips clearable hide-details />
            <v-select v-if="has('ring_groups') && ringGroups.length" v-model="f.ring_groups" :items="ringGroups" item-title="label" item-value="value" label="Vogelgruppe" multiple chips closable-chips clearable hide-details />
            <v-select v-if="has('status')" v-model="f.status" :items="opts('status')" item-title="label" item-value="value" label="Status" multiple chips closable-chips clearable hide-details />
            <v-select v-if="has('age')" v-model="f.age" :items="opts('age')" item-title="label" item-value="value" label="Alter" multiple chips closable-chips clearable hide-details />
            <v-select v-if="has('sex')" v-model="f.sex" :items="opts('sex')" item-title="label" item-value="value" label="Geschlecht" multiple chips closable-chips clearable hide-details />
            <ChoiceSelect v-if="has('melder')" v-model="f.melder" :source="source" :filters="ctx" column="melder" label="Melder" />
            <ChoiceSelect v-if="has('ringing_places')" v-model="f.ringing_places" :source="source" :filters="ctx" column="ringing_place" label="Beringungsort (Namensteil)" free-text />
            <v-select v-if="has('ringing_age')" v-model="f.ringing_age" :items="opts('ringing_age')" item-title="label" item-value="value" label="Alter bei Beringung" multiple chips closable-chips clearable hide-details />
            <ChoiceSelect v-if="has('exclude_places')" v-model="f.exclude_places" :source="source" :filters="ctx" column="place" label="Orte ausschließen" free-text />
            <div v-if="has('around_place')" class="d-flex ga-2 align-center">
              <v-text-field v-model="f.around_place" label="Umkreis um Ort" hide-details clearable />
              <v-text-field v-model.number="f.around_place_km" type="number" label="km" hide-details style="max-width: 90px" />
            </div>
            <v-checkbox v-if="has('only_with_coords')" v-model="f.only_with_coords" label="Nur Einträge mit Koordinaten" hide-details density="compact" />
            <v-checkbox v-if="has('only_exact_location')" v-model="f.only_exact_location" label="Nur exakte Koordinaten" hide-details density="compact" />
          </div>
        </v-expansion-panel-text>
      </v-expansion-panel>

      <v-expansion-panel v-if="withGroups" value="groups" elevation="0">
        <v-expansion-panel-title>
          Gruppen verknüpfen (und / nicht)
          <v-chip v-if="groupCount" size="x-small" class="ml-2" variant="tonal">{{ groupCount }}</v-chip>
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <div class="muted hint">Mit gespeicherten Gruppen rechnen: „in mindestens einer“ (oder) wählst du oben. Hier kommt dazu: nur, was zugleich in allen genannten Gruppen liegt (und), und was in keiner der genannten liegen darf (nicht). So entsteht z. B. „in A oder B, aber nicht in C“.</div>
          <div class="filters">
            <v-select v-if="has('all_groups')" v-model="f.all_groups" :items="groups" item-title="label" item-value="value" label="In allen diesen Gruppen (und)" multiple chips closable-chips clearable hide-details>
              <template #chip="{ props: cp, item }"><v-chip v-bind="cp" :prepend-icon="undefined"><span class="dot" :style="{ background: item.raw.color || '#8aa' }" />{{ item.raw.name }}</v-chip></template>
              <template #item="{ props: ip, item }"><v-list-item v-bind="ip" :title="item.raw.name" :subtitle="item.raw.describe"><template #prepend><span class="dot mr-3" :style="{ background: item.raw.color || '#8aa' }" /></template></v-list-item></template>
            </v-select>
            <v-select v-if="has('exclude_groups')" v-model="f.exclude_groups" :items="groups" item-title="label" item-value="value" label="Nicht in diesen Gruppen (ausschließen)" multiple chips closable-chips clearable hide-details>
              <template #chip="{ props: cp, item }"><v-chip v-bind="cp" :prepend-icon="undefined"><span class="dot" :style="{ background: item.raw.color || '#8aa' }" />{{ item.raw.name }}</v-chip></template>
              <template #item="{ props: ip, item }"><v-list-item v-bind="ip" :title="item.raw.name" :subtitle="item.raw.describe"><template #prepend><span class="dot mr-3" :style="{ background: item.raw.color || '#8aa' }" /></template></v-list-item></template>
            </v-select>
          </div>
        </v-expansion-panel-text>
      </v-expansion-panel>

      <v-expansion-panel v-if="withBlocks" value="logic" elevation="0">
        <v-expansion-panel-title>
          Und / Oder / Nicht – Bedingungen kombinieren
          <v-chip v-if="blockCount" size="x-small" class="ml-2" variant="tonal">{{ blockCount }}</v-chip>
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <div class="muted hint">Die Filter oben gelten immer zusammen (und). Hier legst du Alternativen fest (oder) – etwa „Mai oder Juni“ <em>oder</em> „April mit Status Mausergast“ – und schließt Fälle aus (nicht).</div>

          <div class="block-intro">Oder: mindestens eine dieser Bedingungen trifft zu</div>
          <div v-for="(_, i) in block.any_of" :key="'any' + i" class="block-card">
            <div class="block-head">
              <span>Bedingung {{ i + 1 }}</span>
              <v-spacer />
              <v-btn size="small" variant="text" @click="block.any_of.splice(i, 1)">Entfernen</v-btn>
            </div>
            <FilterPanel v-model="block.any_of[i]" :source="source" level="fields" />
          </div>
          <v-btn variant="outlined" size="small" prepend-icon="mdi-plus" class="mb-5" @click="block.any_of.push(emptyFields())">Oder-Bedingung hinzufügen</v-btn>

          <div class="block-intro">Nicht: keine dieser Bedingungen trifft zu</div>
          <div v-for="(_, i) in block.none_of" :key="'none' + i" class="block-card block-card--excl">
            <div class="block-head">
              <span>Ausschluss {{ i + 1 }}</span>
              <v-spacer />
              <v-btn size="small" variant="text" @click="block.none_of.splice(i, 1)">Entfernen</v-btn>
            </div>
            <FilterPanel v-model="block.none_of[i]" :source="source" level="fields" />
          </div>
          <v-btn variant="outlined" size="small" prepend-icon="mdi-plus" @click="block.none_of.push(emptyFields())">Ausschluss hinzufügen</v-btn>
        </v-expansion-panel-text>
      </v-expansion-panel>

      <v-expansion-panel v-if="withBirds && (has('birds_of') || has('birds_not_of'))" value="birds" elevation="0">
        <v-expansion-panel-title>
          Vögel statt Sichtungen
          <v-chip v-if="birdCount" size="x-small" class="ml-2" variant="tonal">{{ birdCount }}</v-chip>
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <div class="muted hint">Nimmt alle Einträge der Vögel, auf die die Bedingung mindestens einmal zutrifft – z. B. überall, wo die Mausergäste aus dem Ostpark sonst noch auftauchen.</div>

          <template v-if="has('birds_of')">
            <div class="block-intro">Vögel, auf die die Bedingung mindestens einmal zutrifft</div>
            <div v-if="full.birds_of" class="block-card">
              <div class="block-head">
                <span>Bedingung (Sichtungen)</span>
                <v-spacer />
                <v-btn size="small" variant="text" @click="full.birds_of = null">Entfernen</v-btn>
              </div>
              <FilterPanel v-model="full.birds_of" source="sightings" level="block" />
            </div>
            <v-btn v-else variant="outlined" size="small" prepend-icon="mdi-bird" class="mb-5" @click="full.birds_of = emptyBlock()">Bedingung festlegen</v-btn>
          </template>

          <template v-if="has('birds_not_of')">
            <div class="block-intro" :class="{ 'mt-4': full.birds_of }">Vögel, auf die die Bedingung nie zutrifft</div>
            <div v-if="full.birds_not_of" class="block-card block-card--excl">
              <div class="block-head">
                <span>Bedingung (Sichtungen)</span>
                <v-spacer />
                <v-btn size="small" variant="text" @click="full.birds_not_of = null">Entfernen</v-btn>
              </div>
              <FilterPanel v-model="full.birds_not_of" source="sightings" level="block" />
            </div>
            <v-btn v-else variant="outlined" size="small" prepend-icon="mdi-bird-off" @click="full.birds_not_of = emptyBlock()">Bedingung festlegen</v-btn>
          </template>
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
import { cleanFilters, emptyBlock, emptyFields, type FilterBlock, type FilterFields, type Filters } from '@/stores/builder'
import { MONTHS_DE_LONG } from '@/lib/format'
import ChoiceSelect from './ChoiceSelect.vue'

defineOptions({ name: 'FilterPanel' })

/**
 * level: 'full' = everything (views, groups, workbooks); 'block' = fields + Oder/Ausschluss (inside „Vögel statt
 * Sichtungen“); 'fields' = simple fields only (inside an Oder-/Ausschluss-Bedingung). The nesting mirrors the server's
 * FilterSpec → FilterBlock → FilterFields and is deliberately not recursive.
 */
const props = withDefaults(defineProps<{ modelValue: FilterFields | FilterBlock | Filters; source: string; level?: 'full' | 'block' | 'fields' }>(), { level: 'full' })
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

const open = ref<string[]>([])
const f = computed(() => props.modelValue as FilterFields)
const block = computed(() => props.modelValue as FilterBlock)
const full = computed(() => props.modelValue as Filters)
const withBlocks = computed(() => props.level !== 'fields')
const withBirds = computed(() => props.level === 'full')
const withGroups = computed(() => groups.value.length > 0 && (has('all_groups') || has('exclude_groups')))
const groupCount = computed(() => (withGroups.value ? (f.value.all_groups?.length || 0) + (f.value.exclude_groups?.length || 0) : 0))
const ctx = computed(() => cleanFilters(props.modelValue))
const supported = computed(() => new Set(meta.sourceByKey(props.source)?.filters || []))
const has = (name: string) => supported.value.has(name)
const opts = (name: string) => meta.sources?.filters.find((x) => x.name === name)?.options || []
const monthItems = MONTHS_DE_LONG.map((label, i) => ({ value: i + 1, label }))
const seasonItems = computed(() => (meta.sources?.seasons || []).map((s) => ({ value: s.key, label: s.label })))
const placeGroups = computed(() => meta.definitionsOf('place_group').map((d) => ({ value: d.name, label: `${d.name} – ${d.description || d.values.join(', ')}` })))
const ringGroups = computed(() => meta.definitionsOf('ring_group').map((d) => ({ value: d.name, label: `${d.name} (${d.values.length} Ringe)` })))
const periods = computed(() => meta.definitionsOf('period').map((d) => ({ value: d.name, label: `${d.name} – ${d.description || d.values.join(', ')}` })))
const blockCount = computed(() => (withBlocks.value ? (block.value.any_of?.length || 0) + (block.value.none_of?.length || 0) : 0))
const birdCount = computed(() => (withBirds.value ? (full.value.birds_of ? 1 : 0) + (full.value.birds_not_of ? 1 : 0) : 0))

// a saved spec with blocks should show them right away
watch(
  () => [blockCount.value, birdCount.value, groupCount.value],
  ([b, v, g]) => {
    if (b && !open.value.includes('logic')) open.value = [...open.value, 'logic']
    if (v && !open.value.includes('birds')) open.value = [...open.value, 'birds']
    if (g && !open.value.includes('groups')) open.value = [...open.value, 'groups']
  },
  { immediate: true },
)
</script>

<style scoped>
.filters { display: flex; flex-direction: column; gap: 14px; }
.filters :deep(.v-expansion-panel-text__wrapper) { padding: 12px 0 4px 0; }
.filters :deep(.v-expansion-panel-title) { padding-left: 4px; padding-right: 4px; min-height: 44px; }
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; flex: none; }
.hint { font-size: 13px; line-height: 1.45; margin-bottom: 14px; }
.block-intro { font-size: 12px; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; color: rgb(var(--text-tertiary)); margin: 0 0 8px 0; }
.block-card { border: 1px solid rgb(var(--border-light)); border-radius: 12px; padding: 12px 14px 14px 14px; margin-bottom: 10px; background: rgb(var(--surface-primary-alt)); }
.block-card--excl { border-style: dashed; }
.block-head { display: flex; align-items: center; font-size: 13px; font-weight: 600; color: rgb(var(--text-secondary)); margin-bottom: 10px; }
</style>
