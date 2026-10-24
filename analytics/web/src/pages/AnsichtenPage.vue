<template>
  <div class="page">
    <PageHeader title="Ansichten" icon="mdi-image-multiple-outline" subtitle="Gespeicherte Diagramme, Karten und Tabellen – von dir oder vom Assistenten.">
      <template #actions>
        <v-text-field v-model="q" label="Suchen" prepend-inner-icon="mdi-magnify" hide-details clearable style="width: 260px" />
        <v-btn color="primary" to="/erkunden" prepend-icon="mdi-plus">Neue Ansicht</v-btn>
      </template>
    </PageHeader>
    <EmptyState v-if="!filtered.length" icon="mdi-image-multiple-outline" text="Noch keine Ansichten. Erstelle eine unter „Daten erkunden“ oder bitte den Assistenten darum.">
      <v-btn color="primary" to="/erkunden" prepend-icon="mdi-compass-outline">Daten erkunden</v-btn>
    </EmptyState>
    <v-row v-else>
      <v-col v-for="v in filtered" :key="v.id" cols="12" sm="6" md="4" lg="3">
        <v-card class="big-card d-flex flex-column" :to="`/erkunden/${v.id}`">
          <div class="thumb" :style="v.png_url ? { backgroundImage: `url(${v.png_url}?t=${encodeURIComponent(v.updated_at)})` } : undefined">
            <div v-if="!v.png_url" class="d-flex align-center justify-center fill-height muted"><v-icon size="40">{{ KIND_ICON[v.kind] }}</v-icon></div>
          </div>
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon size="18" class="mr-2 muted">{{ KIND_ICON[v.kind] }}</v-icon>
              <span class="font-weight-medium text-truncate">{{ v.title }}</span>
              <v-spacer />
              <v-icon v-if="v.pinned" size="16" class="muted">mdi-pin</v-icon>
            </div>
            <div class="muted text-truncate text-xs mt-1">{{ v.description }}</div>
            <div class="muted text-xs">{{ relTime(v.updated_at) }}</div>
          </v-card-text>
          <v-card-actions class="mt-auto px-3" @click.stop.prevent>
            <v-btn size="small" variant="text" icon="mdi-pin-outline" :color="v.pinned ? 'primary' : undefined" title="Anheften" @click="pin(v)" />
            <v-btn size="small" variant="text" icon="mdi-download" :href="v.png_url" title="Bild herunterladen" :disabled="!v.png_url" />
            <v-btn size="small" variant="text" icon="mdi-open-in-new" :href="v.interactive_url" target="_blank" title="Interaktiv öffnen" :disabled="!v.interactive_url" />
            <v-spacer />
            <v-btn size="small" variant="text" icon="mdi-delete-outline" color="error" title="Löschen" @click="remove(v)" />
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import EmptyState from '@/components/EmptyState.vue'
import PageHeader from '@/components/PageHeader.vue'
import { computed, onMounted, ref, watch } from 'vue'
import { api, type ViewSummary } from '@/api/client'
import { KIND_ICON, relTime } from '@/lib/format'
import { useLiveStore } from '@/stores/live'
import { useMetaStore } from '@/stores/meta'

const live = useLiveStore()
const meta = useMetaStore()
const items = ref<ViewSummary[]>([])
const q = ref('')
const filtered = computed(() => items.value.filter((v) => !q.value || `${v.title} ${v.description}`.toLowerCase().includes(q.value.toLowerCase())))

async function load() {
  items.value = (await api.views()).items
}
async function pin(v: ViewSummary) {
  await api.pin('view', v.id, !v.pinned)
  await load()
}
async function remove(v: ViewSummary) {
  if (!confirm(`Ansicht „${v.title}“ wirklich löschen?`)) return
  await api.remove('view', v.id)
  meta.notify('Ansicht gelöscht.')
  await load()
}
onMounted(load)
watch(() => live.version.views, load)
</script>
