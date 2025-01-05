import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { Sighting } from '../types';
import * as api from '../api';

export const useSightingsStore = defineStore('sightings', {
  state: () => ({
    sightings: [] as Sighting[],
    loading: false,
    error: null as string | null,
    initialized: false,
  }),

  actions: {
    async updateSighting(sighting: Partial<Sighting>) {
      try {
        const response = await api.updateSighting(sighting);
        
        // Update the sighting in the local state
        const index = this.sightings.findIndex(s => s.id === sighting.id);
        if (index !== -1) {
          this.sightings[index] = { ...this.sightings[index], ...response };
        }
        
        return response;
      } catch (error) {
        console.error('Error updating sighting:', error);
        throw error;
      }
    },

    async fetchSightings(params?: {
      start_date?: string;
      end_date?: string;
      species?: string;
      place?: string;
    }) {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await api.getSightings({
          per_page: 10000,
          ...params
        });
        
        this.sightings = response;
        this.initialized = true;
      } catch (err) {
        console.error('Error fetching sightings:', err);
        this.error = err instanceof Error ? err.message : 'Failed to fetch sightings';
        this.sightings = [];
      } finally {
        this.loading = false;
      }
    },

    async createSighting(sighting: Partial<Sighting>) {
      try {
        const newSighting = await api.createSighting(sighting);
        this.sightings.push(newSighting);
        return newSighting;
      } catch (error) {
        console.error('Error creating sighting:', error);
        throw error;
      }
    },

    async deleteSighting(id: string) {
      try {
        await api.deleteSighting(id);
        this.sightings = this.sightings.filter(s => s.id !== id);
      } catch (error) {
        console.error('Error deleting sighting:', error);
        throw error;
      }
    }
  }
});