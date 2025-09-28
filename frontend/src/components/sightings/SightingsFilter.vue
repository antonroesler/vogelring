<template>
  <v-card class="mb-6">
    <v-card-title class="bg-primary text-white px-6 py-4 d-flex align-center">
      Filter
      <v-spacer></v-spacer>
      <v-menu>
        <template v-slot:activator="{ props }">
          <v-btn
            color="white"
            variant="text"
            v-bind="props"
            prepend-icon="mdi-plus"
          >
            Filter hinzufügen
          </v-btn>
        </template>
        <v-list>
          <v-list-item
            v-for="filter in availableFilters"
            :key="filter.id"
            :disabled="activeFilters.includes(filter.id)"
            @click="addFilter(filter.id)"
          >
            <v-list-item-title>
              <v-icon start>{{ filter.icon }}</v-icon>
              {{ filter.title }}
            </v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </v-card-title>

    <v-card-text class="px-6 py-4">
      <v-row v-if="activeFilters.length > 0">
        <v-col 
          v-for="filterId in activeFilters" 
          :key="filterId"
          cols="12" 
          md="6" 
          lg="4"
          class="filter-item"
        >
          <v-card variant="outlined" class="pa-2">
            <div class="d-flex align-center mb-2">
              <v-icon :icon="getFilterById(filterId).icon" class="me-2"></v-icon>
              <span class="text-subtitle-2">{{ getFilterById(filterId).title }}</span>
              <v-spacer></v-spacer>
              <v-btn
                density="compact"
                icon="mdi-close"
                variant="text"
                size="small"
                @click="removeFilter(filterId)"
              ></v-btn>
            </div>

            <!-- Date Range Filter -->
            <template v-if="filterId === 'dateRange'">
              <v-row dense>
                <v-col cols="6">
                  <v-text-field
                    type="date"
                    v-model="filters.start_date"
                    label="Von"
                    density="compact"
                    variant="outlined"
                    @update:model-value="emitFilters"
                  ></v-text-field>
                </v-col>
                <v-col cols="6">
                  <v-text-field
                    type="date"
                    v-model="filters.end_date"
                    label="Bis"
                    density="compact"
                    variant="outlined"
                    @update:model-value="emitFilters"
                  ></v-text-field>
                </v-col>
              </v-row>
            </template>

            <!-- Month Range Filter -->
            <template v-if="filterId === 'monthRange'">
              <v-row dense>
                <v-col cols="6">
                  <v-select
                    v-model="filters.month_start"
                    label="Von"
                    :items="monthOptions"
                    density="compact"
                    variant="outlined"
                    @update:model-value="emitFilters"
                  ></v-select>
                </v-col>
                <v-col cols="6">
                  <v-select
                    v-model="filters.month_end"
                    label="Bis"
                    :items="monthOptions"
                    density="compact"
                    variant="outlined"
                    @update:model-value="emitFilters"
                  ></v-select>
                </v-col>
              </v-row>
            </template>

            <!-- Text Filters -->
            <template v-if="['species', 'ring', 'place', 'melder'].includes(filterId)">
              <v-text-field
                v-model="filters[filterId]"
                :label="getFilterById(filterId).title"
                density="compact"
                variant="outlined"
                @update:model-value="emitFilters"
              ></v-text-field>
            </template>

            <!-- Status Filter -->
            <template v-if="filterId === 'status'">
              <v-select
                v-model="filters.status"
                :items="[
                  { title: 'Brutvogel', value: 'BV' },
                  { title: 'Mausergast', value: 'MG' },
                  { title: 'Nichtbrüter', value: 'NB' },
                  { title: 'Reviervogel', value: 'RV' },
                  { title: 'Totfund', value: 'TF' }
                ]"
                density="compact"
                variant="outlined"
                @update:model-value="emitFilters"
              ></v-select>
            </template>

            <!-- Melded Filter -->
            <template v-if="filterId === 'melded'">
              <v-select
                v-model="filters.melded"
                :items="[
                  { title: 'Ja', value: true },
                  { title: 'Nein', value: false }
                ]"
                density="compact"
                variant="outlined"
                @update:model-value="emitFilters"
              ></v-select>
            </template>
          </v-card>
        </v-col>
      </v-row>
      
      <div v-else class="text-center py-8 text-medium-emphasis">
        Keine Filter ausgewählt
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import type { BirdStatus } from '@/types';
import { useSightingsStore } from '@/stores/sightings';

const store = useSightingsStore();

const emit = defineEmits<{
  'update:filters': [filters: Filters];
}>();

// Use computed properties to sync with store
const filters = computed({
  get: () => store.filters,
  set: (newFilters) => {
    store.setFilters(newFilters, activeFilters.value);
    emit('update:filters', newFilters);
  }
});

const activeFilters = computed({
  get: () => store.activeFilters,
  set: (newActiveFilters) => store.setFilters(filters.value, newActiveFilters)
});

const availableFilters = [
  { id: 'dateRange', title: 'Datumsbereich', icon: 'mdi-calendar-range' },
  { id: 'monthRange', title: 'Monatsbereich', icon: 'mdi-calendar-month' },
  { id: 'species', title: 'Spezies', icon: 'mdi-bird' },
  { id: 'ring', title: 'Ring', icon: 'mdi-ring' },
  { id: 'place', title: 'Ort', icon: 'mdi-map-marker' },
  { id: 'melder', title: 'Melder', icon: 'mdi-account' },
  { id: 'status', title: 'Status', icon: 'mdi-flag' },
  { id: 'melded', title: 'Gemeldet', icon: 'mdi-check-circle' },
];

const monthOptions = [
  { title: 'Januar', value: 1 },
  { title: 'Februar', value: 2 },
  { title: 'März', value: 3 },
  { title: 'April', value: 4 },
  { title: 'Mai', value: 5 },
  { title: 'Juni', value: 6 },
  { title: 'Juli', value: 7 },
  { title: 'August', value: 8 },
  { title: 'September', value: 9 },
  { title: 'Oktober', value: 10 },
  { title: 'November', value: 11 },
  { title: 'Dezember', value: 12 }
];

const getFilterById = (id: string) => {
  return availableFilters.find(f => f.id === id) || availableFilters[0];
};

const addFilter = (filterId: string) => {
  if (!activeFilters.value.includes(filterId)) {
    activeFilters.value = [...activeFilters.value, filterId];
  }
};

const removeFilter = (filterId: string) => {
  activeFilters.value = activeFilters.value.filter(id => id !== filterId);
  
  // Clear the corresponding filter values
  const newFilters = { ...filters.value };
  if (filterId === 'dateRange') {
    newFilters.start_date = undefined;
    newFilters.end_date = undefined;
  } else if (filterId === 'monthRange') {
    newFilters.month_start = undefined;
    newFilters.month_end = undefined;
  } else {
    newFilters[filterId as keyof Filters] = undefined;
  }
  
  filters.value = newFilters;
};

const emitFilters = () => {
  emit('update:filters', filters.value);
};
</script>

<style scoped>
.filter-item .v-card {
  border: 1px solid #DED5CA !important;
}
</style>