<template>
  <v-card class="mb-6">
    <v-card-title class="bg-primary text-white px-6 py-4">
      Filter
    </v-card-title>
    <v-card-text class="px-6 py-4">
      <v-row>
        <v-col cols="12" md="6" lg="3">
          <v-text-field
            v-model="filters.species"
            label="Spezies"
            clearable
            prepend-icon="mdi-bird"
            @update:model-value="emitFilters"
          ></v-text-field>
        </v-col>
        <v-col cols="12" md="6" lg="3">
          <v-text-field
            v-model="filters.ring"
            label="Ring"
            clearable
            prepend-icon="mdi-ring"
            @update:model-value="emitFilters"
          ></v-text-field>
        </v-col>
        <v-col cols="12" md="6" lg="3">
          <v-text-field
            v-model="filters.place"
            label="Ort"
            clearable
            prepend-icon="mdi-map-marker"
            @update:model-value="emitFilters"
          ></v-text-field>
        </v-col>
        <v-col cols="12" md="6" lg="3">
          <v-text-field
            v-model="filters.melder"
            label="Melder"
            clearable
            prepend-icon="mdi-account"
            @update:model-value="emitFilters"
          ></v-text-field>
        </v-col>
        <v-col cols="12" md="6" lg="3">
          <v-text-field
            type="date"
            v-model="filters.start_date"
            label="Von"
            clearable
            prepend-icon="mdi-calendar-start"
            @update:model-value="emitFilters"
          ></v-text-field>
        </v-col>
        <v-col cols="12" md="6" lg="3">
          <v-text-field
            type="date"
            v-model="filters.end_date"
            label="Bis"
            clearable
            prepend-icon="mdi-calendar-end"
            @update:model-value="emitFilters"
          ></v-text-field>
        </v-col>
        <v-col cols="12" md="6" lg="3">
          <v-select
            v-model="filters.melded"
            label="Gemeldet"
            prepend-icon="mdi-check-circle"
            :items="[
              { title: 'Alle', value: undefined },
              { title: 'Ja', value: true },
              { title: 'Nein', value: false }
            ]"
            clearable
            @update:model-value="emitFilters"
          ></v-select>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref } from 'vue';

interface Filters {
  species?: string;
  ring?: string;
  place?: string;
  melder?: string;
  start_date?: string;
  end_date?: string;
  melded?: boolean;
}

const emit = defineEmits<{
  'update:filters': [filters: Filters];
}>();

const filters = ref<Filters>({});

const emitFilters = () => {
  emit('update:filters', filters.value);
};
</script>