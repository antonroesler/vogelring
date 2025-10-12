<template>
  <v-container class="pa-6">
    <div class="text-h4 mb-8 font-weight-light">Dashboard</div>
    
    <!-- Stats Grid -->
    <v-row class="mb-8">
      <!-- This Week -->
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 text-center" elevation="2">
          <div class="text-h3 font-weight-bold primary--text mb-2">
            {{ dashboardData?.count_sightings_this_week || 0 }}
          </div>
          <div class="text-subtitle-1 text-medium-emphasis">Diese Woche</div>
          <div class="text-caption mt-1">
            <span :class="weeklyTrendClass">
              <v-icon size="small" :icon="weeklyTrendIcon" class="me-1"></v-icon>
              {{ weeklyTrendText }}
            </span>
          </div>
        </v-card>
      </v-col>

      <!-- Today -->
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 text-center" elevation="2">
          <div class="text-h3 font-weight-bold success--text mb-2">
            {{ dashboardData?.count_sightings_today || 0 }}
          </div>
          <div class="text-subtitle-1 text-medium-emphasis">Heute</div>
          <div class="text-caption mt-1">
            <span :class="dailyTrendClass">
              <v-icon size="small" :icon="dailyTrendIcon" class="me-1"></v-icon>
              {{ dailyTrendText }}
            </span>
          </div>
        </v-card>
      </v-col>

      <!-- Streak -->
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 text-center" elevation="2">
          <div class="text-h3 font-weight-bold warning--text mb-2">
            <v-icon color="warning" icon="mdi-fire" class="me-2"></v-icon>
            {{ dashboardData?.day_streak || 0 }}
          </div>
          <div class="text-subtitle-1 text-medium-emphasis">Tage Streak</div>
        </v-card>
      </v-col>

      <!-- Total -->
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 text-center" elevation="2">
          <div class="text-h3 font-weight-bold info--text mb-2">
            {{ dashboardData?.count_total_sightings || 0 }}
          </div>
          <div class="text-subtitle-1 text-medium-emphasis">Gesamt</div>
          <div class="text-caption mt-1">
            {{ dashboardData?.count_total_unique_birds || 0 }} Vögel
          </div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Top Lists -->
    <v-row>
      <!-- Top Species -->
      <v-col cols="12" md="6">
        <v-card elevation="2">
          <v-card-title class="text-h6 font-weight-medium">
            <v-icon icon="mdi-bird" class="me-2"></v-icon>
            Top Arten
          </v-card-title>
          <v-card-text class="pa-0">
            <v-list density="compact">
              <v-list-item
                v-for="([species, count], index) in topSpeciesList"
                :key="species"
                class="px-4"
              >
                <template #prepend>
                  <div class="text-h6 font-weight-bold me-4" style="min-width: 24px;">
                    {{ index + 1 }}
                  </div>
                </template>
                <v-list-item-title>{{ species }}</v-list-item-title>
                <template #append>
                  <v-chip size="small" color="primary" variant="tonal">
                    {{ count }}
                  </v-chip>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Top Locations -->
      <v-col cols="12" md="6">
        <v-card elevation="2">
          <v-card-title class="text-h6 font-weight-medium">
            <v-icon icon="mdi-map-marker" class="me-2"></v-icon>
            Top Orte
          </v-card-title>
          <v-card-text class="pa-0">
            <v-list density="compact">
              <v-list-item
                v-for="([location, count], index) in topLocationsList"
                :key="location"
                class="px-4"
              >
                <template #prepend>
                  <div class="text-h6 font-weight-bold me-4" style="min-width: 24px;">
                    {{ index + 1 }}
                  </div>
                </template>
                <v-list-item-title>{{ location }}</v-list-item-title>
                <template #append>
                  <v-chip size="small" color="success" variant="tonal">
                    {{ count }}
                  </v-chip>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import * as api from '../../api';
import type { Dashboard } from '../../types';

const dashboardData = ref<Dashboard | null>(null);

const weeklyTrendClass = computed(() => {
  const thisWeek = dashboardData.value?.count_sightings_this_week || 0;
  const lastWeek = dashboardData.value?.count_sightings_last_week || 0;
  if (thisWeek > lastWeek) return 'text-success';
  if (thisWeek < lastWeek) return 'text-error';
  return 'text-medium-emphasis';
});

const weeklyTrendIcon = computed(() => {
  const thisWeek = dashboardData.value?.count_sightings_this_week || 0;
  const lastWeek = dashboardData.value?.count_sightings_last_week || 0;
  if (thisWeek > lastWeek) return 'mdi-arrow-up';
  if (thisWeek < lastWeek) return 'mdi-arrow-down';
  return 'mdi-minus';
});

const weeklyTrendText = computed(() => {
  const thisWeek = dashboardData.value?.count_sightings_this_week || 0;
  const lastWeek = dashboardData.value?.count_sightings_last_week || 0;
  const diff = thisWeek - lastWeek;
  if (diff > 0) return `+${diff} vs. letzte Woche`;
  if (diff < 0) return `${diff} vs. letzte Woche`;
  return 'Keine Änderung';
});

const dailyTrendClass = computed(() => {
  const today = dashboardData.value?.count_sightings_today || 0;
  const yesterday = dashboardData.value?.count_sightings_yesterday || 0;
  if (today > yesterday) return 'text-success';
  if (today < yesterday) return 'text-error';
  return 'text-medium-emphasis';
});

const dailyTrendIcon = computed(() => {
  const today = dashboardData.value?.count_sightings_today || 0;
  const yesterday = dashboardData.value?.count_sightings_yesterday || 0;
  if (today > yesterday) return 'mdi-arrow-up';
  if (today < yesterday) return 'mdi-arrow-down';
  return 'mdi-minus';
});

const dailyTrendText = computed(() => {
  const today = dashboardData.value?.count_sightings_today || 0;
  const yesterday = dashboardData.value?.count_sightings_yesterday || 0;
  const diff = today - yesterday;
  if (diff > 0) return `+${diff} vs. gestern`;
  if (diff < 0) return `${diff} vs. gestern`;
  return 'Keine Änderung';
});

const topSpeciesList = computed(() => {
  if (!dashboardData.value?.top_species) return [];
  return Object.entries(dashboardData.value.top_species)
    .filter(([species]) => species !== 'null')
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5);
});

const topLocationsList = computed(() => {
  if (!dashboardData.value?.top_locations) return [];
  return Object.entries(dashboardData.value.top_locations)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5);
});

const fetchDashboardData = async () => {
  try {
    dashboardData.value = await api.getDashboard();
  } catch (error) {
    console.error('Error fetching dashboard data:', error);
  }
};

onMounted(() => {
  fetchDashboardData();
});
</script>
