import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { Sighting } from '../types';
import * as api from '../api';

export const useSightingsStore = defineStore('sightings', () => {
  const sightings = ref<Sighting[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const fetchSightings = async (params?: {
    start_date?: string;
    end_date?: string;
    species?: string;
    place?: string;
  }) => {
    loading.value = true;
    error.value = null;
    
    try {
      console.log('Fetching all sightings with params:', params);
      const response = await api.getSightings({
        per_page: 10000,
        ...params
      });
      
      sightings.value = response;
      console.log('Successfully fetched sightings:', sightings.value);
    } catch (err) {
      console.error('Error fetching sightings:', err);
      error.value = err instanceof Error ? err.message : 'Failed to fetch sightings';
      sightings.value = [];
    } finally {
      loading.value = false;
    }
  };

  const createSighting = async (sighting: Partial<Sighting>) => {
    try {
      await api.createSighting(sighting);
      await fetchSightings();
    } catch (error) {
      console.error('Error creating sighting:', error);
      throw error;
    }
  };

  return {
    sightings,
    loading,
    error,
    fetchSightings,
    createSighting
  };
});