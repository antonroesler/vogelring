<template>
  <v-form @submit.prevent="saveSighting">
    <v-row>
      <v-col cols="12" md="6">
        <v-text-field
          v-model="localSighting.reading"
          label="Ablesung"
        ></v-text-field>
      </v-col>
      <v-col cols="12" md="6">
        <v-text-field
          v-model="localSighting.ring"
          label="Ring"
        ></v-text-field>
      </v-col>
      <v-col cols="12" md="6">
        <v-text-field
          v-model="localSighting.species"
          label="Spezies"
        ></v-text-field>
      </v-col>
      <v-col cols="12" md="6">
        <v-text-field
          v-model="localSighting.place"
          label="Ort"
        ></v-text-field>
      </v-col>
      <v-col cols="12" md="6">
        <v-text-field
          v-model="localSighting.group_size"
          label="Gruppengröße"
          type="number"
        ></v-text-field>
      </v-col>
      <v-col cols="12" md="6">
        <v-text-field
          v-model="localSighting.melder"
          label="Melder"
        ></v-text-field>
      </v-col>
      <v-col cols="12" md="6">
        <v-checkbox
          v-model="localSighting.melded"
          label="Gemeldet"
        ></v-checkbox>
      </v-col>
      <v-col cols="12">
        <v-textarea
          v-model="localSighting.comment"
          label="Kommentare"
        ></v-textarea>
      </v-col>
      <v-col cols="12">
        <leaflet-map
          v-model:latitude="localSighting.lat"
          v-model:longitude="localSighting.lon"
        ></leaflet-map>
      </v-col>
    </v-row>
    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn
        color="primary"
        type="submit"
        :loading="loading"
      >
        Speichern
      </v-btn>
    </v-card-actions>
  </v-form>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import type { Sighting } from '@/types';
import LeafletMap from '@/components/map/LeafletMap.vue';

const props = defineProps<{
  sighting: Partial<Sighting>;
  loading?: boolean;
}>();

const emit = defineEmits<{
  'submit': [sighting: Partial<Sighting>];
}>();

const localSighting = ref<Partial<Sighting>>({ ...props.sighting });

watch(() => props.sighting, (newSighting) => {
  localSighting.value = { ...newSighting };
}, { deep: true });

const saveSighting = () => {
  emit('submit', localSighting.value);
};
</script>