<template>
  <div>
    <!-- Species Info Box -->
    <v-alert
      type="info"
      variant="tonal"
      class="mb-4"
      closable
      v-model="showSpeciesInfo"
    >
      <v-alert-title>Artencodes</v-alert-title>
      <div class="mt-2">
        <div class="species-mapping">
          <div v-for="(name, code) in speciesMapping" :key="code" class="species-item">
            <strong>{{ code }}:</strong> {{ name }}
          </div>
        </div>
      </div>
      <template v-slot:append>
        <v-btn
          icon="mdi-information"
          variant="text"
          size="small"
          @click="showSpeciesInfo = !showSpeciesInfo"
        />
      </template>
    </v-alert>

    <!-- Settings Menu -->
    <div class="d-flex justify-end mb-3" v-if="showSettings">
      <v-menu v-model="settingsOpen" :close-on-content-click="false">
        <template v-slot:activator="{ props }">
          <v-btn
            icon="mdi-cog"
            variant="text"
            v-bind="props"
          ></v-btn>
        </template>
        <v-card min-width="300">
          <v-card-title class="text-h6">Tabelleneinstellungen</v-card-title>
          <v-card-text>
            <v-label class="mb-2">Sichtbare Spalten</v-label>
            <v-container class="pa-0">
              <draggable 
                v-model="orderedColumnKeys" 
                item-key="key"
                @start="dragIndex = $event.oldIndex"
                @end="dragIndex = null"
                handle=".drag-handle"
              >
                <template #item="{element: colKey, index}">
                  <v-row 
                    :key="colKey" 
                    class="ma-0 align-center column-item"
                    :class="{ 'dragging': dragIndex === index }"
                  >
                    <v-col cols="auto" class="pa-1">
                      <v-icon class="drag-handle" size="small">mdi-drag</v-icon>
                    </v-col>
                    <v-col class="pa-1">
                      <v-checkbox
                        v-model="selectedSet[colKey as ColumnKey]"
                        :label="availableColumns.find(c => c.key === colKey)?.title || colKey"
                        hide-details
                        density="compact"
                      />
                    </v-col>
                  </v-row>
                </template>
              </draggable>
            </v-container>
            
            <v-divider class="my-3"></v-divider>
            
            <v-checkbox
              v-model="hoverExpandEnabled"
              label="Hover-Erweiterung aktivieren"
              hide-details
              density="compact"
            />
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="primary" variant="text" @click="settingsOpen = false">Schließen</v-btn>
          </v-card-actions>
        </v-card>
      </v-menu>
    </div>

    <v-data-table
      :headers="headers"
      :items="ringings"
      :loading="loading"
      hover
      v-model:page="page"
      v-model:items-per-page="itemsPerPage"
      :items-per-page-options="[10, 25, 50, 100]"
      class="elevation-0 border rounded"
    >
      <template v-slot:item="{ item }">
        <tr
          class="ringing-row"
          :class="{ 'expanded': expandedRow === item.id }"
          @mouseenter="onRowMouseEnter(item.id)"
          @mouseleave="onRowMouseLeave"
          @click="onRowClick($event, item)"
          style="cursor: pointer;"
        >
          <td v-for="col in selectedColumnsOrdered" :key="col">
            <template v-if="col === 'date'">
              {{ formatDate(item.date) }}
            </template>
            <template v-else-if="col === 'ring'">
              {{ item.ring }}
            </template>
            <template v-else-if="col === 'species'">
              {{ resolveSpeciesName(item.species) }}
            </template>
            <template v-else-if="col === 'place'">
              {{ item.place }}
            </template>
            <template v-else-if="col === 'ringer'">
              {{ item.ringer }}
            </template>
            <template v-else-if="col === 'sex'">
              {{ formatSex(item.sex) }}
            </template>
            <template v-else-if="col === 'age'">
              {{ formatAge(item.age) }}
            </template>
            <template v-else-if="col === 'ring_scheme'">
              {{ item.ring_scheme }}
            </template>
            <template v-else-if="col === 'comment'">
              <span v-if="item.comment" class="comment-text">{{ item.comment }}</span>
              <span v-else class="text-medium-emphasis">-</span>
            </template>
            <template v-else>
              {{ formatField(col as string, (item as any)[col]) }}
            </template>
          </td>
          <td class="actions-cell">
            <div class="d-flex align-center justify-center">
              <v-btn
                icon="mdi-open-in-new"
                variant="text"
                color="primary"
                size="small"
                @click.stop="openInNewTab(item)"
                v-tooltip="'In neuem Tab öffnen'"
              />
              <v-btn
                icon="mdi-delete"
                variant="text"
                color="error"
                size="small"
                @click.stop="confirmDelete(item)"
                v-tooltip="'Löschen'"
              />
            </div>
          </td>
        </tr>
      </template>
    </v-data-table>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="showDeleteDialog" max-width="400" width="90%">
      <v-card class="pa-4">
        <v-card-title class="text-h6 px-0">Beringung löschen</v-card-title>
        <v-card-text class="px-0">
          Möchten Sie diese Beringung wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden.
        </v-card-text>
        <v-card-actions class="px-0">
          <v-spacer></v-spacer>
          <v-btn 
            color="grey-darken-1" 
            variant="text" 
            @click="showDeleteDialog = false"
          >
            Abbrechen
          </v-btn>
          <v-btn
            color="error"
            variant="text"
            @click="handleDelete"
            :loading="deleteLoading"
          >
            Löschen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
