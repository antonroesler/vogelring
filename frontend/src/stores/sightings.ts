import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { Sighting } from '../types';
import * as api from '../api';

export const useSightingsStore = defineStore('sightings', () => {
  const sightings = ref<Sighting[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const initialized = ref(false);

  const fetchSightings = async (params?: {
    start_date?: string;
    end_date?: string;
    species?: string;
    place?: string;
  }) => {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await api.getSightings({
        per_page: 10000,
        ...params
      });
      
      sightings.value = response;
      initialized.value = true;
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
      const newSighting = await api.createSighting(sighting);
      sightings.value.push(newSighting);
      return newSighting;
    } catch (error) {
      console.error('Error creating sighting:', error);
      throw error;
    }
  };

  const updateSighting = async (sighting: Partial<Sighting>) => {
    try {
      const updatedSighting = await api.updateSighting(sighting);
      const index = sightings.value.findIndex(s => s.id === updatedSighting.id);
      if (index !== -1) {
        sightings.value[index] = updatedSighting;
      }
      return updatedSighting;
    } catch (error) {
      console.error('Error updating sighting:', error);
      throw error;
    }
  };

  const deleteSighting = async (id: string) => {
    try {
      await api.deleteSighting(id);
      sightings.value = sightings.value.filter(s => s.id !== id);
    } catch (error) {
      console.error('Error deleting sighting:', error);
      throw error;
    }
  };

  return {
    sightings,
    loading,
    error,
    initialized,
    fetchSightings,
    createSighting,
    updateSighting,
    deleteSighting
  };
});