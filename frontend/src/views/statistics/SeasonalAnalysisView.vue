<template>
  <v-card class="mt-4">
    <v-card-text>
      <v-row>
        <v-col cols="12">
          <v-card>
            <v-card-title class="d-flex align-center">
              <span>Saisonale Verteilung</span>
              <v-spacer></v-spacer>
              <v-select
                v-model="selectedSpecies"
                :items="availableSpecies"
                label="Arten auswählen"
                multiple
                chips
                closable-chips
                class="species-select"
              ></v-select>
            </v-card-title>
            <v-card-text>
              <v-progress-circular
                v-if="isLoading"
                indeterminate
                color="primary"
                class="ma-4"
              ></v-progress-circular>
              <div v-else>
                <div class="species-grid">
                  <div 
                    v-for="(species, index) in selectedSpecies" 
                    :key="species" 
                    class="species-row"
                    :class="{ 'not-last': index < selectedSpecies.length - 1 }"
                  >
                    <div class="species-label">{{ species }}</div>
                    <v-chart :option="getChartOption(species)" class="chart" autoresize></v-chart>
                  </div>
                </div>
                
                <!-- Chart explanation -->
                <v-card class="mt-6 explanation-card">
                  <v-card-text>
                    <h3 class="text-h6 mb-4">Erklärung der Visualisierung</h3>
                    <div class="d-flex flex-column gap-4">
                      <div class="explanation-item">
                        <div class="explanation-title">
                          <div class="line-sample main-line"></div>
                          <strong>Aktuelle Sichtungen (letzte 12 Monate)</strong>
                        </div>
                        <p>Zeigt die tatsächliche Anzahl der Sichtungen für jeden Monat aus den letzten 12 Monaten.</p>
                      </div>
                      <div class="explanation-item">
                        <div class="explanation-title">
                          <div class="line-sample q3-line"></div>
                          <strong>Q3-Linie (75% Quartil)</strong>
                        </div>
                        <p>Diese Linie zeigt den Wert an, unter dem 75% aller historischen Sichtungen für diesen Monat liegen.</p>
                      </div>
                      <div class="explanation-item">
                        <div class="explanation-title">
                          <div class="area-sample"></div>
                          <strong>Q1-Q3 Bereich</strong>
                        </div>
                        <p>Der schattierte Bereich zeigt die typische Spanne der Sichtungen. 50% aller historischen Sichtungen liegen in diesem Bereich.</p>
                      </div>
                      <div class="explanation-item">
                        <div class="explanation-title">
                          <div class="x-sample">×</div>
                          <strong>Historisches Maximum</strong>
                        </div>
                        <p>Der höchste jemals erfasste Wert für diesen Monat.</p>
                      </div>
                    </div>
                  </v-card-text>
                </v-card>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart } from 'echarts/charts';
import { 
  GridComponent,
  TooltipComponent,
  MarkLineComponent,
  MarkAreaComponent,
  LegendComponent
} from 'echarts/components';
import { getSpeciesColor } from '@/utils/colors';
import * as api from '@/api';

// Register ECharts components
use([
  CanvasRenderer,
  LineChart,
  GridComponent,
  TooltipComponent,
  MarkLineComponent,
  MarkAreaComponent,
  LegendComponent
]);

const isLoading = ref(true);
const seasonalData = ref<any>(null);

// Default selected species
const selectedSpecies = ref(['Graugans', 'Kanadagans', 'Nilgans', 'Höckerschwan']);

const monthNames = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'];

// Season definitions with more subtle colors
const seasons = [
  { name: 'Winter', color: 'rgba(227, 242, 253, 0.15)', start: 0, end: 2 },
  { name: 'Frühling', color: 'rgba(232, 245, 233, 0.15)', start: 3, end: 5 },
  { name: 'Sommer', color: 'rgba(255, 243, 224, 0.15)', start: 6, end: 8 },
  { name: 'Herbst', color: 'rgba(239, 235, 233, 0.15)', start: 9, end: 11 }
];

// Get all available species from the data
const availableSpecies = computed(() => {
  if (!seasonalData.value) return [];
  return Object.keys(seasonalData.value.counts).sort();
});