// import { useRouter } from 'vue-router'; // Not used currently
import { format } from 'date-fns';
import type { Ringing } from '@/types';
import draggable from 'vuedraggable';
import { formatRingingAge } from '@/utils/ageMapping';

const props = withDefaults(defineProps<{
  ringings: Ringing[];
  loading: boolean;
  useStorePagination?: boolean;
  defaultPage?: number;
  defaultItemsPerPage?: number;
  settingsKey?: string;
  showSettings?: boolean;
  defaultColumns?: string[];
  defaultHoverExpand?: boolean;
}>(), {
  useStorePagination: false,
  defaultPage: 1,
  defaultItemsPerPage: 10,
  showSettings: true,
  defaultColumns: () => ['date', 'ring', 'species', 'place', 'ringer', 'sex', 'age'],
  defaultHoverExpand: true
});

const emit = defineEmits<{
  'row-clicked': [ringing: Ringing];
  'deleted': [ring: string];
}>();

// const router = useRouter(); // Not used currently
const showSpeciesInfo = ref(true);
const showDeleteDialog = ref(false);
const deleteLoading = ref(false);
const selectedRinging = ref<Ringing | null>(null);

// Species code to name mapping
const speciesMapping = {
  '01660': 'Kanadagans',
  '01610': 'Graugans',
  '01520': 'Höckerschwan',
  '01700': 'Nilgans',
  '01670': 'Weißwangengans'
} as const;

const allColumnDefs = [
  { key: 'id', title: 'ID' },
  { key: 'date', title: 'Datum' },
  { key: 'ring', title: 'Ring' },
  { key: 'ring_scheme', title: 'Ring Schema' },
  { key: 'species', title: 'Spezies' },
  { key: 'place', title: 'Ort' },
  { key: 'ringer', title: 'Beringer' },
  { key: 'sex', title: 'Geschlecht' },
  { key: 'age', title: 'Alter' },
  { key: 'status', title: 'Status' },
  { key: 'comment', title: 'Kommentar' },
  { key: 'lat', title: 'Breitengrad' },
  { key: 'lon', title: 'Längengrad' },
] as const;

const availableColumns = allColumnDefs;
type ColumnKey = typeof allColumnDefs[number]['key'];
const orderedColumnKeys = ref<ColumnKey[]>([]);
const selectedSet = ref<Record<ColumnKey, boolean>>({} as Record<ColumnKey, boolean>);
const hoverExpandEnabled = ref<boolean>(props.defaultHoverExpand);
const settingsOpen = ref(false);
let dragIndex: number | null = null;

const localPage = ref(props.defaultPage || 1);
const localItemsPerPage = ref(props.defaultItemsPerPage || 10);

const page = computed({
  get: () => localPage.value,
  set: (value) => localPage.value = value
});

const itemsPerPage = computed({
  get: () => localItemsPerPage.value,
  set: (value) => localItemsPerPage.value = value
});

const selectedColumnsOrdered = computed(() => {
  return orderedColumnKeys.value.filter(key => selectedSet.value[key]);
});

const headers = computed(() => {
  const columnHeaders = selectedColumnsOrdered.value.map(key => {
    const colDef = availableColumns.find(c => c.key === key);
    return {
      title: colDef?.title || key,
      key: key,
      sortable: true
    };
  });
  
  // Always add actions column at the end
  columnHeaders.push({
    title: 'Aktionen' as any,
    key: 'actions' as any,
    sortable: false
  });
  
  return columnHeaders;
});

// Initialize column settings
const initializeColumns = () => {
  const savedSettings = props.settingsKey ? localStorage.getItem(`table-settings-${props.settingsKey}`) : null;
  
  if (savedSettings) {
    try {
      const settings = JSON.parse(savedSettings);
      orderedColumnKeys.value = settings.orderedColumns || props.defaultColumns;
      
      // Initialize selectedSet
      selectedSet.value = {} as Record<ColumnKey, boolean>;
      allColumnDefs.forEach(col => {
        selectedSet.value[col.key] = settings.selectedColumns ? 
          settings.selectedColumns.includes(col.key) : 
          props.defaultColumns.includes(col.key);
      });
      
      hoverExpandEnabled.value = settings.hoverExpand !== undefined ? settings.hoverExpand : props.defaultHoverExpand;
    } catch (e) {
      console.warn('Failed to parse saved table settings, using defaults');
      initializeDefaults();
    }
  } else {
    initializeDefaults();
  }
};

