<template>
  <div class="d-flex justify-end mb-2" v-if="showSettings">
    <v-menu v-model="settingsOpen" location="bottom end" :close-on-content-click="false">
      <template #activator="{ props: menuProps }">
        <v-btn
          icon="mdi-cog"
          variant="text"
          size="small"
          v-bind="menuProps"
        >
        </v-btn>
      </template>
      <v-card class="pa-3" min-width="360">
        <div class="text-subtitle-2 mb-2">Spalten und Reihenfolge</div>
        <div class="config-list">
          <div
            v-for="(colKey, idx) in orderedColumnKeys"
            :key="colKey"
            class="config-item d-flex align-center"
            draggable="true"
            @dragstart="onDragStart(idx)"
            @dragover.prevent
            @drop="onDrop(idx)"
          >
            <v-icon icon="mdi-drag" class="me-2" />
            <v-checkbox
              :model-value="!!selectedSet[colKey]"
              @update:modelValue="(val: boolean | null) => toggleSelected(colKey, !!val)"
              :label="columnTitle(colKey)"
              density="compact"
              hide-details
            />
          </div>
          <div class="text-caption text-medium-emphasis mt-1">
            Aktionen sind immer rechts und nicht konfigurierbar
          </div>
        </div>
        <v-divider class="my-2" />
        <v-switch
          v-model="hoverExpandEnabled"
          :label="hoverExpandEnabled ? 'Hover-Erweiterung: An' : 'Hover-Erweiterung: Aus'"
          :color="hoverExpandEnabled ? 'success' : 'error'"
          density="compact"
          hide-details
        />
        <v-card-actions class="px-0 pt-2">
          <v-spacer />
          <v-btn variant="text" @click="settingsOpen = false">Schließen</v-btn>
        </v-card-actions>
      </v-card>
    </v-menu>
  </div>

  <v-data-table
    :headers="headers"
    :items="sightings"
    :loading="loading"
    hover
    v-model:page="page"
    v-model:items-per-page="itemsPerPage"
    :items-per-page-options="[10, 25, 50, 100]"
    class="elevation-0 border rounded"
    @click:row="handleRowClick"
  >
    <template v-slot:item="{ item }">
      <tr
        class="sighting-row"
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
            {{ item.species }}
          </template>
          <template v-else-if="col === 'place'">
            {{ item.place }}
          </template>
          <template v-else-if="col === 'pair'">
            {{ formatPairStatus(item.pair) }}
          </template>
          <template v-else-if="col === 'status'">
            <v-chip
              v-if="item.status"
              :color="getBirdStatusColor(item.status)"
              size="small"
              variant="tonal"
            >
              <v-icon 
                v-if="getBirdStatusIcon(item.status)"
                :icon="getBirdStatusIcon(item.status)"
                size="x-small"
                class="mr-1"
              ></v-icon>
              {{ formatBirdStatus(item.status) }}
            </v-chip>
            <span v-else>-</span>
          </template>
          <template v-else-if="col === 'melder'">
            {{ item.melder }}
          </template>
          <template v-else-if="col === 'melded'">
            <v-btn
              :icon="item.melded ? 'mdi-check-circle' : 'mdi-circle-outline'"
              :color="item.melded ? 'success' : 'grey'"
              variant="text"
              size="small"
              :loading="loadingMeldedStates[item.id]"
              @click.stop="toggleMelded(item)"
              :disabled="loading"
            />
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
      <tr v-if="expandedRow === item.id" class="expanded-row"
        @mouseenter="onExtensionMouseEnter"
        @mouseleave="onExtensionMouseLeave"
      >
        <td :colspan="headers.length">
          <transition name="fade-expand">
            <div class="details-grid expanded-details-row">
              <div v-for="(value, key) in getExtraFields(item)" :key="key" class="detail-field">
                <span class="field-label">{{ fieldLabels[key] || key }}:</span>
                <span class="field-value">{{ formatField(key, value) }}</span>
              </div>
            </div>
          </transition>
        </td>
      </tr>
    </template>
  </v-data-table>

  <!-- Delete Confirmation Dialog -->
  <v-dialog v-model="showDeleteDialog" max-width="400">
    <v-card class="pa-4">
      <v-card-title class="text-h6 px-0">Sichtung löschen</v-card-title>
      <v-card-text class="px-0">
        Möchten Sie diese Sichtung wirklich löschen?
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
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { format } from 'date-fns';
import { formatBirdStatus, getBirdStatusColor, getBirdStatusIcon } from '@/utils/statusUtils';
import type { Sighting } from '@/types';
import { useSightingsStore } from '@/stores/sightings';

const props = withDefaults(defineProps<{
  sightings: Sighting[];
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
  defaultColumns: () => ['date', 'ring', 'species', 'place', 'pair', 'status', 'melder', 'melded'],
  defaultHoverExpand: true
});

