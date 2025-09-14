<template>
  <v-card class="mb-4" variant="outlined">
    <v-card-text>
      <v-row>
        <!-- Date Range -->
        <v-col cols="12" sm="6" md="3">
          <v-text-field
            v-model="localFilters.startDate"
            type="date"
            label="Von Datum"
            clearable
            variant="outlined"
            density="compact"
            @update:model-value="updateFilters"
          ></v-text-field>
        </v-col>
        
        <v-col cols="12" sm="6" md="3">
          <v-text-field
            v-model="localFilters.endDate"
            type="date"
            label="Bis Datum"
            clearable
            variant="outlined"
            density="compact"
            @update:model-value="updateFilters"
          ></v-text-field>
        </v-col>

        <!-- Species Filter -->
        <v-col cols="12" sm="6" md="3">
          <v-select
            v-model="localFilters.species"
            :items="speciesOptions"
            label="Spezies"
            clearable
            variant="outlined"
            density="compact"
            @update:model-value="updateFilters"
          ></v-select>
        </v-col>

        <!-- Place Filter -->
        <v-col cols="12" sm="6" md="3">
          <v-text-field
            v-model="localFilters.place"
            label="Ort"
            clearable
            variant="outlined"
            density="compact"
            @update:model-value="updateFilters"
          ></v-text-field>
        </v-col>

        <!-- Ring Filter -->
        <v-col cols="12" sm="6" md="3">
          <v-text-field
            v-model="localFilters.ring"
            label="Ring"
            clearable
            variant="outlined"
            density="compact"
            @update:model-value="updateFilters"
          ></v-text-field>
        </v-col>

        <!-- Ringer Filter -->
        <v-col cols="12" sm="6" md="3">
          <v-text-field
            v-model="localFilters.ringer"
            label="Beringer"
            clearable
            variant="outlined"
            density="compact"
            @update:model-value="updateFilters"
          ></v-text-field>
        </v-col>
      </v-row>

      <!-- Active Filters Display -->
      <div v-if="activeFilters.length > 0" class="mt-3">
        <v-chip-group>
          <v-chip
            v-for="filter in activeFilters"
            :key="filter.key"
            closable
            @click:close="removeFilter(filter.key)"
            color="primary"
            variant="outlined"
            size="small"
          >
            {{ filter.label }}
          </v-chip>
        </v-chip-group>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
// Using a simple debounce implementation instead of lodash-es
const debounce = <T extends (...args: any[]) => any>(func: T, wait: number): ((...args: Parameters<T>) => void) => {
  let timeout: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

interface Filters {
  startDate: string | null;
  endDate: string | null;
  species: string | null;
  place: string | null;
  ring: string | null;
  ringer: string | null;
}

const props = defineProps<{
  filters: Filters;
}>();

const emit = defineEmits<{
  'update:filters': [filters: Filters];
}>();

const localFilters = ref<Filters>({ ...props.filters });

// Species options for the dropdown
const speciesOptions = [
  { title: 'Kanadagans', value: '01660' },
  { title: 'Graugans', value: '01610' },
  { title: 'Höckerschwan', value: '01520' },
  { title: 'Nilgans', value: '01700' },
  { title: 'Weißwangengans', value: '01670' }
];

const activeFilters = computed(() => {
  const active = [];
  if (localFilters.value.startDate) {
    active.push({ 
      key: 'startDate', 
      value: localFilters.value.startDate, 
      label: `Von: ${localFilters.value.startDate}` 
    });
  }
  if (localFilters.value.endDate) {
    active.push({ 
      key: 'endDate', 
      value: localFilters.value.endDate, 
      label: `Bis: ${localFilters.value.endDate}` 
    });
  }
  if (localFilters.value.species) {
    const speciesOption = speciesOptions.find(opt => opt.value === localFilters.value.species);
    active.push({ 
      key: 'species', 
      value: localFilters.value.species, 
      label: `Spezies: ${speciesOption?.title || localFilters.value.species}` 
    });
  }
  if (localFilters.value.place) {
    active.push({ 
      key: 'place', 
      value: localFilters.value.place, 
      label: `Ort: ${localFilters.value.place}` 
    });
  }
  if (localFilters.value.ring) {
    active.push({ 
      key: 'ring', 
      value: localFilters.value.ring, 
      label: `Ring: ${localFilters.value.ring}` 
    });
  }
  if (localFilters.value.ringer) {
    active.push({ 
      key: 'ringer', 
      value: localFilters.value.ringer, 
      label: `Beringer: ${localFilters.value.ringer}` 
    });
  }
  return active;
});

// Debounced update function
const debouncedEmit = debounce((filters: Filters) => {
  emit('update:filters', filters);
}, 500);

const updateFilters = () => {
  debouncedEmit({ ...localFilters.value });
};

const removeFilter = (key: string) => {
  if (key in localFilters.value) {
    (localFilters.value as any)[key] = null;
    updateFilters();
  }
};

// Watch for external filter changes
watch(() => props.filters, (newFilters) => {
  localFilters.value = { ...newFilters };
}, { deep: true });
</script>

<style scoped>
/* Add any custom styles if needed */
</style>
