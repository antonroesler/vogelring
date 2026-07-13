<template>
  <div>
    <div class="d-flex align-center mb-4">
      <v-btn
        v-if="$route.query.from === 'detail'"
        icon="mdi-arrow-left"
        variant="text"
        @click="handleBack"
        class="me-2"
      ></v-btn>
      <h1 class="text-h4 flex-grow-1">Eintragliste</h1>
      <v-btn
        v-if="store.activeFilters.length > 0"
        variant="text"
        @click="clearAllFilters"
        class="me-2"
      >
        Filter zurücksetzen
      </v-btn>
      <v-btn
        prepend-icon="mdi-microsoft-excel"
        variant="tonal"
        color="green-darken-2"
        @click="exportDialog = true"
        class="me-2"
      >
        Wiederfunde-Export
        <v-tooltip activator="parent" location="bottom">
          Excel-Export der nicht gemeldeten Wiederfunde für die Vogelwarte (RING)
        </v-tooltip>
      </v-btn>
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
      :use-store-pagination="true"
      settings-key="entry-list"
      :show-settings="true"
      :default-columns="['date','ring','species','place','pair','status','melder','melded']"
      :default-hover-expand="true"
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

    <v-dialog v-model="exportDialog" max-width="440">
      <v-card>
        <v-card-title>Wiederfunde-Export (RING)</v-card-title>
        <v-card-text>
          <p class="text-body-2 mb-4">
            Exportiert alle <strong>nicht gemeldeten</strong> Wiederfunde im
            gewählten Zeitraum als Excel-Datei für die Vogelwarte.
          </p>
          <v-text-field
            v-model="exportStartDate"
            label="Von (Datum)"
            type="date"
            variant="outlined"
            density="comfortable"
          ></v-text-field>
          <v-text-field
            v-model="exportEndDate"
            label="Bis (optional)"
            type="date"
            variant="outlined"
            density="comfortable"
            hint="Leer lassen = keine Obergrenze"
            persistent-hint
          ></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="exportDialog = false">Abbrechen</v-btn>
          <v-btn
            color="green-darken-2"
            variant="flat"
            :loading="exporting"
            :disabled="!exportStartDate"
            @click="handleExport"
          >
            Exportieren
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useSightingsStore } from '@/stores/sightings';
import SightingsFilter from '@/components/sightings/SightingsFilter.vue';
import SightingsTable from '@/components/sightings/SightingsTable.vue';
import type { Sighting } from '@/types';
import { useRouter } from 'vue-router';
import { exportSightingsVogelwarte } from '@/api';

const store = useSightingsStore();
const router = useRouter();
const showDeleteSnackbar = ref(false);
const showMeldedSnackbar = ref(false);
const meldedSnackbarText = ref('');
const exporting = ref(false);
const exportDialog = ref(false);
const exportStartDate = ref('2026-01-01');
const exportEndDate = ref('');

const handleExport = async () => {
  exporting.value = true;
  try {
    const params: { start_date?: string; end_date?: string } = {};
    if (exportStartDate.value) params.start_date = exportStartDate.value;
    if (exportEndDate.value) params.end_date = exportEndDate.value;
    await exportSightingsVogelwarte(params);
    exportDialog.value = false;
  } catch (error) {
    console.error('Error exporting Wiederfunde:', error);
    store.error = 'Export fehlgeschlagen. Bitte erneut versuchen.';
  } finally {
    exporting.value = false;
  }
};

const filters = computed({
  get: () => store.filters,
  set: (newFilters) => store.setFilters(newFilters, activeFilters.value)
});

const activeFilters = computed({
  get: () => store.activeFilters,
  set: (newActiveFilters) => store.setFilters(filters.value, newActiveFilters)
});

const filteredSightings = computed(() => {
  return store.sightings.filter(sighting => {
    let matches = true;
    
    if (filters.value.species) {
      matches = matches && !!(sighting.species && sighting.species.toLowerCase().includes(filters.value.species.toLowerCase()));
    }
    if (filters.value.ring) {
      matches = matches && !!(sighting.ring && sighting.ring.includes(filters.value.ring));
    }
    if (filters.value.place) {
      matches = matches && !!(sighting.place && sighting.place.toLowerCase().includes(filters.value.place.toLowerCase()));
    }
    if (filters.value.melder) {
      matches = matches && !!(sighting.melder && sighting.melder.toLowerCase().includes(filters.value.melder.toLowerCase()));
    }
    if (filters.value.start_date) {
      matches = matches && !!sighting.date && sighting.date >= filters.value.start_date;
    }
    if (filters.value.end_date) {
      matches = matches && !!sighting.date && sighting.date <= filters.value.end_date;
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

const handleBack = () => {
  router.back();
};

const clearAllFilters = () => {
  store.clearState();
};

// Watch for route changes
watch(
  () => router.currentRoute.value.query.from,
  (newFrom) => {
    // Only clear everything if we're not coming from a detail view
    if (!newFrom) {
      store.clearState(); // This will clear filters and reset pagination
    }
  },
  { immediate: true }
);

// Add this watch to handle pagination restoration
watch(
  () => router.currentRoute.value.query,
  (query) => {
    if (query.from === 'detail' && query.page) {
      store.setPagination({
        page: parseInt(query.page as string),
        itemsPerPage: parseInt(query.perPage as string) || 10
      });
    }
  },
  { immediate: true }
);

onMounted(async () => {
  if (!store.initialized) {
    await loadSightings();
  }
});
</script>