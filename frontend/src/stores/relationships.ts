import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { getAllRelationships, deleteRelationship as apiDeleteRelationship } from '@/api';

export interface Relationship {
  id: string;
  bird1_ring: string;
  bird2_ring: string;
  relationship_type: 'breeding_partner' | 'parent_of' | 'child_of' | 'sibling_of';
  year: number | null;
  confidence: number | null;
  source: string | null;
  notes: string | null;
  sighting1_id: string | null;
  sighting2_id: string | null;
  ringing1_id: string | null;
  ringing2_id: string | null;
  created_at: string;
  updated_at: string;
}

export const useRelationshipsStore = defineStore('relationships', () => {
  const relationships = ref<Relationship[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const initialized = ref(false);

  // Filters
  const filters = ref({
    relationship_type: null as Relationship['relationship_type'] | null,
    year: null as number | null,
    bird_ring: null as string | null,
  });

  const activeFilters = computed(() => {
    const active = [];
    if (filters.value.relationship_type) {
      const labels: Record<string, string> = {
        breeding_partner: 'Brutpartner',
        parent_of: 'Elternteil von',
        child_of: 'Kind von',
        sibling_of: 'Geschwister von',
      };
      active.push({ key: 'relationship_type', value: filters.value.relationship_type, label: labels[filters.value.relationship_type] });
    }
    if (filters.value.year) active.push({ key: 'year', value: filters.value.year, label: `Jahr: ${filters.value.year}` });
    if (filters.value.bird_ring) active.push({ key: 'bird_ring', value: filters.value.bird_ring, label: `Ring: ${filters.value.bird_ring}` });
    return active;
  });

  const setFilters = (newFilters: Partial<typeof filters.value>) => {
    filters.value = { ...filters.value, ...newFilters };
  };

  const clearFilters = () => {
    filters.value = {
      relationship_type: null,
      year: null,
      bird_ring: null,
    };
  };

  const loadRelationships = async () => {
    loading.value = true;
    error.value = null;

    try {
      const params: Record<string, string | number> = {};

      if (filters.value.relationship_type) params.relationship_type = filters.value.relationship_type;
      if (filters.value.year) params.year = filters.value.year;
      if (filters.value.bird_ring) params.bird_ring = filters.value.bird_ring;

      relationships.value = await getAllRelationships(Object.keys(params).length > 0 ? params as any : undefined);
      initialized.value = true;
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load relationships';
      console.error('Error loading relationships:', err);
    } finally {
      loading.value = false;
    }
  };

  const deleteRelationship = async (id: string) => {
    try {
      await apiDeleteRelationship(id);
      relationships.value = relationships.value.filter(r => r.id !== id);
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to delete relationship';
      console.error('Error deleting relationship:', err);
      throw err;
    }
  };

  return {
    relationships,
    loading,
    error,
    initialized,
    filters,
    activeFilters,
    setFilters,
    clearFilters,
    loadRelationships,
    deleteRelationship,
  };
});
