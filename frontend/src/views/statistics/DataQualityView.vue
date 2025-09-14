<template>
  <v-card class="mt-4">
    <v-card-text>
      <v-row>
        <!-- Field Completeness Overview -->
        <v-col cols="12">
          <v-card>
            <v-card-title class="d-flex align-center">
              <v-icon icon="mdi-chart-bar" class="me-2"></v-icon>
              Datenqualität Übersicht
            </v-card-title>
            <v-card-text>
              <v-progress-circular
                v-if="store.loading || isProcessing"
                indeterminate
                color="primary"
                class="ma-4"
              ></v-progress-circular>
              
              <div v-if="store.loading || isProcessing" class="text-center mt-2">
                <div class="text-subtitle-1">
                  {{ store.loading ? 'Lade Daten...' : 'Analysiere Datenqualität...' }}
                </div>
              </div>
              
              <div v-else>
                <!-- Summary Cards -->
                <v-row class="mb-4">
                  <v-col cols="12" md="3">
                    <v-card color="primary" variant="tonal">
                      <v-card-text class="text-center">
                        <div class="text-h4 mb-2">{{ totalSightings }}</div>
                        <div class="text-subtitle-1">Gesamt Sichtungen</div>
                      </v-card-text>
                    </v-card>
                  </v-col>
                  <v-col cols="12" md="3">
                    <v-card color="success" variant="tonal">
                      <v-card-text class="text-center">
                        <div class="text-h4 mb-2">{{ completeIdentifications }}</div>
                        <div class="text-subtitle-1">Vollständige IDs</div>
                        <div class="text-caption">Ring + Spezies</div>
                      </v-card-text>
                    </v-card>
                  </v-col>
                  <v-col cols="12" md="3">
                    <v-card color="warning" variant="tonal">
                      <v-card-text class="text-center">
                        <div class="text-h4 mb-2">{{ partialIdentifications }}</div>
                        <div class="text-subtitle-1">Teilweise IDs</div>
                        <div class="text-caption">Nur Ring oder Spezies</div>
                      </v-card-text>
                    </v-card>
                  </v-col>
                  <v-col cols="12" md="3">
                    <v-card color="error" variant="tonal">
                      <v-card-text class="text-center">
                        <div class="text-h4 mb-2">{{ noIdentification }}</div>
                        <div class="text-subtitle-1">Keine ID</div>
                        <div class="text-caption">Weder Ring noch Spezies</div>
                      </v-card-text>
                    </v-card>
                  </v-col>
                </v-row>

                <!-- Field Completeness Chart -->
                <v-chart class="chart" :option="fieldCompletenessOptionData" autoresize></v-chart>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

                        <!-- Data Quality Issues -->
        <v-col cols="12">
          <v-card>
            <v-card-title class="d-flex align-center">
              <v-icon icon="mdi-alert-circle" class="me-2"></v-icon>
              Datenqualitätsprobleme
            </v-card-title>
            <v-card-text>
              <v-row>
                <v-col 
                  v-for="issue in dataQualityIssuesData" 
                  :key="issue.id"
                  cols="12" 
                  md="6" 
                  lg="4"
                >
                  <v-card 
                    :color="issue.severity === 'high' ? 'error' : issue.severity === 'medium' ? 'warning' : 'info'"
                    variant="tonal"
                    class="issue-card"
                    @click="showIssueDetails(issue)"
                    style="cursor: pointer"
                  >
                    <v-card-text>
                      <div class="d-flex align-center mb-2">
                        <v-icon :icon="issue.icon" class="me-2"></v-icon>
                        <span class="text-subtitle-1 font-weight-medium">{{ issue.title }}</span>
                      </div>
                      <div class="text-h5 mb-1">{{ issue.count }}</div>
                      <div class="text-caption">{{ issue.description }}</div>
                      <v-progress-linear
                        :model-value="(issue.count / totalSightings) * 100"
                        :color="issue.severity === 'high' ? 'error' : issue.severity === 'medium' ? 'warning' : 'info'"
                        height="4"
                        class="mt-2"
                      ></v-progress-linear>
                      <div class="text-caption mt-1">
                        {{ ((issue.count / totalSightings) * 100).toFixed(1) }}% aller Sichtungen
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Detailed Field Analysis -->
        <v-col cols="12">
          <v-card>
            <v-card-title class="d-flex align-center">
              <v-icon icon="mdi-table-search" class="me-2"></v-icon>
              Detaillierte Feldanalyse
            </v-card-title>
            <v-card-text>
              <v-data-table
                :headers="fieldHeaders"
                :items="fieldAnalysisData"
                :items-per-page="15"
                class="elevation-0"
              >
                <template v-slot:item.completeness="{ item }">
                  <div class="d-flex align-center">
                    <v-progress-linear
                      :model-value="item.completeness"
                      :color="getCompletenessColor(item.completeness)"
                      height="8"
                      class="flex-grow-1 me-2"
                      style="min-width: 100px"
                    ></v-progress-linear>
                    <span class="text-caption">{{ item.completeness.toFixed(1) }}%</span>
                  </div>
                </template>
                <template v-slot:item.actions="{ item }">
                  <v-btn
                    v-if="item.nullCount > 0"
                    icon="mdi-eye"
                    size="small"
                    variant="text"
                    @click="showFieldIssues(item.field)"
                    v-tooltip="'Problematische Einträge anzeigen'"
                  ></v-btn>
                </template>
              </v-data-table>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Issue Details Dialog -->
      <v-dialog v-model="showIssueDialog" max-width="1200">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon :icon="selectedIssue?.icon" class="me-2"></v-icon>
            {{ selectedIssue?.title }}
            <v-spacer></v-spacer>
            <v-btn icon="mdi-close" variant="text" @click="showIssueDialog = false"></v-btn>
          </v-card-title>
          <v-card-text>
            <p class="mb-4">{{ selectedIssue?.description }}</p>
            
            <sightings-table
              v-if="issueEntries.length > 0"
              :sightings="issueEntries"
              :loading="false"
              :use-store-pagination="false"
              :default-page="1"
              :default-items-per-page="10"
               :show-settings="true"
               :settings-key="`data-quality:${selectedIssue?.id || 'unknown'}`"
               :default-columns="['date','ring','species','place','pair','status','melder','melded']"
               :default-hover-expand="true"
              @deleted="handleSightingDeleted"
            ></sightings-table>
            
            <v-alert v-else type="info" variant="tonal">
              Keine problematischen Einträge gefunden.
            </v-alert>
          </v-card-text>
        </v-card>
      </v-dialog>

      <v-snackbar
        v-model="showDeleteSnackbar"
        color="success"
      >
        Sichtung erfolgreich gelöscht
      </v-snackbar>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue';
