<template>
  <div>
    <h1 class="text-h4 mb-4">Statistiken</h1>

    <v-tabs v-model="activeTab">
      <v-tab value="dashboard">Dashboard</v-tab>
      <v-tab value="friends">Freunde</v-tab>
      <v-tab value="radius">Umkreis</v-tab>
    </v-tabs>

    <v-window v-model="activeTab">
      <v-window-item value="dashboard">
        <v-card class="mt-4">
          <v-card-text>
            <v-row>
              <!-- Weekly Stats Card -->
              <v-col cols="12" md="6" lg="3">
                <v-card>
                  <v-card-text class="text-center">
                    <div class="text-h6 mb-2">Diese Woche</div>
                    <div class="text-h4 mb-2">{{ dashboardData?.bird_count_this_week || 0 }}</div>
                    <div :class="[
                      'text-subtitle-1',
                      weeklyTrend > 0 ? 'text-success' : weeklyTrend < 0 ? 'text-error' : ''
                    ]">
                      <v-icon :icon="weeklyTrend > 0 ? 'mdi-arrow-up' : weeklyTrend < 0 ? 'mdi-arrow-down' : 'mdi-minus'"></v-icon>
                      {{ weeklyTrend > 0 ? '+' : ''}}{{ dashboardData?.bird_count_this_week - (dashboardData?.bird_count_last_week || 0) }}
                    </div>
                    <div class="text-caption">Letzte Woche: {{ dashboardData?.bird_count_last_week || 0 }}</div>
                  </v-card-text>
                </v-card>
              </v-col>

              <!-- Daily Stats Card -->
              <v-col cols="12" md="6" lg="3">
                <v-card>
                  <v-card-text class="text-center">
                    <div class="text-h6 mb-2">Heute</div>
                    <div class="text-h4 mb-2">{{ dashboardData?.bird_count_today || 0 }}</div>
                    <div :class="[
                      'text-subtitle-1',
                      dailyTrend > 0 ? 'text-success' : dailyTrend < 0 ? 'text-error' : ''
                    ]">
                      <v-icon :icon="dailyTrend > 0 ? 'mdi-arrow-up' : dailyTrend < 0 ? 'mdi-arrow-down' : 'mdi-minus'"></v-icon>
                      {{ dailyTrend > 0 ? '+' : ''}}{{ dashboardData?.bird_count_today - (dashboardData?.bird_count_yesterday || 0) }}
                    </div>
                    <div class="text-caption">Gestern: {{ dashboardData?.bird_count_yesterday || 0 }}</div>
                  </v-card-text>
                </v-card>
              </v-col>

              <!-- Strike Days Card -->
              <v-col cols="12" md="6" lg="3">
                <v-card>
                  <v-card-text class="text-center">
                    <div class="text-h6 mb-2">Beobachtungs-Streak</div>
                    <div class="text-h4 mb-2">
                      <v-icon color="warning" icon="mdi-fire" class="me-2"></v-icon>
                      {{ dashboardData?.strike_day_count || 0 }}
                    </div>
                    <div class="text-subtitle-1">Tage in Folge</div>
                  </v-card-text>
                </v-card>
              </v-col>

              <!-- Total Stats Card -->
              <v-col cols="12" md="6" lg="3">
                <v-card>
                  <v-card-text class="text-center">
                    <div class="text-h6 mb-2">Gesamt</div>
                    <div class="text-h4 mb-2">
                      <v-icon icon="mdi-bird" class="me-2"></v-icon>
                      {{ dashboardData?.total_birds || 0 }}
                    </div>
                    <div class="text-subtitle-1">
                      <v-icon icon="mdi-eye" class="me-1"></v-icon>
                      {{ dashboardData?.total_sightings || 0 }} Sichtungen
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>

              <!-- Top Birds This Year -->
              <v-col cols="12" md="6">
                <v-card>
                  <v-card-title class="d-flex align-center">
                    <v-icon icon="mdi-medal" class="me-2"></v-icon>
                    Top 3 Vögel dieses Jahr
                  </v-card-title>
                  <v-card-text>
                    <v-list>
                      <v-list-item
                        v-for="(bird, index) in dashboardData?.top_3_birds_this_year"
                        :key="bird.ring"
                        :subtitle="`${bird.sighting_count} Sichtungen`"
                      >
                        <template v-slot:prepend>
                          <v-icon
                            :icon="index === 0 ? 'mdi-medal-outline' : ''"
                            :color="index === 0 ? 'warning' : index === 1 ? 'grey' : 'brown'"
                          ></v-icon>
                        </template>
                        {{ bird.ring }} - {{ bird.species }}
                      </v-list-item>
                    </v-list>
                  </v-card-text>
                </v-card>
              </v-col>

              <!-- Top Places This Year -->
              <v-col cols="12" md="6">
                <v-card>
                  <v-card-title class="d-flex align-center">
                    <v-icon icon="mdi-map-marker" class="me-2"></v-icon>
                    Top 3 Orte dieses Jahr
                  </v-card-title>
                  <v-card-text>
                    <v-list>
                      <v-list-item
                        v-for="(place, index) in dashboardData?.top_3_places_this_year"
                        :key="place.place"
                        :subtitle="`${place.count} Sichtungen`"
                      >
                        <template v-slot:prepend>
                          <v-icon
                            :icon="index === 0 ? 'mdi-map-marker-star' : 'mdi-map-marker'"
                            :color="index === 0 ? 'success' : index === 1 ? 'info' : 'grey'"
                          ></v-icon>
                        </template>
                        {{ place.place }}
                      </v-list-item>
                    </v-list>
                  </v-card-text>
                </v-card>
              </v-col>

              <!-- Species Chart -->
              <v-col cols="12">
                <v-card>
                  <v-card-title class="d-flex align-center">
                    <v-icon icon="mdi-chart-line" class="me-2"></v-icon>
                    Sichtungen pro Art (12 Monate)
                  </v-card-title>
                  <v-card-text>
                    <v-chart class="chart" :option="speciesTimelineOption" autoresize></v-chart>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-window-item>
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
      </v-window-item>
      <v-window-item value="radius">
        <v-card class="mt-4">
          <v-card-text>
            <v-row>
              <v-col cols="12" md="6">
                <v-card>
                  <v-card-title>Standort wählen</v-card-title>
                  <v-card-text>
                    <leaflet-map
                      v-model:latitude="selectedLat"
                      v-model:longitude="selectedLon"
                      :radius="radius"
                    ></leaflet-map>
                    <v-slider
                      v-model="radius"
                      label="Radius"
                      :ticks="radiusValues"
                      :tick-size="4"
                      :min="Math.min(...radiusValues)"
                      :max="Math.max(...radiusValues)"
                      :step="null"
                      thumb-label
                      :thumb-label-value="formatRadiusLabel(radius)"
                      class="mt-4"
                    ></v-slider>
                    <v-btn
                      color="primary"
                      block
                      :disabled="!selectedLat || !selectedLon"
                      @click="fetchRadiusData"
                      :loading="isLoadingRadius"
                    >
                      Suchen
                    </v-btn>
                  </v-card-text>
                </v-card>
              </v-col>
              <v-col cols="12" md="6" v-if="radiusStats">
                <v-card>
                  <v-card-title>Arten im Umkreis</v-card-title>
                  <v-card-text>
                    <v-chart class="chart" :option="speciesChartOption" autoresize></v-chart>
                  </v-card-text>
                </v-card>
              </v-col>
              <v-col cols="12" v-if="radiusStats">
                <v-card>
                  <v-card-title>Top 10 Vögel</v-card-title>
                  <v-card-text>
                    <v-chart class="chart" :option="topBirdsChartOption" autoresize @click="handleChartClick"></v-chart>
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
import { ref, computed, watch, onMounted } from 'vue';
import { format } from 'date-fns';
import type { BirdMeta, AnalyticsBirdMeta, Sighting, Dashboard } from '@/types';
import * as api from '@/api';
import BirdDetails from '@/components/birds/BirdDetails.vue';
import FriendsMap from '@/components/map/FriendsMap.vue';
import LeafletMap from '@/components/map/LeafletMap.vue';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { BarChart, PieChart, LineChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import { getSpeciesColor } from '@/utils/colors';
import { useRouter } from 'vue-router';

use([
  CanvasRenderer,
  BarChart,
  PieChart,
  LineChart,
  GridComponent,
  TooltipComponent,
  LegendComponent
]);

const activeTab = ref('dashboard');
const searchQuery = ref('');
const suggestions = ref<BirdMeta[]>([]);
const selectedBird = ref<BirdMeta | null>(null);
const friends = ref<AnalyticsBirdMeta[]>([]);
const map = ref<typeof LeafletMap | null>(null);
const dashboardData = ref<Dashboard | null>(null);
const router = useRouter();

// Watch for tab changes to trigger map resize
watch(activeTab, (newTab) => {
  if (newTab === 'radius') {
    // Force map resize after tab becomes visible
    setTimeout(() => {
      const mapElement = document.querySelector('.map-container');
      if (mapElement) {
        const event = new Event('resize');
        window.dispatchEvent(event);
      }
    }, 100);
  }
});

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

// Radius tab data
const selectedLat = ref<number | null>(50.1109);
const selectedLon = ref<number | null>(8.6821);
const radius = ref(100);
const radiusValues = computed(() => {
  const values = [];
  // 10m to 100m in steps of 10
  for (let i = 10; i <= 100; i += 10) values.push(i);
  // 100m to 1000m in steps of 100
  for (let i = 200; i <= 1000; i += 100) values.push(i);
  // 1km to 10km
  for (let i = 2000; i <= 10000; i += 1000) values.push(i);
  return values;
});

const formatRadiusLabel = (value: number) => {
  return value >= 1000 ? `${value/1000}km` : `${value}m`;
};

const radiusStats = ref<{
  speciesCounts: Record<string, number>;
  topBirds: { ring: string; count: number }[];
} | null>(null);
const isLoadingRadius = ref(false);

const fetchRadiusData = async () => {
  if (!selectedLat.value || !selectedLon.value) return;
  
  isLoadingRadius.value = true;
  try {
    const sightings = await api.getSightingsInRadius(
      selectedLat.value,
      selectedLon.value,
      radius.value
    );
    
    // Calculate species counts
    const speciesCounts: Record<string, number> = {};
    const birdCounts: Record<string, { count: number; species: string }> = {};
    
    sightings.forEach(sighting => {
      // Count species
      if (sighting.species) {
        speciesCounts[sighting.species] = (speciesCounts[sighting.species] || 0) + 1;
      }
      
      // Count individual birds
      if (sighting.ring) {
        // Initialize if first time seeing this ring
        if (!birdCounts[sighting.ring]) {
          birdCounts[sighting.ring] = {
            count: 0,
            species: sighting.species || ''
          };
        }
        // Increment the count
        birdCounts[sighting.ring].count += 1;
      }
    });
    
    // Get top 10 birds
    const topBirds = Object.entries(birdCounts)
      .map(([ring, data]) => ({
        ring,
        count: data.count,
        species: data.species
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
    
    radiusStats.value = {
      speciesCounts,
      topBirds
    };
  } catch (error) {
    console.error('Error fetching radius data:', error);
  } finally {
    isLoadingRadius.value = false;
  }
};

const speciesChartOption = computed(() => {
  if (!radiusStats.value) return {};
  
  const { speciesCounts } = radiusStats.value;
  return {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      type: 'scroll',
      orient: 'vertical',
      right: 10,
      top: 20,
      bottom: 20,
      textStyle: {
        overflow: 'truncate',
        width: 150
      }
    },
    grid: {
      containLabel: true
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['40%', '50%'],
      avoidLabelOverlap: true,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: false
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 16,
          fontWeight: 'bold'
        }
      },
      data: Object.entries(speciesCounts)
        .map(([name, value]) => ({
          name,
          value,
          itemStyle: {
            color: getSpeciesColor(name)
          }
        }))
        .sort((a, b) => b.value - a.value) // Sort by count to show most frequent species first
    }]
  };
});

