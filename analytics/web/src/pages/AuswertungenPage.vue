<template>
  <div class="page">
    <PageHeader title="Auswertungen" icon="mdi-play-box-multiple-outline" subtitle="Fertige Auswertungen: ein paar Angaben machen, starten, Ergebnis ansehen. Neue Auswertungen kann der Assistent für dich anlegen.">
      <template #actions>
        <v-btn variant="tonal" prepend-icon="mdi-robot-happy-outline" @click="meta.openChat('Lege mir eine neue Auswertung an. Ich beschreibe dir, was sie jedes Mal zeigen soll: ')">Neue Auswertung vom Agenten</v-btn>
      </template>
    </PageHeader>
    <EmptyState v-if="!items.length" icon="mdi-play-box-multiple-outline" text="Noch keine Auswertungen. Der Assistent kann dir welche anlegen – sag ihm einfach, was du regelmäßig sehen möchtest." />
    <v-row v-else>
      <v-col v-for="p in items" :key="p.id" cols="12" sm="6" md="4">
        <v-card class="big-card pa-5" :to="`/auswertungen/${p.id}`">
          <div class="d-flex align-center ga-3">
            <span class="icon-tile" aria-hidden="true"><v-icon>{{ p.icon || 'mdi-play-box-multiple-outline' }}</v-icon></span>
            <span class="big-card__title">{{ p.title }}</span>
            <v-spacer />
            <v-icon v-if="p.pinned" size="16" class="muted">mdi-pin</v-icon>
          </div>
          <div class="mt-3 text-small" style="color: rgb(var(--text-secondary))">{{ p.description }}</div>
          <div class="muted mt-3 text-xs">
            <span v-for="(q, i) in p.parameters" :key="q.name">{{ i ? ' · ' : 'Angaben: ' }}{{ q.label }}</span>
            <span v-if="!p.parameters.length">Keine Angaben nötig</span>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { api, type PipelineSummary } from '@/api/client'
import EmptyState from '@/components/EmptyState.vue'
import PageHeader from '@/components/PageHeader.vue'
import { useLiveStore } from '@/stores/live'
import { useMetaStore } from '@/stores/meta'

const meta = useMetaStore()
const live = useLiveStore()
const items = ref<PipelineSummary[]>([])
async function load() {
  items.value = (await api.pipelines()).items
}
onMounted(load)
watch(() => live.version.pipelines, load)
</script>
