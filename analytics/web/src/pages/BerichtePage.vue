<template>
  <div class="page">
    <PageHeader title="Berichte & Präsentationen" icon="mdi-file-document-multiple-outline" subtitle="Alle erstellten Berichte (PDF, Word) und Präsentationen (PowerPoint). Neue entstehen aus Mappen oder über den Assistenten." />
    <v-row>
      <v-col cols="12" md="7">
        <v-card class="pa-5">
          <div class="d-flex align-center mb-3">
            <div class="card-title mb-0">Berichte</div>
            <v-spacer />
            <v-btn size="small" variant="tonal" prepend-icon="mdi-robot-happy-outline" @click="meta.openChat('Erstelle mir einen Kurzbericht zu folgender Frage: ')">Bericht vom Agenten</v-btn>
          </div>
          <v-list density="comfortable">
            <v-list-item v-for="r in reports" :key="r.report_id" prepend-icon="mdi-file-document-outline" :title="r.title" :subtitle="fmtDateTime(r.created_at)">
              <template #append>
                <v-btn size="small" variant="text" :href="r.html" target="_blank" prepend-icon="mdi-web">Ansehen</v-btn>
                <v-btn size="small" variant="text" :href="r.pdf" prepend-icon="mdi-file-pdf-box">PDF</v-btn>
                <v-btn size="small" variant="text" :href="r.docx" prepend-icon="mdi-file-word">Word</v-btn>
                <v-btn size="small" variant="text" prepend-icon="mdi-presentation" :loading="busy === r.report_id" @click="toDeck(r.report_id)">Präsentation</v-btn>
              </template>
            </v-list-item>
          </v-list>
          <div v-if="!reports.length" class="muted text-small">Noch keine Berichte.</div>
        </v-card>
      </v-col>
      <v-col cols="12" md="5">
        <v-card class="pa-5">
          <div class="card-title">Präsentationen</div>
          <v-list density="comfortable">
            <v-list-item v-for="d in decks" :key="d.deck_id" prepend-icon="mdi-presentation" :title="d.title" :subtitle="`${d.slides} Folien · ${fmtDateTime(d.created_at)}`">
              <template #append><v-btn size="small" variant="text" :href="d.pptx_url" prepend-icon="mdi-download">PowerPoint</v-btn></template>
            </v-list-item>
          </v-list>
          <div v-if="!decks.length" class="muted text-small">Noch keine Präsentationen.</div>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import PageHeader from '@/components/PageHeader.vue'
import { onMounted, ref, watch } from 'vue'
import { api, type DeckItem, type ReportItem } from '@/api/client'
import { fmtDateTime, friendlyError } from '@/lib/format'
import { useLiveStore } from '@/stores/live'
import { useMetaStore } from '@/stores/meta'

const meta = useMetaStore()
const live = useLiveStore()
const reports = ref<ReportItem[]>([])
const decks = ref<DeckItem[]>([])
const busy = ref('')
async function load() {
  const [r, d] = await Promise.all([api.reports(), api.decks()])
  reports.value = r.items
  decks.value = d.items
}
async function toDeck(id: string) {
  busy.value = id
  try {
    await api.deckFromReport(id)
    meta.notify('Präsentation erstellt.')
    await load()
  } catch (e) {
    meta.notify(friendlyError(e), 'error')
  } finally {
    busy.value = ''
  }
}
onMounted(load)
watch(() => [live.version.reports, live.version.decks], load)
</script>
