<template>
  <div class="page">
    <PageHeader title="Begriffe" icon="mdi-book-open-variant" subtitle="Was du mit „Nordufer“, „Mauserzeit“ oder „Kerngruppe“ meinst – einmal festlegen, überall verwenden. Auch der Assistent merkt sich diese Begriffe.">
      <template #actions><v-btn color="primary" prepend-icon="mdi-plus" @click="edit()">Neuer Begriff</v-btn></template>
    </PageHeader>
    <EmptyState v-if="!meta.definitions.length" icon="mdi-book-open-variant" text="Noch keine Begriffe gespeichert. Lege fest, was ein Ortsname, eine Vogelgruppe oder ein Zeitraum für dich bedeutet – oder erkläre es dem Assistenten im Chat.">
      <v-btn color="primary" prepend-icon="mdi-plus" @click="edit()">Neuer Begriff</v-btn>
    </EmptyState>
    <v-card v-else>
      <v-table>
        <thead><tr><th>Name</th><th>Art</th><th>Bedeutung</th><th>Inhalt</th><th></th></tr></thead>
        <tbody>
          <tr v-for="d in meta.definitions" :key="d.name">
            <td class="font-weight-medium">{{ d.name }}</td>
            <td>{{ KINDS.find((k) => k.value === d.kind)?.label }}</td>
            <td>{{ d.description }}</td>
            <td class="muted" style="max-width: 420px; white-space: normal">{{ d.sql || d.values.join(', ') }}{{ d.date_from ? ` ${d.date_from} – ${d.date_to}` : '' }}</td>
            <td class="text-right" style="white-space: nowrap">
              <v-btn size="small" variant="text" icon="mdi-pencil" @click="edit(d)" />
              <v-btn size="small" variant="text" icon="mdi-delete-outline" color="error" @click="remove(d)" />
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card>

    <v-dialog v-model="dialog" max-width="600">
      <v-card class="pa-6">
        <div class="card-title">{{ form.name && editing ? 'Begriff bearbeiten' : 'Neuer Begriff' }}</div>
        <v-text-field v-model="form.name" label="Name (so, wie du ihn sagst)" :disabled="editing" />
        <v-select v-model="form.kind" :items="KINDS" item-title="label" item-value="value" label="Art" />
        <v-text-field v-model="form.description" label="Bedeutung in einem Satz" />
        <v-combobox v-if="form.kind === 'place_group'" v-model="form.values" label="Orte (Namensteil genügt, Eingabe mit Enter)" multiple chips closable-chips hint="z. B. Mainkai, Weseler Werft, Portikusinsel" persistent-hint />
        <v-combobox v-else-if="form.kind === 'ring_group'" v-model="form.values" label="Ringnummern (Eingabe mit Enter)" multiple chips closable-chips />
        <template v-else-if="form.kind === 'period'">
          <v-select v-model="months" :items="monthItems" item-title="label" item-value="value" label="Monate" multiple chips closable-chips />
          <div class="d-flex ga-2"><v-text-field v-model="form.date_from" type="date" label="oder von" /><v-text-field v-model="form.date_to" type="date" label="bis" /></div>
        </template>
        <v-textarea v-else-if="form.kind === 'filter'" v-model="form.sql" label="Bedingung (für Fortgeschrittene, SQL)" rows="2" />
        <div class="d-flex justify-end ga-2 mt-2"><v-btn variant="text" @click="dialog = false">Abbrechen</v-btn><v-btn color="primary" :disabled="!form.name" @click="save">Speichern</v-btn></div>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import EmptyState from '@/components/EmptyState.vue'
import PageHeader from '@/components/PageHeader.vue'
import { reactive, ref, watch } from 'vue'
import { api, type Definition } from '@/api/client'
import { friendlyError, MONTHS_DE_LONG } from '@/lib/format'
import { useLiveStore } from '@/stores/live'
import { useMetaStore } from '@/stores/meta'

const meta = useMetaStore()
const live = useLiveStore()
const dialog = ref(false)
const editing = ref(false)
const months = ref<number[]>([])
const monthItems = MONTHS_DE_LONG.map((label, i) => ({ value: i + 1, label }))
const KINDS = [
  { value: 'place_group', label: 'Ortsgruppe' },
  { value: 'ring_group', label: 'Vogelgruppe' },
  { value: 'period', label: 'Zeitraum' },
  { value: 'filter', label: 'Bedingung (Fortgeschrittene)' },
  { value: 'note', label: 'Notiz' },
]
const form = reactive<Partial<Definition>>({ name: '', kind: 'place_group', description: '', values: [], sql: null, date_from: null, date_to: null })

function edit(d?: Definition) {
  editing.value = !!d
  Object.assign(form, d ? JSON.parse(JSON.stringify(d)) : { name: '', kind: 'place_group', description: '', values: [], sql: null, date_from: null, date_to: null })
  months.value = d?.kind === 'period' ? d.values.flatMap((v) => (v.includes('-') ? [] : [Number(v)])).filter((n) => n >= 1 && n <= 12) : []
  dialog.value = true
}
async function save() {
  try {
    const payload: any = { name: form.name, kind: form.kind, description: form.description, values: form.values || [] }
    if (form.kind === 'period') {
      payload.values = months.value.map(String)
      payload.date_from = form.date_from || null
      payload.date_to = form.date_to || null
    }
    if (form.kind === 'filter') payload.sql = form.sql
    await api.saveDefinition(payload)
    dialog.value = false
    await meta.reloadDefinitions()
    meta.notify('Begriff gespeichert.')
  } catch (e) {
    meta.notify(friendlyError(e), 'error')
  }
}
async function remove(d: Definition) {
  if (!confirm(`Begriff „${d.name}“ löschen?`)) return
  await api.deleteDefinition(d.name)
  await meta.reloadDefinitions()
}
watch(() => live.version.definitions, () => meta.reloadDefinitions())
</script>
