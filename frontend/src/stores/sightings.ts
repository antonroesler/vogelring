import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { Sighting, BirdStatus, BirdAge } from '../types';
import * as api from '../api';

interface Filters {
  start_date?: string;
  end_date?: string;
  species?: string;
  place?: string;
  ring?: string;
  melder?: string;
  melded?: boolean;
  status?: BirdStatus;
  age?: BirdAge;
  month_start?: number;
  month_end?: number;
}

interface PaginationState {
  page: number;
  itemsPerPage: number;
}

export const useSightingsStore = defineStore('sightings', {
  state: () => ({
    sightings: [] as Sighting[],
    loading: false,
    error: null as string | null,
    initialized: false,
    filters: {} as Filters,
    activeFilters: [] as string[],
    pagination: {
      page: 1,
      itemsPerPage: 10
    } as PaginationState,
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
        this.sightings.unshift(newSighting);
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
    },

    setFilters(filters: Filters, activeFilters: string[]) {
      this.filters = filters;
      this.activeFilters = activeFilters;
    },

    clearFilters() {
      this.filters = {};
      this.activeFilters = [];
    },

    setPagination(pagination: Partial<PaginationState>) {
      this.pagination = {
        ...this.pagination,
        ...pagination
      };
    },

    clearState() {
      this.filters = {};
      this.activeFilters = [];
      this.pagination = {
        page: 1,
        itemsPerPage: 10
      };
    }
  }
});