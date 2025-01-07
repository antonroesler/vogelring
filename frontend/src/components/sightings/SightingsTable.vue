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
    <template v-slot:item.date="{ item }">
      {{ formatDate(item.date) }}
    </template>
    <template v-slot:item.melded="{ item }">
      <v-btn
        :icon="item.melded ? 'mdi-check-circle' : 'mdi-circle-outline'"
        :color="item.melded ? 'success' : 'grey'"
        variant="text"
        color="error"
        size="small"
        :loading="loadingMeldedStates[item.id]"
        @click.stop="toggleMelded(item)"
        :disabled="loading"
      ></v-btn>
    </template>
    <template v-slot:item.actions="{ item }">
      <v-btn
        icon="mdi-delete"
        variant="text"
        color="error"
        size="small"
        @click.stop="confirmDelete(item)"
      ></v-btn>
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

// Add computed properties for pagination
const page = computed({
  get: () => store.pagination.page,
  set: (value) => store.setPagination({ page: value })
});

const itemsPerPage = computed({
  get: () => store.pagination.itemsPerPage,
  set: (value) => store.setPagination({ itemsPerPage: value })
});

const headers = [
  { title: 'Datum', key: 'date', sortable: true },
  { title: 'Ring', key: 'ring', sortable: true },
  { title: 'Ablesung', key: 'reading', sortable: true },
  { title: 'Spezies', key: 'species', sortable: true },
  { title: 'Ort', key: 'place', sortable: true },
  { title: 'Melder', key: 'melder', sortable: true },
  { title: 'Gemeldet', key: 'melded', sortable: true },
  { title: 'Aktionen', key: 'actions', sortable: false }
];

const formatDate = (date?: string) => {
  return date ? format(new Date(date), 'dd.MM.yyyy') : '';
};

const handleRowClick = (event: Event, item: any) => {
  const sighting = item.item;
  router.push({
    path: `/entries/${sighting.id}`,
    query: { 
      from: 'list',
      page: store.pagination.page.toString(),
      perPage: store.pagination.itemsPerPage.toString()
    }
  });
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
</style>