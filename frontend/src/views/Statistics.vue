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
                <v-text-field
                  v-model="searchQuery"
                  label="Vogel suchen (Ring oder Ablesung)"
                  hint="Nutze ... oder * als Platzhalter"
                  persistent-hint
                  clearable
                  @update:model-value="handleSearch"
                ></v-text-field>
              </v-col>
            </v-row>

            <v-row v-if="suggestions.length > 0">
              <v-col cols="12">
                <v-list>
                  <v-list-item
                    v-for="bird in suggestions"
                    :key="bird.ring"
                    @click="selectBird(bird)"
                  >
                    <v-list-item-title>
                      {{ bird.ring }} - {{ bird.species }}
                    </v-list-item-title>
                    <v-list-item-subtitle>
                      Letzte Sichtung: {{ formatDate(bird.last_seen) }}
                    </v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-col>
            </v-row>

            <v-row v-if="selectedBird">
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
                        <v-list-item-title>
                          {{ friend.ring }} - {{ friend.species }}
                        </v-list-item-title>
                        <v-list-item-subtitle>
                          Gemeinsame Sichtungen: {{ friend.count }}
                          <br>
                          Orte: {{ friend.places.join(', ') }}
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
import { ref } from 'vue';
import { format } from 'date-fns';
import type { BirdMeta, AnalyticsBirdMeta } from '@/types';
import * as api from '@/api';
import BirdDetails from '@/components/birds/BirdDetails.vue';
import FriendsMap from '@/components/map/FriendsMap.vue';

const activeTab = ref('friends');
const searchQuery = ref('');
const suggestions = ref<BirdMeta[]>([]);
const selectedBird = ref<BirdMeta | null>(null);
const friends = ref<AnalyticsBirdMeta[]>([]);

const handleSearch = async () => {
  if (searchQuery.value.length >= 3) {
    try {
      suggestions.value = await api.getBirdSuggestions(searchQuery.value);
    } catch (error) {
      console.error('Error fetching suggestions:', error);
    }
  } else {
    suggestions.value = [];
  }
};

const selectBird = async (bird: BirdMeta) => {
  try {
    const response = await api.getBirdFriends(bird.ring);
    selectedBird.value = response.bird;
    friends.value = response.friends;
    suggestions.value = [];
    searchQuery.value = '';
  } catch (error) {
    console.error('Error fetching bird friends:', error);
  }
};

const formatDate = (date: string) => {
  return format(new Date(date), 'dd.MM.yyyy');
};
</script>