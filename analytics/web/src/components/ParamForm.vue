<template>
  <div class="d-flex flex-column ga-3">
    <template v-for="p in parameters" :key="p.name">
      <v-autocomplete v-if="p.type === 'species'" v-model="values[p.name]" :items="choices.species" item-title="label" item-value="value" :label="p.label + (p.required ? '' : ' (optional)')" :hint="p.help || undefined" persistent-hint clearable />
      <v-combobox v-else-if="p.type === 'place'" v-model="values[p.name]" :items="choices.place" item-title="label" item-value="value" :return-object="false" :label="p.label + (p.required ? '' : ' (optional)')" :hint="p.help || 'Namensteil genügt, z. B. Ostpark'" persistent-hint clearable @update:search="(q: string) => searchPlace(q)" />
      <v-select v-else-if="p.type === 'group'" v-model="values[p.name]" :items="groupItems" item-title="label" item-value="value" :label="p.label + (p.required ? '' : ' (optional)')" :hint="p.help || 'Eine gespeicherte Gruppe'" persistent-hint clearable />
      <v-select v-else-if="p.type === 'place_group'" v-model="values[p.name]" :items="placeGroups" item-title="label" item-value="value" :label="p.label" :hint="p.help || undefined" persistent-hint clearable />
      <v-text-field v-else-if="p.type === 'ring'" v-model="values[p.name]" :label="p.label" :hint="p.help || 'Ringnummer genau wie im Eintrag'" persistent-hint />
      <v-select v-else-if="p.type === 'year'" v-model="values[p.name]" :items="years" :label="p.label" :hint="p.help || undefined" persistent-hint clearable />
      <div v-else-if="p.type === 'year_range'" class="d-flex ga-2">
        <v-select v-model="range(p.name).from" :items="years" :label="p.label + ' von'" />
        <v-select v-model="range(p.name).to" :items="years" :label="p.label + ' bis'" />
      </div>
      <v-select v-else-if="p.type === 'period'" v-model="values[p.name]" :items="monthItems" item-title="label" item-value="value" :label="p.label" :hint="p.help || 'Monate auswählen'" persistent-hint multiple chips closable-chips />
      <v-text-field v-else-if="p.type === 'number'" v-model.number="values[p.name]" type="number" :label="p.label" :hint="p.help || undefined" persistent-hint />
      <v-text-field v-else-if="p.type === 'date'" v-model="values[p.name]" type="date" :label="p.label" :hint="p.help || undefined" persistent-hint />
      <v-select v-else-if="p.type === 'choice'" v-model="values[p.name]" :items="p.choices || []" :label="p.label" :hint="p.help || undefined" persistent-hint />
      <v-checkbox v-else-if="p.type === 'boolean'" v-model="values[p.name]" :label="p.label" :hint="p.help || undefined" persistent-hint />
      <v-text-field v-else v-model="values[p.name]" :label="p.label" :hint="p.help || undefined" persistent-hint />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { api, type PipelineSummary } from '@/api/client'
import { useMetaStore } from '@/stores/meta'
import { MONTHS_DE_LONG } from '@/lib/format'

const props = defineProps<{ parameters: PipelineSummary['parameters']; modelValue: Record<string, any> }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: Record<string, any>): void }>()
const meta = useMetaStore()
const values = reactive<Record<string, any>>({ ...props.modelValue })
const choices = reactive<{ species: any[]; place: any[] }>({ species: [], place: [] })
const groupItems = ref<{ value: string; label: string }[]>([])
const years = computed(() => {
  const now = new Date().getFullYear()
  return Array.from({ length: now - 2006 }, (_, i) => now - i)
})
const monthItems = MONTHS_DE_LONG.map((label, i) => ({ value: i + 1, label }))
const placeGroups = computed(() => meta.definitionsOf('place_group').map((d) => ({ value: d.name, label: d.name })))

function range(name: string) {
  if (!values[name] || typeof values[name] !== 'object') values[name] = { from: null, to: null }
  return values[name]
}

for (const p of props.parameters) {
  if (values[p.name] === undefined && p.default !== undefined && p.default !== null) values[p.name] = p.default
  if (p.type === 'period' && !Array.isArray(values[p.name])) values[p.name] = values[p.name] ? [values[p.name]] : []
}

watch(values, (v) => emit('update:modelValue', JSON.parse(JSON.stringify(v))), { deep: true, immediate: true })

let timer: any = null
async function searchPlace(q: string) {
  clearTimeout(timer)
  timer = setTimeout(async () => {
    const r = await api.choices('sightings', 'place', q || '', 40)
    choices.place = r.items.map((c) => ({ value: c.value, label: `${c.label} (${c.count})` }))
  }, 250)
}

onMounted(async () => {
  if (props.parameters.some((p) => p.type === 'group')) {
    try {
      groupItems.value = (await api.groups()).items.map((g) => ({ value: g.id, label: g.name }))
    } catch {
      groupItems.value = []
    }
  }
  const [s, p] = await Promise.all([api.choices('sightings', 'species', '', 40), api.choices('sightings', 'place', '', 40)])
  choices.species = s.items.map((c) => ({ value: c.value, label: `${c.label} (${c.count})` }))
  choices.place = p.items.map((c) => ({ value: c.value, label: `${c.label} (${c.count})` }))
})
</script>
