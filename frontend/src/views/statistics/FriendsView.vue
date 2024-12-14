<template>
  <v-card class="mt-4">
    <v-card-text>
      <v-row>
        <v-col cols="12" md="6">
          <v-row no-gutters>
            <v-col>
              <v-text-field
                v-model="searchQuery"
                label="Vogel suchen (Ring oder Ablesung)"
                hint="Nutze ... oder * als Platzhalter"
                persistent-hint
                clearable
                @keyup.enter="handleSearch"
              ></v-text-field>
            </v-col>
            <v-col cols="auto" class="ml-2">
              <v-btn
                color="primary"
                :disabled="searchQuery.length < 3"
                @click="handleSearch"
              >
                Suchen
              </v-btn>
            </v-col>
          </v-row>
        </v-col>
      </v-row>

      <v-row>
        <v-col cols="12">
          <v-list v-if="isLoadingSuggestions || suggestions.length > 0">
            <v-list-item v-if="isLoadingSuggestions">
              <template v-slot:prepend>
                <v-progress-circular
                  indeterminate
                  size="20"
                  width="2"
                  color="primary"
                ></v-progress-circular>
              </template>
              <v-list-item-title>
                Suche Vögel...
              </v-list-item-title>
            </v-list-item>
            <template v-if="!isLoadingSuggestions">
              <v-list-item
                v-for="bird in sortedSuggestions"
                :key="bird.ring"
                @click="selectBird(bird)"
              >
                <v-list-item-title>
                  {{ bird.ring }} - {{ bird.species }}
                </v-list-item-title>
                <v-list-item-subtitle>
                  {{ bird.sighting_count }} Sichtung{{ bird.sighting_count !== 1 ? 'en' : '' }} | Letzte Sichtung: {{ formatDate(bird.last_seen) }}
                </v-list-item-subtitle>
              </v-list-item>
            </template>
          </v-list>
        </v-col>
      </v-row>

      <v-row v-if="selectedBird">
        <v-overlay
          :model-value="isLoadingFriends"
          class="align-center justify-center"
          persistent
          location="center center"
        >
          <v-progress-circular
            indeterminate
            size="64"
            color="primary"
          ></v-progress-circular>
        </v-overlay>
        
        <v-col cols="12" md="4">
          <bird-details 
            :bird="selectedBird"
            :ringing-data="ringingData"
          ></bird-details>
        </v-col>

        <v-col cols="12" md="8">
          <v-card class="bird-details-card">
            <v-card-title>Freunde</v-card-title>
            <v-card-text class="friends-list-container">
              <v-list class="friends-list">
                <v-list-item
                  v-for="friend in friends"
                  :key="friend.ring"
                  @click="selectBird({ ...friend })"
                >
                  <template v-slot:prepend>
                    <div 
                      class="color-marker" 
                      :style="{ backgroundColor: friendColors[friend.ring] }"
                    ></div>
                  </template>
                  <v-list-item-title>
                    {{ friend.ring }} - {{ friend.species }}
                  </v-list-item-title>
                  <v-list-item-subtitle>
                    <v-container class="pa-0">
                      <v-row dense>
                        <v-col cols="12">
                          Gemeinsame Sichtungen: {{ friend.count }}
                        </v-col>
                        <v-col cols="12">
                          Orte: {{ friend.places.join(', ') }}
                        </v-col>
                      </v-row>
                    </v-container>
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12">
          <v-card>
            <v-card-title>Sichtungen Karte</v-card-title>
            <v-card-text>
              <friends-map
                :bird="selectedBird"
                :friends="friends"
                :friend-colors="friendColors"
              ></friends-map>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { format } from 'date-fns';
import type { BirdMeta, AnalyticsBirdMeta, Ringing } from '@/types';
import * as api from '@/api';
import BirdDetails from '@/components/birds/BirdDetails.vue';
import FriendsMap from '@/components/map/FriendsMap.vue';

const searchQuery = ref('');
const suggestions = ref<BirdMeta[]>([]);
const selectedBird = ref<BirdMeta | null>(null);
const friends = ref<AnalyticsBirdMeta[]>([]);
const isLoadingSuggestions = ref(false);
const isLoadingFriends = ref(false);
const ringingData = ref<Ringing | null>(null);

const friendColors = computed(() => {
  const colors = [
    '#FF4444', // bright red
    '#00BCD4', // cyan
    '#2196F3', // bright blue
    '#4CAF50', // bright green
    '#FFC107', // amber
    '#E91E63', // pink
    '#9C27B0', // bright purple
    '#3F51B5', // indigo
    '#FF5722', // deep orange
    '#009688', // teal
  ];
  
  return friends.value.reduce((acc, friend, index) => {
    acc[friend.ring] = colors[index % colors.length];
    return acc;
  }, {} as Record<string, string>);
});

const sortedSuggestions = computed(() => {
  return [...suggestions.value].sort((a, b) => b.sighting_count - a.sighting_count);
});

const handleSearch = async () => {
  if (searchQuery.value.length < 3) {
    return;
  }
  
  isLoadingSuggestions.value = true;
  try {
    suggestions.value = await api.getBirdSuggestions(searchQuery.value);
  } catch (error) {
    console.error('Error fetching suggestions:', error);
  } finally {
    isLoadingSuggestions.value = false;
  }
};

const loadRingingData = async (ring: string) => {
  try {
    ringingData.value = await api.getRingingByRing(ring);
  } catch (error) {
    console.error('Error loading ringing data:', error);
    ringingData.value = null;
  }
};

const selectBird = async (bird: BirdMeta) => {
  isLoadingFriends.value = true;
  try {
    const response = await api.getBirdFriends(bird.ring);
    selectedBird.value = response.bird;
    friends.value = response.friends;
    suggestions.value = [];
    searchQuery.value = '';
    
    if (response.bird.ring) {
      await loadRingingData(response.bird.ring);
    }
  } catch (error) {
    console.error('Error fetching bird friends:', error);
  } finally {
    isLoadingFriends.value = false;
  }
};

const formatDate = (date: string) => {
  return format(new Date(date), 'dd.MM.yyyy');
};
</script>

<style scoped>
.color-marker {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 1px solid rgba(0,0,0,0.2);
  display: inline-block;
  margin-right: 8px;
}

.bird-details-card {
  height: 450px;
}

.friends-list-container {
  height: calc(100% - 64px);
  padding: 0;
  max-height: calc(450px - 64px);
}

.friends-list {
  height: 100%;
  overflow-y: auto;
  padding: 16px;
}
</style> 