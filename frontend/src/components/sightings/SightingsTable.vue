<template>
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
    <template v-slot:item="{ item, index }">
      <tr
        class="sighting-row"
        :class="{ 'expanded': expandedRow === item.id }"
        @mouseenter="onRowMouseEnter(item.id)"
        @mouseleave="onRowMouseLeave"
        @click="onRowClick($event, item)"
        style="cursor: pointer;"
      >
        <td>{{ formatDate(item.date) }}</td>
        <td>{{ item.ring }}</td>
        <td>{{ item.species }}</td>
        <td>{{ item.place }}</td>
        <td>{{ formatPairStatus(item.pair) }}</td>
        <td>{{ formatStatus(item.status) }}</td>
        <td>{{ item.melder }}</td>
        <td>
          <v-btn
            :icon="item.melded ? 'mdi-check-circle' : 'mdi-circle-outline'"
            :color="item.melded ? 'success' : 'grey'"
            variant="text"
            size="small"
            :loading="loadingMeldedStates[item.id]"
            @click.stop="toggleMelded(item)"
            :disabled="loading"
          ></v-btn>
        </td>
        <td>
          <div class="d-flex align-center justify-center">
            <v-btn
              icon="mdi-open-in-new"
              variant="text"
              color="primary"
              size="small"
              @click.stop="openInNewTab(item)"
              v-tooltip="'In neuem Tab öffnen'"
            ></v-btn>
            <v-btn
              icon="mdi-delete"
              variant="text"
              color="error"
              size="small"
              @click.stop="confirmDelete(item)"
              v-tooltip="'Löschen'"
            ></v-btn>
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
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { format } from 'date-fns';
import type { Sighting } from '@/types';
import * as api from '@/api';
import { useSightingsStore } from '@/stores/sightings';

const props = defineProps<{
  sightings: Sighting[];
  loading: boolean;
  useStorePagination?: boolean;
  defaultPage?: number;
  defaultItemsPerPage?: number;
}>();

const emit = defineEmits<{
  'deleted': [id: string];
  'melded-updated': [sighting: Sighting];
}>();

const router = useRouter();
const showDeleteDialog = ref(false);
const deleteLoading = ref(false);
const selectedSighting = ref<Sighting | null>(null);
const loadingMeldedStates = ref<Record<string, boolean>>({});

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

const headers = [
  { title: 'Datum', key: 'date', sortable: true },
  { title: 'Ring', key: 'ring', sortable: true },
  { title: 'Spezies', key: 'species', sortable: true },
  { title: 'Ort', key: 'place', sortable: true },
  { title: 'Paar-Status', key: 'pair', sortable: true },
  { title: 'Status', key: 'status', sortable: true },
  { title: 'Melder', key: 'melder', sortable: true },
  { title: 'Gemeldet', key: 'melded', sortable: true },
  { title: 'Aktionen', key: 'actions', sortable: false, width: '100px' }
];

const formatDate = (date?: string) => {
  return date ? format(new Date(date), 'dd.MM.yyyy') : '';
};

const formatPairStatus = (pair?: string) => {
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

const formatStatus = (status?: string) => {
  if (!status) return '-';
  switch (status) {
    case 'BV':
      return 'Brutvogel';
    case 'MG':
      return 'Mausergast';
    case 'NB':
      return 'Nichtbrüter';
    case 'RV':
      return 'Reviervogel';
    default:
      return status;
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
  clearCollapseTimer();
  startExpandTimer(id);
};
const onRowMouseLeave = () => {
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
  if (key === 'status') return formatStatus(value);
  if (typeof value === 'boolean') return value ? 'Ja' : 'Nein';
  return value;
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