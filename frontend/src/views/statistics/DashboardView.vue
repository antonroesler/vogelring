<template>
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
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import type { Dashboard } from '@/types';
import * as api from '@/api';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import { getSpeciesColor } from '@/utils/colors';

use([
  CanvasRenderer,
  LineChart,
  GridComponent,
  TooltipComponent,
  LegendComponent
]);

const dashboardData = ref<Dashboard | null>(null);

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

onMounted(async () => {
  try {
    console.log('Fetching dashboard data...');
    dashboardData.value = await api.getDashboard();
    console.log('Dashboard data received:', dashboardData.value);
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
</style> 