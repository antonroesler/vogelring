<template>
  <div class="page">
    <PageHeader title="Notizen" icon="mdi-note-text-outline" subtitle="Gemeinsames Gedächtnis für dich und den Assistenten: Erkenntnisse, offene Fragen, Vorhaben.">
      <template #actions><v-btn color="primary" prepend-icon="mdi-plus" @click="edit()">Neue Notiz</v-btn></template>
    </PageHeader>
    <EmptyState v-if="!notes.length" icon="mdi-note-text-outline" text="Noch keine Notizen. Halte hier fest, was du herausgefunden hast oder noch wissen möchtest – der Assistent liest mit.">
      <v-btn color="primary" prepend-icon="mdi-plus" @click="edit()">Neue Notiz</v-btn>
    </EmptyState>
    <v-row v-else>
      <v-col v-for="n in notes" :key="n.id" cols="12" md="6">
        <v-card class="pa-5">
          <div class="d-flex align-center">
            <span class="icon-tile mr-3" aria-hidden="true"><v-icon>{{ n.owner === 'agent' ? 'mdi-robot-happy-outline' : 'mdi-account' }}</v-icon></span>
            <span class="card-title mb-0">{{ n.title }}</span>
            <v-spacer />
            <span class="muted text-xs mr-1">{{ fmtDateTime(n.updated_at) }}</span>
            <v-btn size="small" variant="text" icon="mdi-pencil" @click="edit(n)" />
            <v-btn size="small" variant="text" icon="mdi-delete-outline" color="error" @click="remove(n)" />
          </div>
          <div class="md mt-2" v-html="md(n.doc.text)" />
          <div v-if="n.project || n.tags.length" class="muted mt-1 text-xs">{{ [n.project, ...n.tags].filter(Boolean).join(' · ') }}</div>
        </v-card>
      </v-col>
    </v-row>

    <v-dialog v-model="dialog" max-width="640">
      <v-card class="pa-6">
        <div class="card-title">Notiz</div>
        <v-text-field v-model="form.title" label="Titel (optional)" />
        <v-textarea v-model="form.text" label="Text" rows="8" autofocus />
        <v-text-field v-model="form.project" label="Projekt (optional)" />
        <div class="d-flex justify-end ga-2"><v-btn variant="text" @click="dialog = false">Abbrechen</v-btn><v-btn color="primary" :disabled="!form.text" @click="save">Speichern</v-btn></div>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import EmptyState from '@/components/EmptyState.vue'
import PageHeader from '@/components/PageHeader.vue'
import { onMounted, reactive, ref, watch } from 'vue'
import { marked } from 'marked'
import { api, type CatalogItem } from '@/api/client'
import { fmtDateTime } from '@/lib/format'
import { useLiveStore } from '@/stores/live'

const live = useLiveStore()
const notes = ref<CatalogItem<{ text: string }>[]>([])
const dialog = ref(false)
const form = reactive<{ id?: string; title: string; text: string; project: string }>({ title: '', text: '', project: '' })
const md = (s: string) => marked.parse(s || '') as string

async function load() {
  notes.value = (await api.list<{ text: string }>('note', { full: 1 })).items
}
function edit(n?: CatalogItem<{ text: string }>) {
  Object.assign(form, n ? { id: n.id, title: n.title, text: n.doc.text, project: n.project } : { id: undefined, title: '', text: '', project: '' })
  dialog.value = true
}
async function save() {
  await api.saveNote({ id: form.id, title: form.title || undefined, text: form.text, project: form.project })
  dialog.value = false
  await load()
}
async function remove(n: CatalogItem) {
  if (!confirm('Notiz löschen?')) return
  await api.remove('note', n.id)
  await load()
}
onMounted(load)
watch(() => live.version.notes, load)
</script>
