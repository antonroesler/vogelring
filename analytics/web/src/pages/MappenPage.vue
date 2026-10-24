<template>
  <div class="page">
    <PageHeader title="Mappen" icon="mdi-view-dashboard-outline" subtitle="Mehrere Ansichten mit gemeinsamen Filtern – daraus entstehen Berichte und Präsentationen.">
      <template #actions><v-btn color="primary" prepend-icon="mdi-plus" @click="dialog = true">Neue Mappe</v-btn></template>
    </PageHeader>
    <EmptyState v-if="!items.length" icon="mdi-view-dashboard-outline" text="Noch keine Mappen. Speichere Ansichten unter „Daten erkunden“ und füge sie einer Mappe hinzu – oder bitte den Assistenten darum.">
      <v-btn color="primary" prepend-icon="mdi-plus" @click="dialog = true">Neue Mappe</v-btn>
    </EmptyState>
    <v-row v-else>
      <v-col v-for="w in items" :key="w.id" cols="12" sm="6" md="4">
        <v-card class="big-card pa-5" :to="`/mappen/${w.id}`">
          <div class="d-flex align-center ga-3">
            <span class="icon-tile" aria-hidden="true"><v-icon>mdi-view-dashboard-outline</v-icon></span>
            <span class="big-card__title">{{ w.title }}</span>
            <v-spacer />
            <v-icon v-if="w.pinned" size="16" class="muted">mdi-pin</v-icon>
          </div>
          <div class="mt-3 text-small" style="color: rgb(var(--text-secondary))">{{ w.description || 'Ohne Beschreibung' }}</div>
          <div class="muted mt-3 text-xs">{{ (w.doc.tiles || []).length }} Kacheln · {{ relTime(w.updated_at) }}</div>
        </v-card>
      </v-col>
    </v-row>

    <v-dialog v-model="dialog" max-width="520">
      <v-card class="pa-6">
        <div class="card-title">Neue Mappe</div>
        <v-text-field v-model="title" label="Titel" autofocus />
        <v-textarea v-model="desc" label="Worum geht es? (optional)" rows="2" />
        <div class="d-flex justify-end ga-2"><v-btn variant="text" @click="dialog = false">Abbrechen</v-btn><v-btn color="primary" :disabled="!title" @click="create">Anlegen</v-btn></div>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api, type CatalogItem } from '@/api/client'
import EmptyState from '@/components/EmptyState.vue'
import PageHeader from '@/components/PageHeader.vue'
import { relTime } from '@/lib/format'
import { useLiveStore } from '@/stores/live'

const router = useRouter()
const live = useLiveStore()
const items = ref<CatalogItem[]>([])
const dialog = ref(false)
const title = ref('')
const desc = ref('')

async function load() {
  items.value = (await api.list('workbook', { full: 1 })).items
}
async function create() {
  const item = await api.saveWorkbook({ title: title.value, description: desc.value, tiles: [] })
  dialog.value = false
  router.push(`/mappen/${item.id}`)
}
onMounted(load)
watch(() => live.version.workbooks, load)
</script>
