<template>
  <v-autocomplete
    v-if="!freeText"
    v-model="model"
    :items="items"
    item-title="label"
    item-value="value"
    :label="label"
    :loading="loading"
    multiple
    chips
    closable-chips
    hide-details
    density="comfortable"
    :menu-props="{ maxHeight: 360 }"
    @update:search="onSearch"
  />
  <v-combobox
    v-else
    v-model="model"
    v-model:menu="menu"
    :items="items"
    item-title="label"
    item-value="value"
    :return-object="false"
    :label="label"
    :loading="loading"
    multiple
    chips
    closable-chips
    hide-details
    density="comfortable"
    :menu-props="{ maxHeight: 360 }"
    @update:search="onSearch"
    @update:model-value="menu = false"
  />
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { api, type Choice } from '@/api/client'

const props = withDefaults(defineProps<{ modelValue: any[]; source: string; column: string; label: string; freeText?: boolean; staticItems?: { value: any; label: string }[]; filters?: Record<string, any> }>(), { freeText: false, staticItems: undefined, filters: undefined })
const emit = defineEmits<{ (e: 'update:modelValue', v: any[]): void }>()
const model = ref<any[]>(props.modelValue || [])
// free text: after a pick the list would reopen in full over the form – close it, the chip is enough
const menu = ref(false)
const items = ref<(Choice | { value: any; label: string })[]>([])
const loading = ref(false)
let timer: any = null

watch(() => props.modelValue, (v) => (model.value = v || []))
watch(model, (v) => emit('update:modelValue', v))

async function load(q = '') {
  if (props.staticItems) {
    items.value = props.staticItems
    return
  }
  loading.value = true
  try {
    const res = await api.choices(props.source, props.column, q, 60, props.filters)
    items.value = res.items.map((c) => ({ value: c.value, label: c.count ? `${c.label} (${c.count})` : c.label, count: c.count }))
    // keep selected values visible even when not in the current result page
    for (const v of model.value) if (!items.value.some((i) => i.value === v)) items.value.push({ value: v, label: String(v) })
  } finally {
    loading.value = false
  }
}
function onSearch(q: string) {
  if (props.staticItems) return
  onSearchQuery(q || '')
  clearTimeout(timer)
  timer = setTimeout(() => load(q || ''), 250)
}
let lastQuery = ''
function onSearchQuery(q: string) {
  lastQuery = q
}
onMounted(() => load())
watch(() => props.source, () => load())
// other filters changed → counts change; the server ignores the filters on this very column
watch(
  () => JSON.stringify(props.filters || {}),
  () => {
    clearTimeout(timer)
    timer = setTimeout(() => load(lastQuery), 300)
  },
)
</script>
