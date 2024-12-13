<template>
  <v-card>
    <v-card-title class="d-flex align-center">
      Vogel Details
      <v-spacer></v-spacer>
      <v-btn
        v-if="bird"
        icon
        variant="text"
        :to="`/birds/${bird.ring}`"
        v-tooltip="'Detailansicht öffnen'"
      >
        <v-icon>mdi-open-in-new</v-icon>
      </v-btn>
    </v-card-title>
    <v-card-text>
      <v-progress-circular
        v-if="!bird"
        indeterminate
        color="primary"
        class="ma-4"
      ></v-progress-circular>

      <template v-else>
        <v-list>
          <v-list-item>
            <v-list-item-title>Spezies</v-list-item-title>
            <v-list-item-subtitle>{{ bird.species }}</v-list-item-subtitle>
          </v-list-item>
          <v-list-item>
            <v-list-item-title>Ring</v-list-item-title>
            <v-list-item-subtitle>{{ bird.ring }}</v-list-item-subtitle>
          </v-list-item>
          <v-list-item>
            <v-list-item-title>Anzahl Sichtungen</v-list-item-title>
            <v-list-item-subtitle>{{ bird.sighting_count }}</v-list-item-subtitle>
          </v-list-item>
          <v-list-item>
            <v-list-item-title>Erste Sichtung</v-list-item-title>
            <v-list-item-subtitle>{{ formatDate(bird.first_seen) }}</v-list-item-subtitle>
          </v-list-item>
          <v-list-item>
            <v-list-item-title>Letzte Sichtung</v-list-item-title>
            <v-list-item-subtitle>{{ formatDate(bird.last_seen) }}</v-list-item-subtitle>
          </v-list-item>
        </v-list>

        <v-divider class="my-4"></v-divider>

        <h3 class="text-h6 mb-2">Andere Artenbestimmungen</h3>
        <v-list v-if="Object.keys(bird.other_species_identifications).length > 0">
          <v-list-item v-for="(count, species) in bird.other_species_identifications" :key="species">
            <v-list-item-title>{{ species }}</v-list-item-title>
            <v-list-item-subtitle>{{ count }} mal</v-list-item-subtitle>
          </v-list-item>
        </v-list>
        <p v-else class="text-body-1">Ausschließlich als {{ bird.species }} identifiziert.</p>
      </template>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { format } from 'date-fns';
import type { BirdMeta } from '@/types';

const props = defineProps<{
  bird: BirdMeta | null;
}>();

const formatDate = (date: string) => {
  return format(new Date(date), 'dd.MM.yyyy');
};
</script>