const emit = defineEmits<{
  'deleted': [id: string];
  'melded-updated': [sighting: Sighting];
}>();

const router = useRouter();
const showDeleteDialog = ref(false);
const deleteLoading = ref(false);
const selectedSighting = ref<Sighting | null>(null);
const loadingMeldedStates = ref<Record<string, boolean>>({});
const allColumnDefs = [
  { key: 'id', title: 'ID' },
  { key: 'date', title: 'Datum' },
  { key: 'ring', title: 'Ring' },
  { key: 'reading', title: 'Ablesung' },
  { key: 'species', title: 'Spezies' },
  { key: 'place', title: 'Ort' },
  { key: 'area', title: 'Bereich' },
  { key: 'habitat', title: 'Habitat' },
  { key: 'field_fruit', title: 'Feldobst' },
  { key: 'partner', title: 'Partner' },
  { key: 'small_group_size', title: 'Kleine Gruppe' },
  { key: 'large_group_size', title: 'Große Gruppe' },
  { key: 'breed_size', title: 'Brutgröße' },
  { key: 'family_size', title: 'Familiengröße' },
  { key: 'pair', title: 'Familien Status' },
  { key: 'status', title: 'Status' },
  { key: 'melded', title: 'Gemeldet' },
  { key: 'age', title: 'Alter' },
  { key: 'sex', title: 'Geschlecht' },
  { key: 'melder', title: 'Melder' },
  { key: 'comment', title: 'Kommentar' },
  { key: 'lat', title: 'Breitengrad' },
  { key: 'lon', title: 'Längengrad' },
  { key: 'is_exact_location', title: 'Exakter Standort' },
] as const;
const availableColumns = allColumnDefs; // no 'actions' here
type ColumnKey = typeof allColumnDefs[number]['key'];
const orderedColumnKeys = ref<ColumnKey[]>([]);
const selectedSet = ref<Record<ColumnKey, boolean>>({} as Record<ColumnKey, boolean>);
const hoverExpandEnabled = ref<boolean>(props.defaultHoverExpand);
const settingsOpen = ref(false);
let dragIndex: number | null = null;

const store = useSightingsStore();

const localPage = ref(props.defaultPage || 1);
const localItemsPerPage = ref(props.defaultItemsPerPage || 10);

const page = computed({
  get: () => props.useStorePagination ? store.pagination.page : localPage.value,
  set: (value) => {
    if (props.useStorePagination) {
      store.setPagination({ page: value });
    } else {
      localPage.value = value;
    }
  }
});

const itemsPerPage = computed({
  get: () => props.useStorePagination ? store.pagination.itemsPerPage : localItemsPerPage.value,
  set: (value) => {
    if (props.useStorePagination) {
      store.setPagination({ itemsPerPage: value });
    } else {
      localItemsPerPage.value = value;
    }
  }
});

const selectedColumnsOrdered = computed<ColumnKey[]>(() => orderedColumnKeys.value.filter(k => !!selectedSet.value[k]));

const headers = computed(() => {
  const dataHeaders = selectedColumnsOrdered.value.map(col => {
    const def = availableColumns.find(c => c.key === col)!;
    return { title: def.title, key: col, sortable: true };
  });
  return [
    ...dataHeaders,
    { title: 'Aktionen', key: 'actions', sortable: false, width: '100px' }
  ];
});

const formatDate = (date?: string) => {
  return date ? format(new Date(date), 'dd.MM.yyyy') : '';
};

const formatPairStatus = (pair?: string | null) => {
  if (!pair) return '-';
  switch (pair) {
    case 'x':
      return 'Verpaart';
    case 'F':
      return 'Familie';
    case 'S':
      return 'Schule';
    default:
      return pair;
  }
};


const handleRowClick = (event: Event, item: any) => {
  const sighting = item.item;
  const query: Record<string, string> = { from: 'list' };
  
  if (props.useStorePagination) {
    query.page = store.pagination.page.toString();
    query.perPage = store.pagination.itemsPerPage.toString();
  }

  const url = router.resolve({
    path: `/entries/${sighting.id}`,
    query
  }).href;

  // Check if Ctrl/Cmd key is pressed to open in new tab
  if (event instanceof MouseEvent && (event.ctrlKey || event.metaKey)) {
    window.open(url, '_blank');
  } else {
    router.push({
      path: `/entries/${sighting.id}`,
      query
    });
  }
};

const openInNewTab = (sighting: Sighting) => {
  const query: Record<string, string> = { from: 'list' };
  
  if (props.useStorePagination) {
    query.page = store.pagination.page.toString();
    query.perPage = store.pagination.itemsPerPage.toString();
  }

  const url = router.resolve({
    path: `/entries/${sighting.id}`,
    query
  }).href;
  
  window.open(url, '_blank');
};