const topBirdsChartOption = computed(() => {
  if (!radiusStats.value) return {};
  
  const { topBirds } = radiusStats.value;
  // Sort birds in ascending order for display
  const sortedBirds = [...topBirds].sort((a, b) => a.count - b.count);

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params: any) => {
        const dataIndex = params[0].dataIndex;
        const bird = sortedBirds[dataIndex];
        return `${bird.ring}${bird.species ? ` (${bird.species})` : ''}: ${bird.count}`;
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value'
    },
    yAxis: {
      type: 'category',
      data: sortedBirds.map(bird => bird.ring)
    },
    series: [{
      type: 'bar',
      data: sortedBirds.map(bird => ({
        value: bird.count,
        itemStyle: {
          color: getSpeciesColor(bird.species || '')
        }
      })),
      emphasis: {
        itemStyle: {
          opacity: 0.8,
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      },
      cursor: 'pointer'
    }]
  };
});

const weeklyTrend = computed(() => {
  if (!dashboardData.value) return 0;
  const thisWeek = dashboardData.value.bird_count_this_week;
  const lastWeek = dashboardData.value.bird_count_last_week;
  if (lastWeek === 0) return 100;
  return Math.round(((thisWeek - lastWeek) / lastWeek) * 100);
});

const dailyTrend = computed(() => {
  if (!dashboardData.value) return 0;
  const today = dashboardData.value.bird_count_today;
  const yesterday = dashboardData.value.bird_count_yesterday;
  if (yesterday === 0) return 100;
  return Math.round(((today - yesterday) / yesterday) * 100);
});

