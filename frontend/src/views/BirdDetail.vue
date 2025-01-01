<template>
  <div>
    <v-progress-circular
      v-if="isLoading"
      indeterminate
      color="primary"
      size="64"
      class="ma-4"
    ></v-progress-circular>

    <v-alert
      v-else-if="error"
      type="error"
      text="Fehler beim Laden der Vogeldaten"
      class="ma-4"
    ></v-alert>

    <template v-else>
      <!-- New Header Section -->
      <v-card class="mb-4">
        <v-card-text>
          <div class="d-flex align-center justify-space-between mb-2">
            <div class="d-flex align-center">
              <h2 class="text-h5 font-weight-bold mb-0">
                {{ bird?.species || 'Loading...' }}
              </h2>
              <v-chip
                class="ml-4 ring-chip"
                color="primary"
                size="large"
              >
                <span class="font-weight-regular">Ring:</span>
                <span class="ring-number">{{ bird?.ring }}</span>
              </v-chip>
            </div>
            <v-btn
              color="primary"
              :to="`/birds/${bird?.ring}/environment-analysis`"
              :disabled="!bird?.ring"
            >
              Umfeld
            </v-btn>
          </div>
        </v-card-text>
      </v-card>

      <v-row>
        <!-- Basic Info Card -->
        <v-col cols="12" md="4">
          <bird-details 
            :bird="bird"
            :ringingData="ringingData"
          ></bird-details>

          <!-- Partners Card - Now shows even when no partners -->
          <v-card class="mt-4">
            <v-card-title>Partner</v-card-title>
            <v-card-text>
              <v-list v-if="bird?.partners?.length" density="compact">
                <v-list-item
                  v-for="partner in bird.partners"
                  :key="`${partner.ring}-${partner.year}`"
                  :href="partner.ring !== 'ub' ? `/birds/${partner.ring}` : undefined"
                  :target="partner.ring !== 'ub' ? '_blank' : undefined"
                  :class="partner.ring !== 'ub' ? 'clickable-partner' : ''"
                >
                  <v-list-item-title>
                    {{ partner.ring === 'ub' ? 'Unberingt' : partner.ring }}
                  </v-list-item-title>
                  <v-list-item-subtitle>
                    {{ partner.year }}
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
              <p v-else class="text-body-1 text-medium-emphasis">
                Keine Partner aufgezeichnet.
              </p>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Analytics Cards -->
        <v-col cols="12" md="8">
          <v-card class="mb-4">
            <v-card-title>Aufenthaltsmuster</v-card-title>
            <v-card-text>
              <v-chart class="chart" :option="timelineChartOption" autoresize></v-chart>
            </v-card-text>
          </v-card>

          <v-card class="mb-4">
            <v-card-title>Melder Statistik</v-card-title>
            <v-card-text>
              <v-chart class="chart" :option="reporterChartOption" autoresize></v-chart>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Map Card -->
        <v-col cols="12">
          <v-card class="mb-4">
            <v-card-title>Sichtungskarte</v-card-title>
            <v-card-text>
              <sightings-map
                v-if="bird?.sightings"
                :other-sightings="bird.sightings"
                :ringing-data="ringingData"
                :timeline-mode="true"
              ></sightings-map>
              <p v-else class="text-body-1 text-medium-emphasis">
                Keine Sichtungsdaten verfügbar.
              </p>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Sightings List -->
        <v-col cols="12">
          <v-card>
            <v-card-title>Sichtungen</v-card-title>
            <v-card-text>
              <v-table>
                <thead>
                  <tr>
                    <th>Datum</th>
                    <th>Ort</th>
                    <th>Melder</th>
                    <th>Ablesung</th>
                    <th>Partner</th>
                    <th>Kommentar</th>
                  </tr>
                </thead>
                <tbody>
                  <tr 
                    v-for="sighting in sortedSightings" 
                    :key="sighting.id"
                    @click="navigateToSighting(sighting.id)"
                    style="cursor: pointer"
                    class="sighting-row"
                  >
                    <td>{{ formatDate(sighting.date) }}</td>
                    <td>{{ sighting.place }}</td>
                    <td>{{ sighting.melder }}</td>
                    <td>{{ sighting.reading }}</td>
                    <td>{{ sighting.partner || '-' }}</td>
                    <td>{{ sighting.comment }}</td>
                  </tr>
                </tbody>
              </v-table>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { format } from 'date-fns';
import type { BirdMeta, Ringing } from '@/types';
import * as api from '@/api';
import BirdDetails from '@/components/birds/BirdDetails.vue';
import SightingsMap from '@/components/map/SightingsMap.vue';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { BarChart, ScatterChart, LineChart, HeatmapChart } from 'echarts/charts';
import { 
  GridComponent, 
  TooltipComponent, 
  LegendComponent,
  DataZoomComponent,
  VisualMapComponent
} from 'echarts/components';
import axios from 'axios';

use([
  CanvasRenderer,
  BarChart,
  ScatterChart,
  LineChart,
  HeatmapChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  VisualMapComponent
]);

const route = useRoute();
const router = useRouter();
const bird = ref<BirdMeta | null>(null);
const ringingData = ref<Ringing | null>(null);
const isLoading = ref(true);
const error = ref<string | null>(null);

