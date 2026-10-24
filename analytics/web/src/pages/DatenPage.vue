<template>
  <div class="page">
    <template v-if="ds">
      <PageHeader :title="ds.name" icon="mdi-table" :subtitle="`${ds.description || 'Datensatz'} · ${fmtInt.format(ds.rows_total)} Zeilen`" />
      <v-card>
        <v-table density="comfortable" fixed-header height="70vh">
          <thead><tr><th v-for="c in ds.columns" :key="c.name">{{ c.name }}</th></tr></thead>
          <tbody>
            <tr v-for="(r, i) in ds.rows" :key="i"><td v-for="c in ds.columns" :key="c.name">{{ cell(r[c.name], c.type) }}</td></tr>
          </tbody>
        </v-table>
        <div class="d-flex align-center pa-3">
          <v-btn variant="text" :disabled="offset === 0" prepend-icon="mdi-chevron-left" @click="page(-1)">Zurück</v-btn>
          <span class="muted text-small tabular">Zeilen {{ offset + 1 }}–{{ Math.min(offset + limit, ds.rows_total) }}</span>
          <v-btn variant="text" :disabled="offset + limit >= ds.rows_total" append-icon="mdi-chevron-right" @click="page(1)">Weiter</v-btn>
          <v-spacer />
          <v-btn variant="tonal" prepend-icon="mdi-robot-happy-outline" @click="meta.openChat(`Exportiere den Datensatz ${ds.dataset_id} als Excel und erkläre mir kurz, was darin steht.`)">Als Excel (über Agent)</v-btn>
        </div>
      </v-card>
    </template>
    <EmptyState v-else-if="error" icon="mdi-alert-circle-outline" :text="error">
      <v-btn variant="tonal" prepend-icon="mdi-refresh" @click="load">Noch einmal versuchen</v-btn>
    </EmptyState>
    <div v-else class="d-flex justify-center pa-10"><v-progress-circular indeterminate /></div>
  </div>
</template>

<script setup lang="ts">
import EmptyState from '@/components/EmptyState.vue'
import PageHeader from '@/components/PageHeader.vue'
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '@/api/client'
import { fmtDate, fmtInt, fmtNum, friendlyError } from '@/lib/format'
import { useMetaStore } from '@/stores/meta'

const route = useRoute()
const meta = useMetaStore()
const ds = ref<any>(null)
const error = ref('')
const offset = ref(0)
const limit = 100
function cell(v: any, type: string) {
  if (v === null || v === undefined) return ''
  if (type === 'date') return fmtDate(v)
  if (typeof v === 'number') return Number.isInteger(v) ? fmtInt.format(v) : fmtNum.format(v)
  return String(v)
}
async function load() {
  error.value = ''
  try {
    ds.value = await api.dataset(route.params.datasetId as string, limit, offset.value)
  } catch (e) {
    ds.value = null
    error.value = 'Der Datensatz konnte nicht geladen werden: ' + friendlyError(e)
  }
}
function page(d: number) {
  offset.value = Math.max(0, offset.value + d * limit)
  load()
}
onMounted(load)
watch(() => route.params.datasetId, () => { offset.value = 0; load() })
</script>
