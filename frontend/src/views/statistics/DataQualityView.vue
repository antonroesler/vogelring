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
                v-if="isLoading"
                indeterminate
                color="primary"
                class="ma-4"
              ></v-progress-circular>
              
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
                <v-chart class="chart" :option="fieldCompletenessOption" autoresize></v-chart>
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
                  v-for="issue in dataQualityIssues" 
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
                :items="fieldAnalysis"
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
              @deleted="handleSightingDeleted"
            ></sightings-table>
            
            <v-alert v-else type="info" variant="tonal">
              Keine problematischen Einträge gefunden.
            </v-alert>
          </v-card-text>
        </v-card>
      </v-dialog>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
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
const isLoading = ref(true);
const showIssueDialog = ref(false);
const selectedIssue = ref<DataQualityIssue | null>(null);
const issueEntries = ref<Sighting[]>([]);

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

const fieldAnalysis = computed((): FieldAnalysis[] => {
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
    { field: 'pair', label: 'Paar-Status' },
    { field: 'status', label: 'Status' },
    { field: 'age', label: 'Alter' },
    { field: 'sex', label: 'Geschlecht' },
    { field: 'melder', label: 'Melder' },
    { field: 'comment', label: 'Kommentar' },
    { field: 'lat', label: 'Breitengrad' },
    { field: 'lon', label: 'Längengrad' }
  ];

  return fields.map(({ field, label }) => {
    const nullCount = store.sightings.filter(s => {
      const value = (s as any)[field];
      return value === null || value === undefined || value === '';
    }).length;
    
    const totalCount = store.sightings.length;
    const completeness = totalCount > 0 ? ((totalCount - nullCount) / totalCount) * 100 : 0;

    return {
      field,
      label,
      nullCount,
      completeness,
      totalCount
    };
  });
});

const dataQualityIssues = computed((): DataQualityIssue[] => {
  const issues: DataQualityIssue[] = [
    {
      id: 'future-dates',
      title: 'Zukünftige Daten',
      description: 'Sichtungen mit Datum in der Zukunft',
      severity: 'high',
      icon: 'mdi-calendar-alert',
      count: 0,
      filter: (sightings) => sightings.filter(s => {
        if (!s.date) return false;
        const sightingDate = new Date(s.date);
        const today = new Date();
        today.setHours(23, 59, 59, 999); // End of today
        return sightingDate > today;
      })
    },
    {
      id: 'invalid-coordinates',
      title: 'Ungültige Koordinaten',
      description: 'Sichtungen mit Koordinaten außerhalb des erwarteten Bereichs',
      severity: 'medium',
      icon: 'mdi-map-marker-alert',
      count: 0,
      filter: (sightings) => sightings.filter(s => {
        if (!s.lat || !s.lon) return false;
        // Rough bounds for Central Europe (Germany area)
        const minLat = 47, maxLat = 55;
        const minLon = 5, maxLon = 15;
        return s.lat < minLat || s.lat > maxLat || s.lon < minLon || s.lon > maxLon;
      })
    },
    {
      id: 'missing-coordinates',
      title: 'Fehlende Koordinaten',
      description: 'Sichtungen ohne Standortdaten',
      severity: 'medium',
      icon: 'mdi-map-marker-off',
      count: 0,
      filter: (sightings) => sightings.filter(s => !s.lat || !s.lon)
    },
    {
      id: 'invalid-partners',
      title: 'Ungültige Partner',
      description: 'Partner-Ringe die nicht im System existieren (außer UB/unberingt)',
      severity: 'medium',
      icon: 'mdi-account-alert',
      count: 0,
      filter: (sightings) => {
        const allRings = new Set(sightings.map(s => s.ring).filter(Boolean));
        return sightings.filter(s => {
          if (!s.partner) return false;
          const partner = s.partner.toLowerCase();
          // Allow "UB", "unberingt", "Unberingt" as valid unringed partners
          if (partner === 'ub' || partner === 'unberingt') return false;
          return !allRings.has(s.partner);
        });
      }
    },
    {
      id: 'conflicting-species',
      title: 'Widersprüchliche Arten',
      description: 'Ringe mit unterschiedlichen Artenbestimmungen',
      severity: 'high',
      icon: 'mdi-bird',
      count: 0,
      filter: (sightings) => {
        const ringSpecies = new Map<string, Set<string>>();
        
        // Group species by ring
        sightings.forEach(s => {
          if (s.ring && s.species) {
            if (!ringSpecies.has(s.ring)) {
              ringSpecies.set(s.ring, new Set());
            }
            ringSpecies.get(s.ring)!.add(s.species);
          }
        });
        
        // Find rings with multiple species
        const conflictingRings = new Set<string>();
        ringSpecies.forEach((species, ring) => {
          if (species.size > 1) {
            conflictingRings.add(ring);
          }
        });
        
        return sightings.filter(s => s.ring && conflictingRings.has(s.ring));
      }
    },
    {
      id: 'extreme-group-sizes',
      title: 'Extreme Gruppengrößen',
      description: 'Ungewöhnlich große Gruppenwerte (>1000)',
      severity: 'low',
      icon: 'mdi-account-group-outline',
      count: 0,
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
      count: 0,
      filter: (sightings) => {
        const seen = new Set<string>();
        const duplicates = new Set<string>();
        
        sightings.forEach(s => {
          if (s.ring && s.date && s.place) {
            const key = `${s.ring}-${s.date}-${s.place}`;
            if (seen.has(key)) {
              duplicates.add(s.id);
            } else {
              seen.add(key);
            }
          }
        });
        
        // Also mark the original entries as duplicates
        sightings.forEach(s => {
          if (s.ring && s.date && s.place) {
            const key = `${s.ring}-${s.date}-${s.place}`;
            const matchingEntries = sightings.filter(other => 
              other.ring === s.ring && 
              other.date === s.date && 
              other.place === s.place
            );
            if (matchingEntries.length > 1) {
              duplicates.add(s.id);
            }
          }
        });
        
        return sightings.filter(s => duplicates.has(s.id));
      }
    }
  ];

  // Calculate counts for each issue
  issues.forEach(issue => {
    issue.count = issue.filter(store.sightings).length;
  });

  return issues.sort((a, b) => b.count - a.count);
});

const fieldCompletenessOption = computed(() => {
  const data = fieldAnalysis.value
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
});

const getCompletenessColor = (completeness: number): string => {
  if (completeness >= 90) return '#4CAF50'; // Green
  if (completeness >= 70) return '#FF9800'; // Orange
  if (completeness >= 50) return '#FF5722'; // Red-orange
  return '#F44336'; // Red
};

const showIssueDetails = (issue: DataQualityIssue) => {
  selectedIssue.value = issue;
  issueEntries.value = issue.filter(store.sightings);
  showIssueDialog.value = true;
};

const showFieldIssues = (field: string) => {
  const fieldLabel = fieldAnalysis.value.find(f => f.field === field)?.label || field;
  
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
  // Refresh the current issue entries after deletion
  if (selectedIssue.value) {
    issueEntries.value = selectedIssue.value.filter(store.sightings);
  }
};

onMounted(async () => {
  if (!store.initialized) {
    await store.fetchSightings();
  }
  isLoading.value = false;
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