const initializeDefaults = () => {
  orderedColumnKeys.value = [...props.defaultColumns] as ColumnKey[];
  selectedSet.value = {} as Record<ColumnKey, boolean>;
  allColumnDefs.forEach(col => {
    selectedSet.value[col.key] = props.defaultColumns.includes(col.key);
  });
};

// Save settings to localStorage
const saveSettings = () => {
  if (!props.settingsKey) return;
  
  const settings = {
    orderedColumns: orderedColumnKeys.value,
    selectedColumns: selectedColumnsOrdered.value,
    hoverExpand: hoverExpandEnabled.value
  };
  
  localStorage.setItem(`table-settings-${props.settingsKey}`, JSON.stringify(settings));
};

// Watch for changes and save
watch([orderedColumnKeys, selectedSet, hoverExpandEnabled], saveSettings, { deep: true });

const resolveSpeciesName = (species: string): string => {
  // If it's a numeric code, try to resolve it
  if (species in speciesMapping) {
    return speciesMapping[species as keyof typeof speciesMapping];
  }
  // Otherwise return the species as is (for entries that already have names)
  return species;
};

const formatDate = (date: string): string => {
  try {
    return format(new Date(date), 'dd.MM.yyyy');
  } catch {
    return date;
  }
};

const formatSex = (sex: number | string): string => {
  if (typeof sex === 'number') {
    switch (sex) {
      case 1: return 'M';
      case 2: return 'W';
      default: return 'U';
    }
  }
  return sex?.toString() || 'U';
};

const formatAge = (age: number | string): string => {
  return formatRingingAge(age, false); // Don't include code for table display
};

const formatField = (_field: string, value: any): string => {
  if (value === null || value === undefined) return '';
  return value.toString();
};

const handleRowClick = (event: Event, ringing: Ringing) => {
  // Check if Ctrl/Cmd key is pressed to open in new tab
  if (event instanceof MouseEvent && (event.ctrlKey || event.metaKey)) {
    const url = `/birds/${ringing.ring}`;
    window.open(url, '_blank');
  } else {
    emit('row-clicked', ringing);
  }
};

const onRowClick = (event: MouseEvent, ringing: Ringing) => {
  handleRowClick(event, ringing);
};

const openInNewTab = (ringing: Ringing) => {
  const url = `/birds/${ringing.ring}`;
  window.open(url, '_blank');
};

const confirmDelete = (ringing: Ringing) => {
  selectedRinging.value = ringing;
  showDeleteDialog.value = true;
};

const handleDelete = async () => {
  if (!selectedRinging.value?.ring) return;
  
  deleteLoading.value = true;
  try {
    emit('deleted', selectedRinging.value.ring);
    showDeleteDialog.value = false;
  } finally {
    deleteLoading.value = false;
  }
};

const expandedRow = ref<string | null>(null);
let expandTimer: ReturnType<typeof setTimeout> | null = null;
let collapseTimer: ReturnType<typeof setTimeout> | null = null;

const onRowMouseEnter = (id: string) => {
  if (!hoverExpandEnabled.value) return;
  
  if (collapseTimer) {
    clearTimeout(collapseTimer);
    collapseTimer = null;
  }
  
  expandTimer = setTimeout(() => {
    expandedRow.value = id;
  }, 300);
};

const onRowMouseLeave = () => {
  if (!hoverExpandEnabled.value) return;
  
  if (expandTimer) {
    clearTimeout(expandTimer);
    expandTimer = null;
  }
  
  collapseTimer = setTimeout(() => {
    expandedRow.value = null;
  }, 100);
};

onMounted(() => {
  initializeColumns();
});
</script>

<style scoped>
.species-mapping {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 8px;
}

.species-item {
  font-size: 0.9em;
}

.ringing-row {
  transition: all 0.2s ease;
}

.ringing-row.expanded {
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.column-item {
  border-radius: 4px;
  transition: background-color 0.2s;
}

.column-item:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.column-item.dragging {
  background-color: rgba(var(--v-theme-primary), 0.1);
}

.drag-handle {
  cursor: grab;
}

.drag-handle:active {
  cursor: grabbing;
}

.actions-cell {
  width: 120px;
  text-align: center;
}

.comment-text {
  max-width: 200px;
  display: inline-block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: top;
}
</style>
