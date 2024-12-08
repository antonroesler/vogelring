<template>
  <div>
    <h1 class="text-h4 mb-4">Eintragliste</h1>
    
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
      :sightings="store.sightings"
      :loading="store.loading"
      @deleted="handleSightingDeleted"
    ></sightings-table>

    <v-snackbar
      v-model="showDeleteSnackbar"
      color="success"
    >
      Sichtung erfolgreich gelöscht
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useSightingsStore } from '@/stores/sightings';
import SightingsFilter from '@/components/sightings/SightingsFilter.vue';
import SightingsTable from '@/components/sightings/SightingsTable.vue';

const store = useSightingsStore();
const showDeleteSnackbar = ref(false);
const filters = ref({
  start_date: undefined,
  end_date: undefined,
  species: undefined,
  place: undefined
});

const loadSightings = async () => {
  console.log('Loading sightings...');
  await store.fetchSightings({
    ...filters.value
  });
};

const handleSightingDeleted = () => {
  showDeleteSnackbar.value = true;
  loadSightings();
};

const retryLoading = () => {
  store.error = null;
  loadSightings();
};

// Watch for changes in filters
watch(filters, () => {
  loadSightings();
}, { deep: true });

onMounted(() => {
  console.log('EntryList component mounted');
  loadSightings();
});
</script>