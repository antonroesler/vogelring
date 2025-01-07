<template>
  <div>
    <div class="d-flex align-center mb-4">
      <h1 class="text-h4 flex-grow-1">Eintragliste</h1>
      <v-btn
        icon="mdi-refresh"
        @click="loadSightings"
        :loading="store.loading"
        variant="text"
      ></v-btn>
    </div>
    
    <v-alert
      v-if="store.error"
      type="error"
      class="mb-4"
      closable
    >
      {{ store.error }}
      <template v-slot:append>
        <v-btn
          color="error"
          variant="text"
          @click="retryLoading"
        >
          Retry
        </v-btn>
      </template>
    </v-alert>

    <sightings-filter
      v-model:filters="filters"
    ></sightings-filter>

    <sightings-table
      :sightings="filteredSightings"
      :loading="store.loading"
      @deleted="handleSightingDeleted"
      @melded-updated="handleMeldedUpdated"
    ></sightings-table>

    <v-snackbar
      v-model="showMeldedSnackbar"
      color="success"
      :timeout="3000"
    >
      {{ meldedSnackbarText }}
    </v-snackbar>

    <v-snackbar
      v-model="showDeleteSnackbar"
      color="success"
    >
      Sichtung erfolgreich gelöscht
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useSightingsStore } from '@/stores/sightings';
import SightingsFilter from '@/components/sightings/SightingsFilter.vue';
import SightingsTable from '@/components/sightings/SightingsTable.vue';
import type { Sighting, BirdStatus, BirdAge } from '@/types';

const store = useSightingsStore();
const showDeleteSnackbar = ref(false);
const showMeldedSnackbar = ref(false);
const meldedSnackbarText = ref('');
const filters = ref({
  start_date: undefined as string | undefined,
  end_date: undefined as string | undefined,
  species: undefined as string | undefined,
  place: undefined as string | undefined,
  ring: undefined as string | undefined,
  melder: undefined as string | undefined,
  melded: undefined as boolean | undefined,
  status: undefined as BirdStatus | undefined,
  age: undefined as BirdAge | undefined,
  month_start: undefined as number | undefined,
  month_end: undefined as number | undefined,
});

const filteredSightings = computed(() => {
  return store.sightings.filter(sighting => {
    let matches = true;
    
    if (filters.value.species) {
      matches = matches && sighting.species?.toLowerCase().includes(filters.value.species.toLowerCase());
    }
    if (filters.value.ring) {
      matches = matches && sighting.ring?.includes(filters.value.ring);
    }
    if (filters.value.place) {
      matches = matches && sighting.place?.toLowerCase().includes(filters.value.place.toLowerCase());
    }
    if (filters.value.melder) {
      matches = matches && sighting.melder?.toLowerCase().includes(filters.value.melder.toLowerCase());
    }
    if (filters.value.start_date) {
      matches = matches && sighting.date >= filters.value.start_date;
    }
    if (filters.value.end_date) {
      matches = matches && sighting.date <= filters.value.end_date;
    }
    if (filters.value.melded !== undefined) {
      matches = matches && sighting.melded === filters.value.melded;
    }
    if (filters.value.status) {
      matches = matches && sighting.status === filters.value.status;
    }
    
    if (filters.value.age) {
      matches = matches && sighting.age === filters.value.age;
    }
    
    if (filters.value.month_start || filters.value.month_end) {
      const sightingDate = new Date(sighting.date || '');
      const sightingMonth = sightingDate.getMonth() + 1;
      
      if (filters.value.month_start && filters.value.month_end) {
        if (filters.value.month_start <= filters.value.month_end) {
          matches = matches && 
            sightingMonth >= filters.value.month_start && 
            sightingMonth <= filters.value.month_end;
        } else {
          matches = matches && 
            (sightingMonth >= filters.value.month_start || 
             sightingMonth <= filters.value.month_end);
        }
      } else if (filters.value.month_start) {
        matches = matches && sightingMonth >= filters.value.month_start;
      } else if (filters.value.month_end) {
        matches = matches && sightingMonth <= filters.value.month_end;
      }
    }
    
    return matches;
  });
});

const loadSightings = async () => {
  await store.fetchSightings();
};

const handleSightingDeleted = async (id: string) => {
  try {
    await store.deleteSighting(id);
    showDeleteSnackbar.value = true;
  } catch (error) {
    console.error('Error deleting sighting:', error);
  }
};

const retryLoading = () => {
  store.error = null;
  loadSightings();
};

const handleMeldedUpdated = (sighting: Sighting) => {
  showMeldedSnackbar.value = true;
  meldedSnackbarText.value = sighting.melded 
    ? 'Sichtung als gemeldet markiert'
    : 'Sichtung als nicht gemeldet markiert';
};

onMounted(async () => {
  if (!store.initialized) {
    await loadSightings();
  }
});
</script>