<template>
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
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import type { Sighting } from '@/types';
import * as api from '@/api';
import LeafletMap from '@/components/map/LeafletMap.vue';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { BarChart, PieChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import { getSpeciesColor } from '@/utils/colors';

use([
  CanvasRenderer,
  BarChart,
  PieChart,
  GridComponent,
  TooltipComponent,
  LegendComponent
]);

const router = useRouter();
const selectedLat = ref<number | null>(50.1109);
const selectedLon = ref<number | null>(8.6821);
const radius = ref(100);
const isLoadingRadius = ref(false);

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

const radiusStats = ref<{
  speciesCounts: Record<string, number>;
  topBirds: { ring: string; count: number; species: string }[];
} | null>(null);

const formatRadiusLabel = (value: number) => {
  return value >= 1000 ? `${value/1000}km` : `${value}m`;
};

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
        .sort((a, b) => b.value - a.value)
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

const handleChartClick = (params: any) => {
  if (params.componentType === 'series' && radiusStats.value?.topBirds) {
    const bird = radiusStats.value.topBirds[params.dataIndex];
    if (bird?.ring) {
      router.push(`/birds/${bird.ring}`);
    }
  }
};
</script>

<style scoped>
.chart {
  height: 400px;
}
</style> 