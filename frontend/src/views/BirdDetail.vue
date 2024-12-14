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
        <v-card-text class="bird-header">
          <div class="text-h3 mb-2">{{ bird?.species || 'Unbekannte Art' }}</div>
          <div class="text-h4 text-medium-emphasis">Ring: {{ bird?.ring || 'Unbekannt' }}</div>
        </v-card-text>
      </v-card>

      <v-row>
        <!-- Basic Info Card -->
        <v-col cols="12" md="4">
          <bird-details 
            :bird="bird"
            :ringingData="ringingData"
          ></bird-details>
        </v-col>

        <!-- Analytics Cards -->
        <v-col cols="12" md="8">
          <v-card class="mb-4">
            <v-card-title>Zeitleiste</v-card-title>
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
import { BarChart, ScatterChart, LineChart } from 'echarts/charts';
import { 
  GridComponent, 
  TooltipComponent, 
  LegendComponent,
  DataZoomComponent 
} from 'echarts/components';

use([
  CanvasRenderer,
  BarChart,
  ScatterChart,
  LineChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent
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
    bird.value = await api.getBirdByRing(ring);
    if (bird.value?.ring) {
      ringingData.value = await api.getRingingByRing(bird.value.ring);
    }
  } catch (err) {
    console.error('Error loading bird:', err);
    error.value = 'Fehler beim Laden der Vogeldaten';
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

// Timeline Chart
const timelineChartOption = computed(() => {
  if (!bird.value?.sightings?.length) return {};

  const sightings = [...bird.value.sightings].sort((a, b) => {
    if (!a.date || !b.date) return 0;
    return new Date(a.date).getTime() - new Date(b.date).getTime();
  });

  // Get unique years from sightings
  const years = Array.from(new Set(sightings.map(s => 
    new Date(s.date || '').getFullYear()
  ))).sort();

  // Create splitLines data for January 1st of each year
  const splitLines = years.map(year => ({
    value: `${year}-01-01`,
    lineStyle: {
      color: '#ddd',
      type: 'solid',
      width: 1
    }
  }));

  // Group sightings by place
  const placeGroups = sightings.reduce((acc, sighting) => {
    const place = sighting.place || 'Unbekannt';
    if (!acc[place]) {
      acc[place] = [];
    }
    acc[place].push(sighting);
    return acc;
  }, {} as Record<string, typeof sightings>);

  // Sort places by first sighting date
  const sortedPlaces = Object.entries(placeGroups)
    .sort(([, a], [, b]) => {
      const aDate = new Date(a[0].date || '');
      const bDate = new Date(b[0].date || '');
      return aDate.getTime() - bDate.getTime();
    })
    .map(([place]) => place);

  // Create series data for each place
  const series = sortedPlaces.map((place, index) => ({
    name: place,
    type: 'line',
    symbol: 'circle',
    symbolSize: 8,
    data: placeGroups[place].map(s => [s.date, index]),
    step: 'middle',
    lineStyle: {
      width: 2
    }
  }));

  return {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        const sighting = sightings.find(s => s.date === params.value[0]);
        if (!sighting) return '';
        return `
          <strong>${formatDate(sighting.date)}</strong><br/>
          Ort: ${sighting.place || 'Unbekannt'}<br/>
          Melder: ${sighting.melder || 'Unbekannt'}<br/>
          ${sighting.comment ? `Kommentar: ${sighting.comment}` : ''}
        `;
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'time',
      axisLabel: {
        formatter: (value: string) => {
          const date = new Date(value);
          // If zoomed in (determined by the data zoom's current range)
          if (date.getDate() === 1) {  // Only show labels for first of month
            const month = date.getMonth();
            if (month === 0) {
              return date.getFullYear().toString();  // Just year for January
            } else {
              return format(date, 'MM.yyyy');  // Month and year for other months
            }
          }
          return '';  // Hide other labels
        },
        interval: 0
      },
      splitLine: {
        show: true,
        lineStyle: {
          color: '#ddd',
          type: 'solid',
          width: 1
        },
        interval: (index: number, value: string) => {
          // Only show lines for January 1st of each year
          const date = new Date(value);
          return date.getMonth() === 0 && date.getDate() === 1;
        }
      },
      axisTick: {
        show: false
      },
      splitArea: {
        show: false
      },
      minorSplitLine: {
        show: false
      },
      min: sightings[0]?.date,  // Start from first sighting
      max: sightings[sightings.length - 1]?.date  // End at last sighting
    },
    yAxis: {
      type: 'category',
      data: sortedPlaces,
      inverse: true,  // Put first place at top
      axisLine: { show: false },
      axisTick: { show: false }
    },
    dataZoom: [
      {
        type: 'slider',
        xAxisIndex: 0,
        filterMode: 'none',
        height: 20,
        bottom: 50,
        start: 0,
        end: 100
      }
    ],
    series
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
</style> 