const confirmDelete = (item: Sighting) => {
  selectedSighting.value = item;
  showDeleteDialog.value = true;
};

const handleDelete = async () => {
  if (!selectedSighting.value?.id) return;
  
  deleteLoading.value = true;
  try {
    emit('deleted', selectedSighting.value.id);
    showDeleteDialog.value = false;
  } finally {
    deleteLoading.value = false;
  }
};

const toggleMelded = async (sighting: Sighting) => {
  if (!sighting.id) return;
  
  loadingMeldedStates.value[sighting.id] = true;
  
  try {
    const updatedSighting = {
      ...sighting,
      melded: !sighting.melded
    };
    
    await store.updateSighting(updatedSighting);
    emit('melded-updated', updatedSighting);
  } catch (error) {
    console.error('Error updating melded status:', error);
  } finally {
    loadingMeldedStates.value[sighting.id] = false;
  }
};

const expandedRow = ref<string | null>(null);
let expandTimer: ReturnType<typeof setTimeout> | null = null;
let collapseTimer: ReturnType<typeof setTimeout> | null = null;

const startExpandTimer = (id: string) => {
  clearExpandTimer();
  expandTimer = setTimeout(() => {
    expandedRow.value = id;
  }, 1000);
};
const clearExpandTimer = () => {
  if (expandTimer) clearTimeout(expandTimer);
  expandTimer = null;
};

const onRowMouseEnter = (id: string) => {
  if (!hoverExpandEnabled.value) return;
  clearCollapseTimer();
  startExpandTimer(id);
};
const onRowMouseLeave = () => {
  if (!hoverExpandEnabled.value) return;
  clearExpandTimer();
  startCollapseTimer();
};
const onExtensionMouseEnter = () => {
  clearCollapseTimer();
};
const onExtensionMouseLeave = () => {
  startCollapseTimer();
};
const startCollapseTimer = () => {
  clearCollapseTimer();
  collapseTimer = setTimeout(() => {
    expandedRow.value = null;
  }, 100);
};
const clearCollapseTimer = () => {
  if (collapseTimer) clearTimeout(collapseTimer);
  collapseTimer = null;
};

const onRowClick = (event: Event, item: Sighting) => {
  // Prevent click if clicking on a button
  if ((event.target as HTMLElement).closest('button')) return;
  handleRowClick(event, { item });
};

const fieldLabels: Record<string, string> = {
  excel_id: 'Excel ID',
  area: 'Bereich',
  habitat: 'Habitat',
  field_fruit: 'Feldobst',
  group_size: 'Gruppengröße',
  small_group_size: 'Kleine Gruppe',
  large_group_size: 'Große Gruppe',
  comment: 'Kommentar',
  lat: 'Breitengrad',
  lon: 'Längengrad',
  is_exact_location: 'Exakter Standort',
  partner: 'Partner',
  age: 'Alter',
  breed_size: 'Brutgröße',
  family_size: 'Familiengröße',
  sex: 'Geschlecht',
  reading: 'Ablesung',
};

const mainFields: (keyof Sighting | 'actions')[] = ['id', 'date', 'ring', 'species', 'place', 'pair', 'status', 'melder', 'melded', 'actions', 'lat', 'lon'];

const getExtraFields = (item: Sighting) => {
  const fields: Record<string, any> = {};
  for (const key in item) {
    if (!mainFields.includes(key as keyof Sighting | 'actions') && (item as any)[key] !== undefined && (item as any)[key] !== null && (item as any)[key] !== '') {
      fields[key] = (item as any)[key];
    }
  }
  return fields;
};

const formatField = (key: string, value: any) => {
  if (key === 'date') return formatDate(value);
  if (key === 'pair') return formatPairStatus(value);
  if (key === 'status') return formatBirdStatus(value);
  if (typeof value === 'boolean') return value ? 'Ja' : 'Nein';
  return value;
};

const columnTitle = (col: ColumnKey) => availableColumns.find(c => c.key === col)?.title || col;
const onDragStart = (index: number) => {
  dragIndex = index;
};
const onDrop = (index: number) => {
  if (dragIndex === null || dragIndex === index) return;
  const arr = [...orderedColumnKeys.value];
  const [moved] = arr.splice(dragIndex, 1);
  arr.splice(index, 0, moved);
  orderedColumnKeys.value = arr as ColumnKey[];
  dragIndex = null;
};

// Persist and restore user settings per view
const SETTINGS_NS = 'sightingsTableSettings:';