import { useSightingsStore } from '@/stores/sightings';
import type { Sighting } from '@/types';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { BarChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import SightingsTable from '@/components/sightings/SightingsTable.vue';

use([
  CanvasRenderer,
  BarChart,
  GridComponent,
  TooltipComponent,
  LegendComponent
]);

const store = useSightingsStore();
const isProcessing = ref(false);
const showIssueDialog = ref(false);
const selectedIssue = ref<DataQualityIssue | null>(null);
const issueEntries = ref<Sighting[]>([]);
const showDeleteSnackbar = ref(false);

// Convert heavy computed properties to refs for async processing
const fieldAnalysisData = ref<FieldAnalysis[]>([]);
const dataQualityIssuesData = ref<DataQualityIssue[]>([]);
const fieldCompletenessOptionData = ref({});

interface FieldAnalysis {
  field: string;
  label: string;
  nullCount: number;
  completeness: number;
  totalCount: number;
}

interface DataQualityIssue {
  id: string;
  title: string;
  description: string;
  count: number;
  severity: 'high' | 'medium' | 'low';
  icon: string;
  filter: (sightings: Sighting[]) => Sighting[];
}

const fieldHeaders = [
  { title: 'Feld', key: 'label', sortable: true },
  { title: 'Vollständigkeit', key: 'completeness', sortable: true },
  { title: 'Fehlende Werte', key: 'nullCount', sortable: true },
  { title: 'Gesamt', key: 'totalCount', sortable: true },
  { title: 'Aktionen', key: 'actions', sortable: false }
];

const totalSightings = computed(() => store.sightings.length);

const completeIdentifications = computed(() => {
  return store.sightings.filter(s => s.ring && s.species).length;
});

const partialIdentifications = computed(() => {
  return store.sightings.filter(s => (s.ring && !s.species) || (!s.ring && s.species)).length;
});

const noIdentification = computed(() => {
  return store.sightings.filter(s => !s.ring && !s.species).length;
});







const getCompletenessColor = (completeness: number): string => {
  if (completeness >= 90) return '#4CAF50'; // Green
  if (completeness >= 70) return '#FF9800'; // Orange
  if (completeness >= 50) return '#FF5722'; // Red-orange
  return '#F44336'; // Red
};

// Optimized single-pass field analysis
const processFieldAnalysis = async (): Promise<FieldAnalysis[]> => {
  const fields = [
    { field: 'species', label: 'Spezies' },
    { field: 'ring', label: 'Ring' },
    { field: 'reading', label: 'Ablesung' },
    { field: 'date', label: 'Datum' },
    { field: 'place', label: 'Ort' },
    { field: 'area', label: 'Bereich' },
    { field: 'habitat', label: 'Habitat' },
    { field: 'field_fruit', label: 'Feldfrucht' },
    { field: 'partner', label: 'Partner' },
    { field: 'small_group_size', label: 'Kleine Gruppe' },
    { field: 'large_group_size', label: 'Große Gruppe' },
    { field: 'breed_size', label: 'Brutgröße' },
    { field: 'family_size', label: 'Familiengröße' },
    { field: 'pair', label: 'Familien Status' },
    { field: 'status', label: 'Status' },
    { field: 'age', label: 'Alter' },
    { field: 'sex', label: 'Geschlecht' },
    { field: 'melder', label: 'Melder' },
    { field: 'comment', label: 'Kommentar' },
    { field: 'lat', label: 'Breitengrad' },
    { field: 'lon', label: 'Längengrad' }
  ];

  // Initialize counters for all fields
  const nullCounts: Record<string, number> = {};
  fields.forEach(({ field }) => {
    nullCounts[field] = 0;
  });

  const totalCount = store.sightings.length;
  let processedCount = 0;

  // Single pass through all sightings to count nulls for all fields
  for (const sighting of store.sightings) {
    fields.forEach(({ field }) => {
      const value = (sighting as any)[field];
      if (value === null || value === undefined || value === '') {
        nullCounts[field]++;
      }
    });

    processedCount++;
    // Yield control every 200 sightings to keep UI responsive
    if (processedCount % 200 === 0) {
      await new Promise(resolve => setTimeout(resolve, 1));
    }
  }

  // Build results from the collected counts
  return fields.map(({ field, label }) => {
    const nullCount = nullCounts[field];
    const completeness = totalCount > 0 ? ((totalCount - nullCount) / totalCount) * 100 : 0;

    return {
      field,
      label,
      nullCount,
      completeness,
      totalCount
    };
  });
};

// Optimized single-pass data quality analysis
const processDataQualityIssues = async (): Promise<DataQualityIssue[]> => {
  // Pre-compute data needed for analysis
  const today = new Date();
  today.setHours(23, 59, 59, 999);
  const allRings = new Set(store.sightings.map(s => s.ring).filter(Boolean));
  const ringSpecies = new Map<string, Set<string>>();
  const keyToIds = new Map<string, string[]>();
  
  // Counters for each issue type
  const counts = {
    'future-dates': 0,
    'invalid-coordinates': 0,
    'missing-coordinates': 0,
    'invalid-partners': 0,
    'conflicting-species': 0,
    'extreme-group-sizes': 0,
    'duplicate-entries': 0
  };

  let processedCount = 0;

  // Single pass through all sightings to check all conditions
  for (const s of store.sightings) {
    // Future dates check
    if (s.date) {
      const sightingDate = new Date(s.date);
      if (sightingDate > today) {
        counts['future-dates']++;
      }
    }

    // Coordinates checks
    if (!s.lat || !s.lon) {
      counts['missing-coordinates']++;
    } else {
      // Invalid coordinates (outside Central Europe bounds)
      const minLat = 47, maxLat = 55, minLon = 5, maxLon = 15;
      if (s.lat < minLat || s.lat > maxLat || s.lon < minLon || s.lon > maxLon) {
        counts['invalid-coordinates']++;
      }
    }

    // Invalid partners check
    if (s.partner) {
      const partner = s.partner.toLowerCase();
      if (partner !== 'ub' && partner !== 'unberingt' && !allRings.has(s.partner)) {
        counts['invalid-partners']++;
      }
    }

    // Collect data for conflicting species analysis
    if (s.ring && s.species) {
      if (!ringSpecies.has(s.ring)) {
        ringSpecies.set(s.ring, new Set());
      }
      ringSpecies.get(s.ring)!.add(s.species);
    }

    // Extreme group sizes check
    if ((s.small_group_size && s.small_group_size > 1000) ||
        (s.large_group_size && s.large_group_size > 1000) ||
        (s.breed_size && s.breed_size > 100) ||
        (s.family_size && s.family_size > 100)) {
      counts['extreme-group-sizes']++;
    }

    // Collect data for duplicates analysis
    if (s.ring && s.date && s.place) {
      const key = `${s.ring}-${s.date}-${s.place}`;
      if (!keyToIds.has(key)) {
        keyToIds.set(key, []);
      }
      keyToIds.get(key)!.push(s.id);
    }

    processedCount++;
    // Yield control every 500 sightings to keep UI responsive
    if (processedCount % 500 === 0) {
      await new Promise(resolve => setTimeout(resolve, 1));
    }
  }

  // Process conflicting species - count during main pass
  const conflictingRings = new Set<string>();
  ringSpecies.forEach((species, ring) => {
    if (species.size > 1) {
      conflictingRings.add(ring);
    }
  });
  
  // Count conflicting species sightings
  for (const s of store.sightings) {
    if (s.ring && conflictingRings.has(s.ring)) {
      counts['conflicting-species']++;
    }
  }

  // Process duplicates
  const duplicateIds = new Set<string>();
  keyToIds.forEach(ids => {
    if (ids.length > 1) {
      ids.forEach(id => duplicateIds.add(id));
      counts['duplicate-entries'] += ids.length;
    }
  });

  // Create issues with pre-calculated counts and optimized filters
  const issues: DataQualityIssue[] = [
    {
      id: 'future-dates',
      title: 'Zukünftige Daten',
      description: 'Sichtungen mit Datum in der Zukunft',
      severity: 'high',
      icon: 'mdi-calendar-alert',
      count: counts['future-dates'],
      filter: (sightings) => sightings.filter(s => {
        if (!s.date) return false;
        const sightingDate = new Date(s.date);
        return sightingDate > today;
      })
    },
    {
      id: 'invalid-coordinates',
      title: 'Ungültige Koordinaten',
      description: 'Sichtungen mit Koordinaten außerhalb des erwarteten Bereichs',
      severity: 'medium',
      icon: 'mdi-map-marker-alert',
      count: counts['invalid-coordinates'],
      filter: (sightings) => sightings.filter(s => {
        if (!s.lat || !s.lon) return false;
        const minLat = 47, maxLat = 55, minLon = 5, maxLon = 15;
        return s.lat < minLat || s.lat > maxLat || s.lon < minLon || s.lon > maxLon;
      })
    },
    {
      id: 'missing-coordinates',
      title: 'Fehlende Koordinaten',
      description: 'Sichtungen ohne Standortdaten',
      severity: 'medium',
      icon: 'mdi-map-marker-off',
      count: counts['missing-coordinates'],
      filter: (sightings) => sightings.filter(s => !s.lat || !s.lon)
    },
    {
      id: 'invalid-partners',
      title: 'Ungültige Partner',
      description: 'Partner-Ringe die nicht im System existieren (außer UB/unberingt)',
      severity: 'medium',
      icon: 'mdi-account-alert',
      count: counts['invalid-partners'],
      filter: (sightings) => sightings.filter(s => {
        if (!s.partner) return false;
        const partner = s.partner.toLowerCase();
        if (partner === 'ub' || partner === 'unberingt') return false;
        return !allRings.has(s.partner);
      })
    },
    {
      id: 'conflicting-species',
      title: 'Widersprüchliche Arten',
      description: 'Ringe mit unterschiedlichen Artenbestimmungen',
      severity: 'high',
      icon: 'mdi-bird',
      count: counts['conflicting-species'],
      filter: (sightings) => sightings.filter(s => s.ring && conflictingRings.has(s.ring))
    },
    {
      id: 'extreme-group-sizes',
      title: 'Extreme Gruppengrößen',
      description: 'Ungewöhnlich große Gruppenwerte (>1000)',
      severity: 'low',
      icon: 'mdi-account-group-outline',
      count: counts['extreme-group-sizes'],
      filter: (sightings) => sightings.filter(s => {
        return (s.small_group_size && s.small_group_size > 1000) ||
               (s.large_group_size && s.large_group_size > 1000) ||
               (s.breed_size && s.breed_size > 100) ||
               (s.family_size && s.family_size > 100);
      })
    },
    {
      id: 'duplicate-entries',
      title: 'Mögliche Duplikate',
      description: 'Sichtungen mit identischem Ring, Datum und Ort',
      severity: 'medium',
      icon: 'mdi-content-duplicate',
      count: counts['duplicate-entries'],
      filter: (sightings) => sightings.filter(s => duplicateIds.has(s.id))
    }
  ];

  return issues.sort((a, b) => b.count - a.count);
};

const processFieldCompletenessChart = async (fieldAnalysis: FieldAnalysis[]) => {
  const data = fieldAnalysis
    .sort((a, b) => a.completeness - b.completeness)
    .slice(0, 15); // Show top 15 fields

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params: any) => {
        const item = params[0];
        const field = data[item.dataIndex];
        return `${field.label}<br/>
                Vollständigkeit: ${field.completeness.toFixed(1)}%<br/>
                Fehlende Werte: ${field.nullCount}<br/>
                Gesamt: ${field.totalCount}`;
      }
    },
    grid: {
      left: '15%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      max: 100,
      axisLabel: {
        formatter: '{value}%'
      }
    },
    yAxis: {
      type: 'category',
      data: data.map(item => item.label),
      axisLabel: {
        interval: 0
      }
    },
    series: [{
      type: 'bar',
      data: data.map(item => ({
        value: item.completeness,
        itemStyle: {
          color: getCompletenessColor(item.completeness)
        }
      })),
      barWidth: '60%'
    }]
  };
};

