<template>
  <div class="page">
    <PageHeader title="Gruppen" icon="mdi-folder-multiple-outline" subtitle="Gespeicherte Auswahlen – z. B. „Graugänse, im Ostpark als Jungvögel beringt“. Du nutzt sie in Ansichten, Mappen und Auswertungen wieder und vergleichst sie miteinander.">
      <template #actions>
        <v-text-field v-model="q" label="Suchen" prepend-inner-icon="mdi-magnify" hide-details clearable style="width: 260px" />
        <v-btn variant="tonal" prepend-icon="mdi-compare-horizontal" :disabled="items.length < 2" @click="openCompare()">Vergleichen</v-btn>
        <v-btn color="primary" prepend-icon="mdi-plus" @click="openNew">Neue Gruppe</v-btn>
      </template>
    </PageHeader>

    <EmptyState v-if="!filtered.length" icon="mdi-folder-multiple-outline" text="Noch keine Gruppen. Lege eine Auswahl an, die du öfter brauchst – oder sag dem Assistenten, welche Vögel du meinst.">
      <v-btn color="primary" prepend-icon="mdi-plus" @click="openNew">Neue Gruppe</v-btn>
      <v-btn variant="tonal" prepend-icon="mdi-robot-happy-outline" @click="meta.openChat('Lege mir eine Gruppe an: ')">Agent fragen</v-btn>
    </EmptyState>

    <v-row v-else>
      <v-col v-for="g in filtered" :key="g.id" cols="12" sm="6" md="4" lg="3">
        <v-card class="big-card group-card d-flex flex-column pa-5" :to="`/gruppen/${g.id}`" :style="{ borderLeft: `6px solid ${g.color || '#B8C4CC'}` }">
          <div class="d-flex align-start">
            <div class="text-h6 text-primary" style="line-height: 1.25; min-width: 0">{{ g.name }}</div>
            <v-spacer />
            <v-icon v-if="g.pinned" size="16" color="warning" class="ml-2 mt-1">mdi-pin</v-icon>
          </div>
          <div class="muted mt-2 clamp" style="font-size: 13.5px">{{ g.description || g.describe }}</div>
          <div class="mt-3 d-flex flex-wrap ga-3 counts">
            <template v-if="g.stats">
              <span><strong>{{ fmtInt.format(g.stats.sightings) }}</strong> Sichtungen</span>
              <span><strong>{{ fmtInt.format(g.stats.birds) }}</strong> Vögel</span>
              <span v-if="g.stats.first">{{ year(g.stats.first) }}–{{ year(g.stats.last) }}</span>
            </template>
            <span v-else class="muted">Zahlen werden geladen …</span>
          </div>
          <div class="d-flex flex-wrap ga-1 mt-3">
            <v-chip v-for="t in g.tags" :key="t" size="x-small" variant="tonal">{{ t }}</v-chip>
            <v-chip v-if="g.ring_count" size="x-small" variant="tonal" color="secondary">{{ g.ring_count }} Ringe</v-chip>
            <v-chip v-if="g.excluded_count" size="x-small" variant="tonal" color="warning">{{ g.excluded_count }} ausgeschlossen</v-chip>
          </div>
          <div class="muted mt-auto pt-3" style="font-size: 12px">{{ relTime(g.updated_at) }}</div>
          <v-card-actions class="px-0 pb-0 pt-2" @click.stop.prevent>
            <v-btn size="small" variant="text" icon="mdi-pin-outline" :color="g.pinned ? 'warning' : undefined" title="Anheften" @click="pin(g)" />
            <v-btn size="small" variant="text" icon="mdi-compass-outline" title="In Erkunden öffnen" @click="explore(g)" />
            <v-btn size="small" variant="text" icon="mdi-compare-horizontal" title="Vergleichen" @click="openCompare(g)" />
            <v-spacer />
            <v-btn size="small" variant="text" icon="mdi-delete-outline" color="error" title="Löschen" @click="remove(g)" />
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <v-dialog v-model="newDialog" max-width="560">
      <v-card class="pa-6">
        <div class="card-title">Neue Gruppe</div>
        <v-text-field v-model="newName" label="Name (so, wie du sie nennst)" autofocus @keyup.enter="create" />
        <v-textarea v-model="newDesc" label="Worum geht es? (optional)" rows="2" />
        <div class="muted mb-3" style="font-size: 13px">Die Filter legst du im nächsten Schritt fest.</div>
        <div class="d-flex justify-end ga-2"><v-btn variant="text" @click="newDialog = false">Abbrechen</v-btn><v-btn color="primary" :disabled="!newName.trim()" :loading="busy" @click="create">Anlegen</v-btn></div>
      </v-card>
    </v-dialog>

    <GroupCompareDialog v-model="compareDialog" :groups="items" :preselect="comparePreselect" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api, type GroupSummary } from '@/api/client'
import EmptyState from '@/components/EmptyState.vue'
import GroupCompareDialog from '@/components/GroupCompareDialog.vue'
import PageHeader from '@/components/PageHeader.vue'
import { fmtInt, friendlyError, relTime } from '@/lib/format'
import { useLiveStore } from '@/stores/live'
import { useMetaStore } from '@/stores/meta'

const router = useRouter()
const live = useLiveStore()
const meta = useMetaStore()
const items = ref<GroupSummary[]>([])
const q = ref('')
const busy = ref(false)
const newDialog = ref(false)
const newName = ref('')
const newDesc = ref('')
const compareDialog = ref(false)
const comparePreselect = ref<string[]>([])

const filtered = computed(() => items.value.filter((g) => !q.value || `${g.name} ${g.description} ${g.describe} ${g.tags.join(' ')}`.toLowerCase().includes(q.value.toLowerCase())))
const year = (iso: string | null) => (iso ? iso.slice(0, 4) : '')

async function load() {
  items.value = (await api.groups()).items
  // numbers are computed live and cached on the server; fetch the missing ones one by one (cheap, read-only)
  for (const g of items.value.filter((x) => !x.stats)) {
    try {
      const s = await api.groupSummary(g.id)
      const cur = items.value.find((x) => x.id === g.id)
      if (cur) cur.stats = s
    } catch {
      /* shown as „Zahlen werden geladen“ */
    }
  }
}
function openNew() {
  newName.value = ''
  newDesc.value = ''
  newDialog.value = true
}
async function create() {
  if (!newName.value.trim()) return
  busy.value = true
  try {
    const g = await api.createGroup({ name: newName.value.trim(), description: newDesc.value.trim() })
    newDialog.value = false
    router.push(`/gruppen/${g.id}`)
  } catch (e) {
    meta.notify(friendlyError(e), 'error')
  } finally {
    busy.value = false
  }
}
async function pin(g: GroupSummary) {
  await api.pin('group', g.id, !g.pinned)
  await load()
}
async function remove(g: GroupSummary) {
  if (!confirm(`Gruppe „${g.name}“ wirklich löschen? Ansichten, die sie verwenden, verlieren diesen Filter.`)) return
  await api.remove('group', g.id)
  meta.notify('Gruppe gelöscht.')
  await load()
}
function explore(g: GroupSummary) {
  router.push({ path: '/erkunden', query: { group: g.id } })
}
function openCompare(g?: GroupSummary) {
  comparePreselect.value = g ? [g.id] : []
  compareDialog.value = true
}
onMounted(load)
watch(() => live.version.groups, load)
</script>

<style scoped>
.group-card { min-height: 100%; }
.clamp { display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.counts { font-size: 13.5px; }
</style>
