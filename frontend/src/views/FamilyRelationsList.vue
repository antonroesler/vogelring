<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card class="mb-4 family-relations-card">
          <v-card-title class="d-flex align-center">
            <v-icon icon="mdi-family-tree" class="me-2" color="primary"></v-icon>
            <div class="d-flex flex-column">
              <span class="card-title-text">Familienbeziehungen</span>
              <v-chip
                v-if="birdRingFilter"
                color="primary"
                variant="tonal"
                size="small"
                class="mt-1"
                prepend-icon="mdi-bird"
                :to="`/birds/${birdRingFilter}`"
                target="_blank"
                clickable
              >
                Gefiltert für Vogel: {{ birdRingFilter }}
                <v-icon size="small" class="ml-1">mdi-open-in-new</v-icon>
              </v-chip>
            </div>
            <v-spacer></v-spacer>
            <v-btn
              v-if="birdRingFilter"
              color="secondary"
              variant="outlined"
              prepend-icon="mdi-close"
              @click="clearBirdFilter"
              class="me-2"
            >
              Filter entfernen
            </v-btn>
            <v-btn
              color="primary"
              variant="elevated"
              prepend-icon="mdi-plus"
              @click="showCreateDialog = true"
              class="create-btn"
            >
              Neue Beziehung
            </v-btn>
          </v-card-title>
          
          <v-card-text>
            <!-- Filters -->
            <v-row class="mb-4">
              <v-col cols="12" md="3">
                <v-select
                  v-model="filters.relationship_type"
                  :items="relationshipTypeOptions"
                  label="Beziehungstyp"
                  clearable
                  variant="outlined"
                  density="compact"
                ></v-select>
              </v-col>
              <v-col cols="12" md="2">
                <v-text-field
                  v-model="filters.year"
                  label="Jahr"
                  type="number"
                  clearable
                  variant="outlined"
                  density="compact"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="3">
                <v-text-field
                  v-model="filters.bird_ring"
                  label="Ring"
                  clearable
                  variant="outlined"
                  density="compact"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="2">
                <v-text-field
                  v-model="filters.limit"
                  label="Anzahl"
                  type="number"
                  variant="outlined"
                  density="compact"
                  :min="1"
                  :max="1000"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="2">
                <v-btn
                  @click="loadRelationships"
                  color="primary"
                  variant="tonal"
                  block
                  :loading="loading"
                >
                  Filtern
                </v-btn>
              </v-col>
            </v-row>

            <!-- Data Table -->
            <v-data-table
              :headers="headers"
              :items="relationships"
              :loading="loading"
              class="elevation-1 family-relations-table"
              :items-per-page="25"
              :items-per-page-options="[10, 25, 50, 100]"
              show-current-page
            >
              <template v-slot:item.relationship_type="{ item }">
                <v-chip
                  :color="getRelationshipTypeColor(item.relationship_type)"
                  size="small"
                  variant="tonal"
                >
                  {{ formatRelationshipType(item.relationship_type) }}
                </v-chip>
              </template>

              <template v-slot:item.bird1_ring="{ item }">
                <v-btn
                  :to="`/birds/${item.bird1_ring}`"
                  target="_blank"
                  variant="text"
                  size="small"
                  color="primary"
                >
                  {{ item.bird1_ring }}
                  <v-icon size="small" class="ml-1">mdi-open-in-new</v-icon>
                </v-btn>
              </template>

              <template v-slot:item.bird2_ring="{ item }">
                <v-btn
                  :to="`/birds/${item.bird2_ring}`"
                  target="_blank"
                  variant="text"
                  size="small"
                  color="primary"
                >
                  {{ item.bird2_ring }}
                  <v-icon size="small" class="ml-1">mdi-open-in-new</v-icon>
                </v-btn>
              </template>


              <template v-slot:item.references="{ item }">
                <div class="d-flex flex-column gap-1">
                  <!-- Prioritize ringing references over sighting references -->
                  <template v-if="item.ringing1_id || item.ringing2_id">
                    <v-btn
                      v-if="item.ringing1_id"
                      :to="`/birds/${item.bird1_ring}`"
                      target="_blank"
                      variant="text"
                      size="x-small"
                      color="primary"
                      class="pa-1"
                      v-tooltip="'Zur Beringung von Vogel 1'"
                    >
                      Beringung 1
                      <v-icon size="x-small" class="ml-1">mdi-open-in-new</v-icon>
                    </v-btn>
                    <v-btn
                      v-if="item.ringing2_id"
                      :to="`/birds/${item.bird2_ring}`"
                      target="_blank"
                      variant="text"
                      size="x-small"
                      color="primary"
                      class="pa-1"
                      v-tooltip="'Zur Beringung von Vogel 2'"
                    >
                      Beringung 2
                      <v-icon size="x-small" class="ml-1">mdi-open-in-new</v-icon>
                    </v-btn>
                  </template>
                  <template v-else-if="item.sighting1_id || item.sighting2_id">
                    <v-btn
                      v-if="item.sighting1_id"
                      :to="`/entries/${item.sighting1_id}`"
                      target="_blank"
                      variant="text"
                      size="x-small"
                      color="primary"
                      class="pa-1"
                      v-tooltip="'Zur Sichtung von Vogel 1'"
                    >
                      Sichtung 1
                      <v-icon size="x-small" class="ml-1">mdi-open-in-new</v-icon>
                    </v-btn>
                    <v-btn
                      v-if="item.sighting2_id"
                      :to="`/entries/${item.sighting2_id}`"
                      target="_blank"
                      variant="text"
                      size="x-small"
                      color="primary"
                      class="pa-1"
                      v-tooltip="'Zur Sichtung von Vogel 2'"
                    >
                      Sichtung 2
                      <v-icon size="x-small" class="ml-1">mdi-open-in-new</v-icon>
                    </v-btn>
                  </template>
                  <span v-else class="text-medium-emphasis">-</span>
                </div>
              </template>

              <template v-slot:item.created_at="{ item }">
                {{ formatDate(item.created_at) }}
              </template>

              <template v-slot:item.actions="{ item }">
                <v-btn
                  icon="mdi-pencil"
                  variant="text"
                  size="small"
                  @click="editRelationship(item)"
                  v-tooltip="'Bearbeiten'"
                ></v-btn>
                <v-btn
                  icon="mdi-delete"
                  variant="text"
                  size="small"
                  color="error"
                  @click="confirmDelete(item)"
                  v-tooltip="'Löschen'"
                ></v-btn>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Create/Edit Dialog -->
    <family-relationship-editor
      v-model="showCreateDialog"
      :relationship="editingRelationship"
      @saved="handleRelationshipSaved"
      @cancelled="handleDialogCancelled"
    />

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="showDeleteDialog" max-width="500">
      <v-card>
        <v-card-title>Beziehung löschen</v-card-title>
        <v-card-text>
          <p>Möchten Sie diese Familienbeziehung wirklich löschen?</p>
          
          
          <v-alert type="warning" variant="tonal" class="mt-3">
            <strong>Achtung:</strong> Diese Aktion kann nicht rückgängig gemacht werden.
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="showDeleteDialog = false">
            Abbrechen
          </v-btn>
          <v-btn 
            color="error" 
            @click="deleteRelationship"
            :loading="deleting"
          >
            Löschen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbars -->
    <v-snackbar v-model="showSuccessSnackbar" color="success">
      <v-icon icon="mdi-check-circle" class="me-2"></v-icon>
      {{ successMessage }}
    </v-snackbar>
    
    <v-snackbar v-model="showErrorSnackbar" color="error">
      <v-icon icon="mdi-alert-circle" class="me-2"></v-icon>
      {{ errorMessage }}
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { format } from 'date-fns';
import { getAllRelationships, deleteRelationship as apiDeleteRelationship } from '@/api';
import FamilyRelationshipEditor from '@/components/family/FamilyRelationshipEditor.vue';