const getChartOption = (species: string) => {
  if (!seasonalData.value) return {};

  const speciesData = seasonalData.value.counts[species];
  const color = getSpeciesColor(species);

  // Create season mark areas
  const markArea = {
    silent: true,
    data: seasons.map(season => [{
      xAxis: season.start,
      itemStyle: { color: season.color }
    }, {
      xAxis: season.end + 1
    }])
  };

  // Prepare data arrays
  const maxValue = Math.max(...speciesData.map((d: { max_count: number }) => d.max_count));

  const recentData = speciesData.map((count: { recent_count: number }) => 
    (count.recent_count / maxValue) * 100
  );
  const q1Data = speciesData.map((count: { q1_avg: number }) => 
    (count.q1_avg / maxValue) * 100
  );
  const q3Data = speciesData.map((count: { q3_avg: number }) => 
    (count.q3_avg / maxValue) * 100
  );
  const maxData = speciesData.map((count: { max_count: number }) => 
    (count.max_count / maxValue) * 100
  );

  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any[]) => {
        const month = monthNames[params[0].dataIndex];
        const data = speciesData[params[0].dataIndex];
        return `${month}<br/>
                Aktuelle Sichtungen: ${data.recent_count}<br/>
                Maximum: ${data.max_count} Sichtungen<br/>
                Quartile: ${data.q1_avg} - ${data.q3_avg} Sichtungen`;
      }
    },
    grid: {
      top: '8%',
      bottom: '8%',
      left: '8%',
      right: '5%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: monthNames,
      boundaryGap: false,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { 
        color: '#666',
        fontSize: 10,
        interval: 1
      },
      splitLine: { show: false }
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: '#666',
        fontSize: 10,
        formatter: (value: number) => {
          return Math.round((value / 100) * maxValue).toString();
        }
      },
      splitLine: {
        lineStyle: {
          type: 'dashed',
          color: 'rgba(0,0,0,0.05)'
        }
      }
    },
    series: [
      {
        name: 'Q1-Q3 Bereich',
        type: 'line',
        smooth: true,
        symbol: 'none',
        data: q3Data,
        lineStyle: { opacity: 0 },
        areaStyle: {
          color,
          opacity: 0.1,
          origin: 'start'
        },
        stack: 'quartile',
        stackStrategy: 'all'
      },
      {
        name: 'Q3',
        type: 'line',
        smooth: true,
        symbol: 'none',
        data: q3Data,
        lineStyle: {
          width: 1,
          color: color,
          opacity: 0.5
        },
        z: 1
      },
      {
        name: 'Aktuelle Sichtungen',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        data: recentData,
        lineStyle: {
          width: 2,
          color: color
        },
        itemStyle: {
          color: color
        },
        markArea: markArea,
        z: 2
      },
      {
        name: 'Maximum',
        type: 'scatter',
        symbol: 'path://M-5,-5 L5,5 M-5,5 L5,-5',  // 'X' shape
        symbolSize: 8,
        data: maxData,
        itemStyle: {
          color: color,
          opacity: 0.7
        },
        z: 3
      }
    ]
  };
};

onMounted(async () => {
  try {
    const response = await api.getSeasonalAnalysis();
    seasonalData.value = response;
  } catch (error) {
    console.error('Error fetching seasonal analysis:', error);
  } finally {
    isLoading.value = false;
  }
});
</script>

<style scoped>
.species-grid {
  background: white;
  border: 1px solid #eee;
  border-radius: 8px;
  overflow: hidden;
}

.species-row {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  background: white;
  min-height: 180px;
}

.species-row.not-last {
  border-bottom: 1px solid #f5f5f5;
}

.species-label {
  width: 120px;
  font-weight: 500;
  color: #333;
  font-size: 0.9rem;
}

.chart {
  flex: 1;
  height: 150px;
  min-height: 150px;
}

.species-select {
  max-width: 400px;
}

.explanation-card {
  background: #f8f9fa !important;
  border: none !important;
}

.explanation-item {
  margin-bottom: 16px;
}

.explanation-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
}

.line-sample {
  width: 24px;
  height: 2px;
  background: #666;
}

.main-line {
  height: 2px;
}

.q3-line {
  height: 1px;
  opacity: 0.5;
}

.area-sample {
  width: 24px;
  height: 16px;
  background: rgba(102, 102, 102, 0.1);
  border-radius: 2px;
}

.x-sample {
  font-size: 16px;
  line-height: 1;
  color: #666;
  opacity: 0.7;
}

p {
  color: #666;
  margin: 0;
  font-size: 0.9rem;
}
</style> 