const showIssueDetails = (issue: DataQualityIssue) => {
  selectedIssue.value = issue;
  issueEntries.value = issue.filter(store.sightings);
  showIssueDialog.value = true;
};

const showFieldIssues = (field: string) => {
  const fieldLabel = fieldAnalysisData.value.find(f => f.field === field)?.label || field;
  
  selectedIssue.value = {
    id: `field-${field}`,
    title: `Fehlende Werte: ${fieldLabel}`,
    description: `Sichtungen ohne Wert für das Feld "${fieldLabel}"`,
    count: 0,
    severity: 'medium',
    icon: 'mdi-database-alert',
    filter: (sightings) => sightings.filter(s => {
      const value = (s as any)[field];
      return value === null || value === undefined || value === '';
    })
  };
  
  issueEntries.value = selectedIssue.value.filter(store.sightings);
  showIssueDialog.value = true;
};

const handleSightingDeleted = async (id: string) => {
  try {
    await store.deleteSighting(id);
    showDeleteSnackbar.value = true;
  } catch (error) {
    console.error('Error deleting sighting:', error);
  } finally {
    if (selectedIssue.value) {
      issueEntries.value = selectedIssue.value.filter(store.sightings);
    }
    // Refresh issue counts to keep the overview in sync
    dataQualityIssuesData.value = await processDataQualityIssues();
  }
};

