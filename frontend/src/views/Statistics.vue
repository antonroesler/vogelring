<template>
  <div>
    <h1 class="text-h4 mb-4">Statistiken</h1>

    <v-tabs v-model="activeTab">
      <v-tab value="friends">Freunde</v-tab>
    </v-tabs>

    <v-window v-model="activeTab">
      <v-window-item value="friends">
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
                <bird-details :bird="selectedBird"></bird-details>
              </v-col>

              <v-col cols="12" md="8">
                <v-card>
                  <v-card-title>Freunde</v-card-title>
                  <v-card-text>
                    <v-list>
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
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { format } from 'date-fns';
import type { BirdMeta, AnalyticsBirdMeta } from '@/types';
import * as api from '@/api';
import BirdDetails from '@/components/birds/BirdDetails.vue';
import FriendsMap from '@/components/map/FriendsMap.vue';
import { type Ref } from 'vue';

const activeTab = ref('friends');
const searchQuery = ref('');
const suggestions = ref<BirdMeta[]>([]);
const selectedBird = ref<BirdMeta | null>(null);
const friends = ref<AnalyticsBirdMeta[]>([]);

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

const isLoadingSuggestions = ref(false);
const isLoadingFriends = ref(false);

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

const selectBird = async (bird: BirdMeta) => {
  isLoadingFriends.value = true;
  try {
    const response = await api.getBirdFriends(bird.ring);
    selectedBird.value = response.bird;
    friends.value = response.friends;
    suggestions.value = [];
    searchQuery.value = '';
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
.friend-details {
  white-space: normal !important;
  overflow: visible !important;
}

.places-list {
  margin-top: 4px;
  word-wrap: break-word;
}

.color-marker {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 8px;
}
</style>