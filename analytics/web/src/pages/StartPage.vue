<template>
  <div class="page">
    <PageHeader :title="name ? `Guten Tag, ${name}!` : 'Guten Tag!'" subtitle="Was möchtest du heute auswerten? Frag den Assistenten oder erkunde die Daten selbst.">
      <template #actions><v-btn color="primary" prepend-icon="mdi-robot-happy-outline" @click="meta.openChat()">Assistenten fragen</v-btn></template>
    </PageHeader>

    <v-row>
      <v-col v-for="c in cards" :key="c.to" cols="12" sm="6" md="3">
        <v-card class="big-card pa-5" :to="c.to">
          <span class="icon-tile icon-tile--lg" aria-hidden="true"><v-icon>{{ c.icon }}</v-icon></span>
          <div class="big-card__title mt-3">{{ c.title }}</div>
          <div class="text-small mt-1" style="color: rgb(var(--text-secondary))">{{ c.text }}</div>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mt-4">
      <v-col cols="12" md="7">
        <v-card class="pa-5">
          <div class="d-flex align-center mb-3">
            <div class="card-title mb-0">Zuletzt passiert</div>
            <v-spacer />
            <v-btn size="small" variant="text" to="/live" prepend-icon="mdi-broadcast">Live verfolgen</v-btn>
          </div>
          <ActivityFeed :items="activity" />
        </v-card>
      </v-col>
      <v-col cols="12" md="5">
        <v-card class="pa-5 mb-6">
          <div class="card-title">Angeheftet</div>
          <v-list density="compact">
            <v-list-item v-for="p in pinned" :key="p.kind + p.id" :to="linkOf(p)" :prepend-icon="KIND_ICON[p.kind]" :title="p.title" :subtitle="p.description" />
          </v-list>
          <div v-if="!pinned.length" class="muted">Noch nichts angeheftet. Ansichten, Mappen und Auswertungen lassen sich mit dem Stecknadel-Symbol hier ablegen.</div>
        </v-card>
        <v-card class="pa-5">
          <div class="card-title">Beispiele zum Ausprobieren</div>
          <v-list density="compact">
            <v-list-item v-for="q in examples" :key="q" prepend-icon="mdi-message-text-outline" :title="q" @click="meta.openChat(q)" />
          </v-list>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { api, type ActivityItem, type CatalogItem } from '@/api/client'
import ActivityFeed from '@/components/ActivityFeed.vue'
import PageHeader from '@/components/PageHeader.vue'
import { KIND_ICON } from '@/lib/format'
import { useLiveStore } from '@/stores/live'
import { useMetaStore } from '@/stores/meta'

const meta = useMetaStore()
const live = useLiveStore()
const activity = ref<ActivityItem[]>([])
const pinned = ref<CatalogItem[]>([])
const GENERIC = new Set(['dev', 'admin', 'info', 'mail', 'office', 'kontakt', 'test', 'user', 'vogelring', 'post', 'hallo', 'hello', 'me', 'root', 'support'])
const name = computed(() => {
  const local = (meta.meta?.user || '').split('@')[0].toLowerCase()
  const first = local.split(/[._-]/)[0]
  if (!/^[a-zäöüß]{3,20}$/.test(first) || GENERIC.has(first)) return ''
  return first.charAt(0).toUpperCase() + first.slice(1)
})

const cards = [
  { to: '/erkunden', icon: 'mdi-compass-outline', title: 'Daten erkunden', text: 'Diagramme, Karten und Tabellen selbst zusammenstellen.' },
  { to: '/auswertungen', icon: 'mdi-play-box-multiple-outline', title: 'Auswertungen', text: 'Fertige Auswertungen mit wenigen Angaben starten.' },
  { to: '/mappen', icon: 'mdi-view-dashboard-outline', title: 'Mappen', text: 'Mehrere Ansichten zu einer Übersicht bündeln.' },
  { to: '/berichte', icon: 'mdi-file-document-multiple-outline', title: 'Berichte & Präsentationen', text: 'PDF, Word und PowerPoint herunterladen.' },
]
const examples = [
  'Wie viele Kanadagänse waren diesen Sommer zur Mauser im Ostpark? Bitte mit Karte.',
  'Zeig mir, aus welchen Beringungsorten die Graugänse am Main stammen.',
  'Was gibt es Neues in den letzten zwei Wochen?',
  'Erstelle einen Kurzbericht zur Ortstreue im Ostpark.',
]

async function load() {
  const [a, v, w, p] = await Promise.all([api.activity(25), api.list('view', { limit: 50 }), api.list('workbook', { limit: 50 }), api.list('pipeline', { limit: 50 })])
  activity.value = a.items
  pinned.value = [...v.items, ...w.items, ...p.items].filter((i) => i.pinned)
}
function linkOf(p: CatalogItem) {
  return p.kind === 'view' ? `/erkunden/${p.id}` : p.kind === 'workbook' ? `/mappen/${p.id}` : `/auswertungen/${p.id}`
}
onMounted(load)
watch(() => live.events.length, () => (activity.value = [...live.events].reverse().slice(0, 25).map((e) => e as ActivityItem)))
</script>
