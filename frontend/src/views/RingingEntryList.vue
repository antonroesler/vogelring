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
      <h1 class="text-h4 flex-grow-1">Beringungs-Eintragliste</h1>
      <v-btn
        v-if="store.activeFilters.length > 0"
        variant="text"
        @click="clearAllFilters"
        class="me-2"
      >
        Filter zurücksetzen
      </v-btn>
      <v-btn
        icon="mdi-refresh"
        @click="loadRingings"
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
          Erneut versuchen
        </v-btn>
      </template>
    </v-alert>

    <ringing-filter
      v-model:filters="filters"
    ></ringing-filter>

    <ringing-table
      :ringings="filteredRingings"
      :loading="store.loading"
      :use-store-pagination="true"
      settings-key="ringing-entry-list"
      :show-settings="true"
      :default-columns="['date','ring','species','place','ringer','sex','age']"
      :default-hover-expand="true"
      @row-clicked="handleRingingClicked"
      @deleted="handleRingingDeleted"
    ></ringing-table>

    <v-snackbar
      v-model="showSnackbar"
      :color="snackbarColor"
      :timeout="3000"
    >
      {{ snackbarText }}
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useRingingStore } from '@/stores/ringings';
import RingingFilter from '@/components/ringings/RingingFilter.vue';
import RingingTable from '@/components/ringings/RingingTable.vue';
import type { Ringing } from '@/types';

const router = useRouter();
const store = useRingingStore();

const showSnackbar = ref(false);
const snackbarText = ref('');
const snackbarColor = ref('info');

const filters = computed({
  get: () => store.filters,
  set: (value) => store.setFilters(value)
});

const filteredRingings = computed(() => {
  return store.ringings;
});

const loadRingings = async () => {
  try {
    await store.loadRingings();
  } catch (error) {
    console.error('Error loading ringings:', error);
  }
};

const retryLoading = () => {
  loadRingings();
};

const clearAllFilters = () => {
  store.clearFilters();
  loadRingings();
};

const handleBack = () => {
  router.go(-1);
};

const handleRingingClicked = (ringing: Ringing) => {
  // Navigate to the bird detail page for this ring
  router.push(`/birds/${ringing.ring}`);
};

const handleRingingDeleted = async (ring: string) => {
  try {
    await store.deleteRingingByRing(ring);
    showSnackbar.value = true;
    snackbarText.value = `Beringung ${ring} erfolgreich gelöscht`;
    snackbarColor.value = 'success';
  } catch (error) {
    console.error('Error deleting ringing:', error);
    showSnackbar.value = true;
    snackbarText.value = `Fehler beim Löschen der Beringung ${ring}`;
    snackbarColor.value = 'error';
  }
};

// Watch filters and reload data
watch(filters, () => {
  loadRingings();
}, { deep: true });

onMounted(() => {
  loadRingings();
});
</script>

<style scoped>
/* Add any custom styles if needed */
</style>
