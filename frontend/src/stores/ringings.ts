import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Ringing } from '@/types';
import { getRingings, deleteRinging } from '@/api';

export const useRingingStore = defineStore('ringings', () => {
  const ringings = ref<Ringing[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // Pagination
  const pagination = ref({
    page: 1,
    itemsPerPage: 25,
    total: 0
  });

  // Filters
  const filters = ref({
    startDate: null as string | null,
    endDate: null as string | null,
    species: null as string | null,
    place: null as string | null,
    ring: null as string | null,
    ringer: null as string | null
  });

  const activeFilters = computed(() => {
    const active = [];
    if (filters.value.startDate) active.push({ key: 'startDate', value: filters.value.startDate, label: `Start: ${filters.value.startDate}` });
    if (filters.value.endDate) active.push({ key: 'endDate', value: filters.value.endDate, label: `Ende: ${filters.value.endDate}` });
    if (filters.value.species) active.push({ key: 'species', value: filters.value.species, label: `Spezies: ${filters.value.species}` });
    if (filters.value.place) active.push({ key: 'place', value: filters.value.place, label: `Ort: ${filters.value.place}` });
    if (filters.value.ring) active.push({ key: 'ring', value: filters.value.ring, label: `Ring: ${filters.value.ring}` });
    if (filters.value.ringer) active.push({ key: 'ringer', value: filters.value.ringer, label: `Beringer: ${filters.value.ringer}` });
    return active;
  });

  const setPagination = (newPagination: Partial<typeof pagination.value>) => {
    pagination.value = { ...pagination.value, ...newPagination };
  };

  const setFilters = (newFilters: Partial<typeof filters.value>) => {
    filters.value = { ...filters.value, ...newFilters };
    // Reset to first page when filters change
    pagination.value.page = 1;
  };

  const clearFilters = () => {
    filters.value = {
      startDate: null,
      endDate: null,
      species: null,
      place: null,
      ring: null,
      ringer: null
    };
    pagination.value.page = 1;
  };

  const loadRingings = async () => {
    loading.value = true;
    error.value = null;

    try {
      const params: Record<string, string> = {};

      if (filters.value.startDate) params.start_date = filters.value.startDate;
      if (filters.value.endDate) params.end_date = filters.value.endDate;
      if (filters.value.species) params.species = filters.value.species;
      if (filters.value.place) params.place = filters.value.place;
      if (filters.value.ring) params.ring = filters.value.ring;
      if (filters.value.ringer) params.ringer = filters.value.ringer;

      ringings.value = await getRingings(Object.keys(params).length > 0 ? params : undefined);
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load ringings';
      console.error('Error loading ringings:', err);
    } finally {
      loading.value = false;
    }
  };

  const refreshRingings = () => {
    return loadRingings();
  };

  const deleteRingingByRing = async (ring: string) => {
    try {
      await deleteRinging(ring);
      // Remove from local state
      ringings.value = ringings.value.filter(r => r.ring !== ring);
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to delete ringing';
      console.error('Error deleting ringing:', err);
      throw err;
    }
  };

  return {
    ringings,
    loading,
    error,
    pagination,
    filters,
    activeFilters,
    setPagination,
    setFilters,
    clearFilters,
    loadRingings,
    refreshRingings,
    deleteRingingByRing
  };
});