const initDefaults = () => {
  const defaults = (props.defaultColumns as ColumnKey[]) || [];
  // Order: defaults first (in given order), then remaining available columns in predefined order
  const rest = availableColumns.map(c => c.key).filter(k => !defaults.includes(k as ColumnKey)) as ColumnKey[];
  orderedColumnKeys.value = [...defaults, ...rest] as ColumnKey[];
  const set: Record<ColumnKey, boolean> = {} as Record<ColumnKey, boolean>;
  orderedColumnKeys.value.forEach(k => { set[k] = defaults.includes(k); });
  selectedSet.value = set;
};

const loadSettings = () => {
  if (!props.settingsKey) return;
  try {
    const raw = localStorage.getItem(SETTINGS_NS + props.settingsKey);
    if (!raw) { initDefaults(); return; }
    const parsed = JSON.parse(raw);
    // Backward compatibility: 'columns' is an ordered array of selected columns
    const selectedFromStorage: string[] | undefined = parsed.selected || parsed.columns;
    const orderFromStorage: string[] | undefined = parsed.order;

    const allKeys = availableColumns.map(c => c.key) as ColumnKey[];
    // Resolve order
    if (Array.isArray(orderFromStorage) && orderFromStorage.length) {
      const filtered = orderFromStorage.filter((k: string) => (allKeys as readonly string[]).includes(k)) as ColumnKey[];
      const missing = allKeys.filter(k => !(filtered as readonly string[]).includes(k as unknown as string)) as ColumnKey[];
      orderedColumnKeys.value = [...(filtered as ColumnKey[]), ...(missing as ColumnKey[])];
    } else {
      initDefaults();
    }

    // Resolve selection
    const set: Record<ColumnKey, boolean> = {} as Record<ColumnKey, boolean>;
    orderedColumnKeys.value.forEach(k => { set[k] = false; });
    if (Array.isArray(selectedFromStorage)) {
      selectedFromStorage.forEach((k: string) => {
        if ((allKeys as readonly string[]).includes(k)) set[k as ColumnKey] = true;
      });
    } else {
      // Fallback to defaults
      (props.defaultColumns as ColumnKey[]).forEach(k => { set[k] = true; });
    }
    selectedSet.value = set;

    if (typeof parsed.hoverExpand === 'boolean') {
      hoverExpandEnabled.value = parsed.hoverExpand;
    }
  } catch (e) {
    console.warn('Failed to load table settings', e);
    initDefaults();
  }
};
const persistSettings = () => {
  if (!props.settingsKey) return;
  try {
    const selected = orderedColumnKeys.value.filter(k => !!selectedSet.value[k]);
    localStorage.setItem(
      SETTINGS_NS + props.settingsKey,
      JSON.stringify({ order: orderedColumnKeys.value, selected, hoverExpand: hoverExpandEnabled.value })
    );
  } catch (e) {
    console.warn('Failed to persist table settings', e);
  }
};

onMounted(loadSettings);
watch([orderedColumnKeys, selectedSet, hoverExpandEnabled, () => props.settingsKey], persistSettings, { deep: true });

const toggleSelected = (key: ColumnKey, val: boolean) => {
  selectedSet.value[key] = val;
};
</script>

<style scoped>
.v-data-table {
  border: 1px solid #E0E0E0;
  border-radius: 8px;
}

.v-data-table :deep(th) {
  font-weight: 600 !important;
  color: rgba(0, 0, 0, 0.87) !important;
  background: #FAFAFA;
}

.v-data-table :deep(tr:hover) {
  background: #FAFAFA !important;
}

.v-btn.v-btn--loading {
  min-width: 36px;
  min-height: 36px;
}

.sighting-row {
  transition: box-shadow 0.2s, background 0.2s;
}
.sighting-row.expanded {
  box-shadow: 0 4px 24px 0 rgba(60,60,60,0.08);
  background: #e3f2fd !important;
  border-left: 4px solid #1976d2;
}
.expanded-row {
  background: #e3f2fd !important;
  border-left: 4px solid #1976d2;
}
.v-data-table :deep(tr.sighting-row.expanded:hover),
.v-data-table :deep(tr.sighting-row.expanded),
.v-data-table :deep(tr.expanded-row:hover),
.v-data-table :deep(tr.expanded-row) {
  background: #e3f2fd !important;
}
.expanded-details-row {
  padding: 16px 0 8px 0;
  background: none;
  border-radius: 0;
  box-shadow: none;
  margin: 0;
}
.details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px 24px;
}
.detail-field {
  display: flex;
  flex-direction: column;
  font-size: 0.97rem;
}
.field-label {
  font-weight: 600;
  color: #888;
  margin-bottom: 2px;
}
.field-value {
  color: #222;
}
.fade-expand-enter-active, .fade-expand-leave-active {
  transition: opacity 0.3s, max-height 0.3s;
}
.fade-expand-enter-from, .fade-expand-leave-to {
  opacity: 0;
  max-height: 0;
}
.fade-expand-enter-to, .fade-expand-leave-from {
  opacity: 1;
  max-height: 400px;
}
</style>