const speciesTimelineOption = computed(() => {
  if (!dashboardData.value) return {};

  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'];
  const data = dashboardData.value.rolling_year_count_per_month_per_species;
  
  // Get all months in the last year as x-axis labels
  const today = new Date();
  const xAxisData = Array.from({ length: 12 }, (_, i) => {
    const d = new Date(today.getFullYear(), today.getMonth() - (11 - i));
    return `${monthNames[d.getMonth()]} ${d.getFullYear()}`;
  });

  // Prepare series data
  const series = Object.entries(data).map(([species, counts]) => {
    const monthData = new Array(12).fill(0);
    counts.forEach(count => {
      const monthIndex = count.month - 1;
      monthData[monthIndex] = count.count;
    });

    return {
      name: species,
      type: 'line',
      data: monthData,
      smooth: true,
      itemStyle: {
        color: getSpeciesColor(species)
      }
    };
  });

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      type: 'scroll',
      orient: 'horizontal',
      top: 'bottom'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: xAxisData
    },
    yAxis: {
      type: 'value'
    },
    series
  };
});

const handleChartClick = (params: any) => {
  if (params.componentType === 'series' && radiusStats.value?.topBirds) {
    const bird = radiusStats.value.topBirds[params.dataIndex];
    if (bird?.ring) {
      router.push(`/birds/${bird.ring}`);
    }
  }
};

onMounted(async () => {
  try {
    dashboardData.value = await api.getDashboard();
  } catch (error) {
    console.error('Error fetching dashboard data:', error);
  }
});
</script>

<style scoped>
.text-success {
  color: #4CAF50 !important;
}

.text-error {
  color: #FF5252 !important;
}

.chart {
  height: 400px;
}

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