// Load bird data
onMounted(async () => {
  const ring = route.params.ring as string;
  try {
    isLoading.value = true;
    error.value = null;
    
    // Add more detailed error logging
    console.log('Attempting to load bird with ring:', ring);
    
    bird.value = await api.getBirdByRing(ring);
    
    if (bird.value?.ring) {
      try {
        ringingData.value = await api.getRingingByRing(bird.value.ring);
      } catch (ringingError) {
        console.error('Error loading ringing data:', ringingError);
        // Don't fail the whole component if ringing data fails to load
        ringingData.value = null;
      }
    }
  } catch (err) {
    console.error('Error loading bird:', err);
    if (axios.isAxiosError(err)) {
      error.value = `Fehler beim Laden der Vogeldaten: ${err.response?.status === 502 ? 'Server nicht erreichbar' : err.message}`;
    } else {
      error.value = 'Fehler beim Laden der Vogeldaten';
    }
  } finally {
    isLoading.value = false;
  }
});

const sortedSightings = computed(() => {
  if (!bird.value) return [];
  return [...bird.value.sightings].sort((a, b) => {
    if (!a.date || !b.date) return 0;
    return new Date(b.date).getTime() - new Date(a.date).getTime();
  });
});

const formatDate = (date: string | null) => {
  if (!date) return '';
  return format(new Date(date), 'dd.MM.yyyy');
};

const navigateToSighting = (id: string) => {
  router.push(`/entries/${id}`);
};

const navigateToEnvironmentAnalysis = () => {
  if (bird.value?.ring) {
    router.push(`/birds/${bird.value.ring}/environment-analysis`);
  } else {
    console.error('Ring number is not available');
  }
};

// Timeline Chart
const timelineChartOption = computed(() => {
  if (!bird.value?.sightings?.length) return {};

  const sightings = bird.value.sightings;

  // Get all unique places
  const places = Array.from(new Set(sightings.map(s => s.place || 'Unbekannt')));

  // Create a map to store sighting counts for each place and month
  const sightingCounts: Record<string, Record<number, number>> = {};
  places.forEach(place => {
    sightingCounts[place] = {};
    // Initialize all months with 0
    for (let month = 0; month < 12; month++) {
      sightingCounts[place][month] = 0;
    }
  });

  // Count sightings for each place and month
  sightings.forEach(sighting => {
    if (!sighting.date) return;
    const date = new Date(sighting.date);
    const month = date.getMonth();
    const place = sighting.place || 'Unbekannt';
    sightingCounts[place][month]++;
  });

  // Find the maximum count for color scaling
  const maxCount = Math.max(
    ...Object.values(sightingCounts).flatMap(monthCounts => 
      Object.values(monthCounts)
    )
  );

  // Create the data array for the heatmap
  const data = places.flatMap((place, placeIndex) => 
    Array.from({ length: 12 }, (_, month) => [
      month,
      placeIndex,
      sightingCounts[place][month]
    ])
  );

  return {
    tooltip: {
      position: 'top',
      formatter: (params: any) => {
        const month = new Date(2000, params.data[0], 1).toLocaleString('de-DE', { month: 'long' });
        const place = places[params.data[1]];
        const count = params.data[2];
        return `${place}<br/>${month}: ${count} Sichtung${count !== 1 ? 'en' : ''}`;
      }
    },
    grid: {
      left: '15%',
      right: '15%',
      top: '10%',
      bottom: '10%'
    },
    xAxis: {
      type: 'category',
      data: Array.from({ length: 12 }, (_, i) => 
        new Date(2000, i, 1).toLocaleString('de-DE', { month: 'long' }).charAt(0)
      ),
      splitArea: {
        show: true
      },
      axisLabel: {
        interval: 0,
        align: 'center',
        fontSize: 14,
        fontWeight: 'bold',
        color: '#333',
        margin: 16
      },
      axisTick: {
        show: false
      },
      position: 'top'
    },
    yAxis: {
      type: 'category',
      data: places,
      splitArea: {
        show: true
      }
    },
    visualMap: {
      min: 0,
      max: maxCount,
      calculable: true,
      orient: 'vertical',
      right: '0%',
      top: 'center',
      text: ['Häufig', 'Selten'],
      color: ['#d73027', '#fc8d59', '#fee090'],
      inRange: {
        color: ['#f0f0f0', '#fee090', '#fc8d59', '#d73027']
      }
    },
    series: [{
      name: 'Sichtungen',
      type: 'heatmap',
      data: data,
      label: {
        show: true,
        formatter: (params: any) => params.data[2] || ''
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      },
      itemStyle: {
        emphasis: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  };
});

// Reporter Chart
const reporterChartOption = computed(() => {
  if (!bird.value?.sightings?.length) return {};

  const reporterCounts = bird.value.sightings.reduce((acc, sighting) => {
    const reporter = sighting.melder || 'Unbekannt';
    acc[reporter] = (acc[reporter] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const sortedReporters = Object.entries(reporterCounts)
    .sort((a, b) => b[1] - a[1])
    .map(([name]) => name);

  const data = sortedReporters.map(reporter => ({
    value: reporterCounts[reporter],
    name: reporter
  }));

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
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
      data: sortedReporters
    },
    series: [{
      type: 'bar',
      data
    }]
  };
});
</script>

<style scoped>
.chart {
  height: 300px;
}

.sighting-row:hover {
  background-color: rgba(0, 0, 0, 0.04);
}

.bird-header {
  text-align: center;
  padding: 24px;
}

.ring-chip {
  font-size: 1.1rem !important;
}

.ring-chip .ring-number {
  font-weight: 700;
  font-family: monospace;
  margin-left: 4px;
}

.clickable-partner {
  cursor: pointer;
  transition: background-color 0.2s;
}

.clickable-partner:hover {
  background-color: rgba(0, 0, 0, 0.04);
}
</style> 