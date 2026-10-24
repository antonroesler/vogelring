<template>
  <div class="bin-control mb-3">
    <div class="bin-control__label">Klassen für „{{ column.label }}“</div>
    <template v-if="column.type === 'date'">
      <v-btn-toggle v-model="m.date_part" mandatory class="vr-toggle vr-toggle--wrap" density="compact" @update:model-value="m.mode = 'date'">
        <v-btn value="year">Jahr</v-btn>
        <v-btn value="month">Monat</v-btn>
        <v-btn value="year_month">Jahr-Monat</v-btn>
        <v-btn value="season">Jahreszeit</v-btn>
      </v-btn-toggle>
    </template>
    <template v-else>
      <v-btn-toggle v-model="m.mode" mandatory class="vr-toggle" density="compact">
        <v-btn value="auto">Automatisch</v-btn>
        <v-btn value="width">Breite</v-btn>
        <v-btn value="edges">Grenzen</v-btn>
      </v-btn-toggle>
      <div v-if="m.mode === 'width'" class="d-flex ga-2 mt-2 align-start">
        <v-text-field v-model.number="m.width" type="number" min="0" step="any" label="Klassenbreite" hide-details density="compact" class="flex-grow-1" />
        <v-text-field v-model="m.unit" label="Einheit" placeholder="km" hide-details density="compact" class="bin-control__unit" />
      </div>
      <div v-else-if="m.mode === 'edges'" class="d-flex ga-2 mt-2 align-start">
        <v-text-field v-model="m.edges" label="Grenzen" placeholder="1, 5, 20, 100" hint="z. B. 1, 5, 20, 100 → < 1, 1–5, 5–20, 20–100, ≥ 100" persistent-hint density="compact" class="flex-grow-1" />
        <v-text-field v-model="m.unit" label="Einheit" placeholder="km" hide-details density="compact" class="bin-control__unit" />
      </div>
      <div v-else class="bin-control__hint">Etwa 8 runde Klassen, passend zu den Werten.</div>
    </template>
  </div>
</template>

<script setup lang="ts">
import type { BinForm } from '@/stores/builder'

defineProps<{ column: { name: string; label: string; type: string } }>()
const m = defineModel<BinForm>({ required: true })
</script>

<style scoped>
.bin-control { padding: 10px 12px 12px; border: 1px solid rgb(var(--border-light)); border-radius: 12px; background: rgb(var(--surface-primary-alt)); }
.bin-control__label { font-size: 12px; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; color: rgb(var(--text-tertiary)); margin-bottom: 8px; }
.bin-control__hint { font-size: 12.5px; color: rgb(var(--text-tertiary)); margin-top: 6px; }
.bin-control .v-btn-toggle.vr-toggle .v-btn { height: 32px; font-size: 13px; }
.bin-control__unit { flex: 0 0 88px; }
</style>