const processData = async () => {
  isProcessing.value = true;
  
  try {
    // Allow UI to update and spinner to start animating
    await new Promise(resolve => requestAnimationFrame(resolve));
    
    // Process field analysis
    fieldAnalysisData.value = await processFieldAnalysis();
    
    // Yield to browser to keep spinner animated
    await new Promise(resolve => requestAnimationFrame(resolve));
    
    // Process data quality issues
    dataQualityIssuesData.value = await processDataQualityIssues();
    
    // Yield to browser to keep spinner animated
    await new Promise(resolve => requestAnimationFrame(resolve));
    
    // Process chart data
    fieldCompletenessOptionData.value = await processFieldCompletenessChart(fieldAnalysisData.value);
    
  } finally {
    isProcessing.value = false;
  }
};

// Watch for when store finishes loading to start processing
watch(() => store.loading, async (isLoading, wasLoading) => {
  // When loading transitions from true to false and we have data
  if (wasLoading && !isLoading && store.sightings.length > 0 && fieldAnalysisData.value.length === 0) {
    await new Promise(resolve => requestAnimationFrame(resolve));
    await processData();
  }
});

onMounted(async () => {
  if (!store.initialized) {
    await store.fetchSightings();
  }
  
  // Only process data if sightings are available and not already loading
  if (store.sightings.length > 0 && !store.loading && fieldAnalysisData.value.length === 0) {
    // Defer processing to next tick to allow loading state to show
    await nextTick();
    // Use requestAnimationFrame to ensure spinner starts animating
    await new Promise(resolve => requestAnimationFrame(resolve));
    await processData();
  }
});
</script>

<style scoped>
.chart {
  height: 400px;
}

.issue-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.issue-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
</style>