interface Relationship {
  id: string;
  bird1_ring: string;
  bird2_ring: string;
  relationship_type: string;
  year: number;
  confidence?: string;
  source?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

const route = useRoute();
const router = useRouter();

const relationships = ref<Relationship[]>([]);
const loading = ref(false);
const deleting = ref(false);
const showCreateDialog = ref(false);
const showDeleteDialog = ref(false);
const showSuccessSnackbar = ref(false);
const showErrorSnackbar = ref(false);
const successMessage = ref('');
const errorMessage = ref('');
const editingRelationship = ref<Relationship | null>(null);
const relationshipToDelete = ref<Relationship | null>(null);

// Get bird ring filter from URL parameter
const birdRingFilter = computed(() => route.query.bird_ring as string || null);

const filters = ref({
  relationship_type: null as string | null,
  year: null as number | null,
  bird_ring: null as string | null,
  limit: 100
});

const relationshipTypeOptions = [
  { value: 'breeding_partner', title: 'Brutpartner' },
  { value: 'parent_of', title: 'Elternteil von' },
  { value: 'child_of', title: 'Kind von' },
  { value: 'sibling_of', title: 'Geschwister von' }
];

const headers = [
  { title: 'Vogel 1', key: 'bird1_ring', sortable: true },
  { title: 'Beziehung', key: 'relationship_type', sortable: true },
  { title: 'Vogel 2', key: 'bird2_ring', sortable: true },
  { title: 'Jahr', key: 'year', sortable: true },
  { title: 'Referenzen', key: 'references', sortable: false },
  { title: 'Erstellt', key: 'created_at', sortable: true },
  { title: 'Aktionen', key: 'actions', sortable: false, width: 120 }
];


const formatRelationshipType = (type: string) => {
  const option = relationshipTypeOptions.find(opt => opt.value === type);
  return option ? option.title : type;
};

const getRelationshipTypeColor = (type: string) => {
  switch (type) {
    case 'breeding_partner': return 'red';
    case 'parent_of': return 'blue';
    case 'child_of': return 'green';
    case 'sibling_of': return 'orange';
    default: return 'grey';
  }
};


const formatDate = (dateString: string) => {
  return format(new Date(dateString), 'dd.MM.yyyy HH:mm');
};

const loadRelationships = async () => {
  loading.value = true;
  try {
    const params: any = {};
    if (filters.value.relationship_type) params.relationship_type = filters.value.relationship_type;
    if (filters.value.year) params.year = filters.value.year;
    if (filters.value.bird_ring) params.bird_ring = filters.value.bird_ring;
    if (filters.value.limit) params.limit = filters.value.limit;

    relationships.value = await getAllRelationships(params);
  } catch (error) {
    console.error('Error loading relationships:', error);
    errorMessage.value = 'Fehler beim Laden der Familienbeziehungen';
    showErrorSnackbar.value = true;
  } finally {
    loading.value = false;
  }
};

const editRelationship = (relationship: Relationship) => {
  editingRelationship.value = relationship;
  showCreateDialog.value = true;
};

const confirmDelete = (relationship: Relationship) => {
  relationshipToDelete.value = relationship;
  showDeleteDialog.value = true;
};

const deleteRelationship = async () => {
  if (!relationshipToDelete.value) return;
  
  deleting.value = true;
  try {
    await apiDeleteRelationship(relationshipToDelete.value.id);
    successMessage.value = 'Familienbeziehung erfolgreich gelöscht';
    showSuccessSnackbar.value = true;
    showDeleteDialog.value = false;
    relationshipToDelete.value = null;
    await loadRelationships();
  } catch (error) {
    console.error('Error deleting relationship:', error);
    errorMessage.value = 'Fehler beim Löschen der Familienbeziehung';
    showErrorSnackbar.value = true;
  } finally {
    deleting.value = false;
  }
};

const handleRelationshipSaved = () => {
  successMessage.value = editingRelationship.value 
    ? 'Familienbeziehung erfolgreich aktualisiert' 
    : 'Familienbeziehung erfolgreich erstellt';
  showSuccessSnackbar.value = true;
  loadRelationships();
};

const handleDialogCancelled = () => {
  editingRelationship.value = null;
};

const clearBirdFilter = () => {
  router.push({ path: '/family-relations' });
};

// Initialize filters with URL parameters
const initializeFilters = () => {
  if (birdRingFilter.value) {
    filters.value.bird_ring = birdRingFilter.value;
  }
};

// Watch filters for auto-refresh
watch(filters, () => {
  loadRelationships();
}, { deep: true });

// Watch route changes to update filters
watch(() => route.query.bird_ring, (newBirdRing) => {
  if (newBirdRing) {
    filters.value.bird_ring = newBirdRing as string;
  } else {
    filters.value.bird_ring = null;
  }
}, { immediate: true });

onMounted(() => {
  initializeFilters();
  loadRelationships();
});
</script>

<style scoped>
.family-relations-card {
  border-radius: 16px !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08) !important;
  border: 1px solid rgba(0, 67, 108, 0.1) !important;
}

.card-title-text {
  font-size: 1.25rem;
  font-weight: 600;
  color: #00436C;
}

.create-btn {
  border-radius: 12px !important;
  font-weight: 600 !important;
  text-transform: none !important;
  letter-spacing: 0.025em !important;
  background: linear-gradient(135deg, #00436C 0%, #228096 100%) !important;
  box-shadow: 0 4px 16px rgba(0, 67, 108, 0.3) !important;
}

.family-relations-table {
  border-radius: 12px !important;
}

:deep(.v-data-table-header th) {
  background-color: rgba(0, 67, 108, 0.05) !important;
  font-weight: 600 !important;
}

:deep(.v-data-table__tr:hover) {
  background-color: rgba(0, 67, 108, 0.02) !important;
}
</style>
