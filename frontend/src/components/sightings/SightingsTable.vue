<template>
  <v-data-table
    :headers="headers"
    :items="sightings"
    :loading="loading"
    hover
    class="elevation-0 border rounded"
    @click:row="handleRowClick"
  >
    <template v-slot:item.date="{ item }">
      {{ formatDate(item.date) }}
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
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { format } from 'date-fns';
import type { Sighting } from '@/types';
import * as api from '@/api';

const props = defineProps<{
  sightings: Sighting[];
  loading: boolean;
}>();

const emit = defineEmits<{
  'deleted': [id: string];
}>();

const router = useRouter();
const showDeleteDialog = ref(false);
const deleteLoading = ref(false);
const selectedSighting = ref<Sighting | null>(null);

const headers = [
  { title: 'Datum', key: 'date', sortable: true },
  { title: 'Ring', key: 'ring', sortable: true },
  { title: 'Ablesung', key: 'reading', sortable: true },
  { title: 'Spezies', key: 'species', sortable: true },
  { title: 'Ort', key: 'place', sortable: true },
  { title: 'Gruppengröße', key: 'group_size', sortable: true },
  { title: 'Melder', key: 'melder', sortable: true },
  { title: 'Gemeldet', key: 'melded', sortable: true },
  { title: 'Aktionen', key: 'actions', sortable: false }
];

const formatDate = (date?: string) => {
  return date ? format(new Date(date), 'dd.MM.yyyy') : '';
};

const handleRowClick = (event: Event, item: any) => {
  const sighting = item.item;
  router.push(`/entry/${sighting.id}`);
};

const confirmDelete = (item: Sighting) => {
  selectedSighting.value = item;
  showDeleteDialog.value = true;
};

const handleDelete = async () => {
  if (!selectedSighting.value?.id) return;
  
  deleteLoading.value = true;
  try {
    await api.deleteSighting(selectedSighting.value.id);
    emit('deleted', selectedSighting.value.id);
    showDeleteDialog.value = false;
  } catch (error) {
    console.error('Error deleting sighting:', error);
  } finally {
    deleteLoading.value = false;
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
</style>