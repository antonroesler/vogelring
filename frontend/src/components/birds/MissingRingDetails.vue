<template>
  <v-card>
    <v-card-title class="d-flex align-center">
      Kein Ring zugeordnet
      <v-spacer></v-spacer>
      <v-progress-circular
        v-if="isLoading"
        indeterminate
        color="primary"
        size="24"
      ></v-progress-circular>
    </v-card-title>
    <v-card-text>
      <p class="text-body-1 mb-4">
        Für diese Sichtung wurde kein Ring bestimmt. Basierend auf der Ablesung "{{ reading }}" 
        wurden folgende mögliche Vögel gefunden:
      </p>

      <v-list v-if="sortedSuggestions.length > 0">
        <template v-for="(group, index) in sortedSuggestions" :key="index">
          <!-- Section header if we have multiple groups -->
          <v-list-subheader v-if="sortedSuggestions.length > 1">
            {{ group.header }}
          </v-list-subheader>

          <!-- Bird suggestions -->
          <v-list-item
            v-for="bird in group.birds"
            :key="bird.ring"
            :class="{'matching-species': bird.species === sightingSpecies}"
            density="compact"
          >
            <template v-slot:prepend>
              <v-btn
                color="primary"
                size="small"
                variant="tonal"
                :loading="isUpdating"
                @click="assignRing(bird)"
                density="compact"
              >
                Zuordnen
              </v-btn>
            </template>

            <v-list-item-title class="d-flex align-center">
              <span class="font-weight-medium font-monospace">{{ bird.ring }}</span>
              <span class="mx-1">-</span>
              <span>{{ bird.species }}</span>
            </v-list-item-title>
            <v-list-item-subtitle class="d-flex flex-wrap">
              <span class="me-2">
                {{ bird.sighting_count }} Sichtung{{ bird.sighting_count !== 1 ? 'en' : '' }}
              </span>
              <span class="text-no-wrap">
                <span class="text-medium-emphasis">Letzte:</span>
                {{ formatDate(bird.last_seen) }}
              </span>
            </v-list-item-subtitle>
          </v-list-item>
        </template>
      </v-list>

      <v-alert
        v-else-if="!isLoading"
        type="info"
        variant="tonal"
        class="mt-2"
      >
        Keine Vorschläge gefunden.
      </v-alert>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { format } from 'date-fns';
import type { BirdMeta, Sighting } from '@/types';
import * as api from '@/api';
import { useSightingsStore } from '@/stores/sightings';

const props = defineProps<{
  reading: string;
  sighting: Sighting;
}>();

const store = useSightingsStore();
const suggestions = ref<BirdMeta[]>([]);
const isLoading = ref(false);
const isUpdating = ref(false);

const sightingSpecies = computed(() => props.sighting.species);

// Sort suggestions into groups
const sortedSuggestions = computed(() => {
  if (!suggestions.value.length) return [];

  // Split birds into matching and non-matching species
  const matchingSpecies: BirdMeta[] = [];
  const otherSpecies: BirdMeta[] = [];

  suggestions.value.forEach(bird => {
    if (sightingSpecies.value && bird.species === sightingSpecies.value) {
      matchingSpecies.push(bird);
    } else {
      otherSpecies.push(bird);
    }
  });

  // Sort each group by last_seen date and sighting_count
  const sortBirds = (birds: BirdMeta[]) => {
    return birds.sort((a, b) => {
      // First by last_seen date
      const dateA = a.last_seen ? new Date(a.last_seen).getTime() : 0;
      const dateB = b.last_seen ? new Date(b.last_seen).getTime() : 0;
      if (dateB !== dateA) return dateB - dateA;
      
      // Then by sighting count
      return (b.sighting_count || 0) - (a.sighting_count || 0);
    });
  };

  const result = [];
  
  if (matchingSpecies.length > 0) {
    result.push({
      header: `Passende Art (${sightingSpecies.value})`,
      birds: sortBirds(matchingSpecies)
    });
  }
  
  if (otherSpecies.length > 0) {
    result.push({
      header: 'Andere Arten',
      birds: sortBirds(otherSpecies)
    });
  }

  return result;
});

const formatDate = (date: string | null) => {
  if (!date) return 'Unbekannt';
  return format(new Date(date), 'dd.MM.yyyy');
};

const assignRing = async (bird: BirdMeta) => {
  isUpdating.value = true;
  try {
    const updatedSighting: Partial<Sighting> = {
      ...props.sighting,
      ring: bird.ring,
      species: bird.species // Also update species if it was empty
    };
    await store.updateSighting(updatedSighting);
    // Emit success or trigger a reload of the parent component
    window.location.reload(); // Simple reload for now
  } catch (error) {
    console.error('Error updating sighting:', error);
  } finally {
    isUpdating.value = false;
  }
};

onMounted(async () => {
  if (props.reading) {
    isLoading.value = true;
    try {
      suggestions.value = await api.getBirdSuggestions(props.reading);
    } catch (error) {
      console.error('Error fetching suggestions:', error);
    } finally {
      isLoading.value = false;
    }
  }
});
</script>

<style scoped>
.matching-species {
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.v-list-item {
  margin-bottom: 4px;
  border-radius: 4px;
}

.text-no-wrap {
  white-space: nowrap;
}

.font-monospace {
  font-family: monospace;
}
</style> 