<template>
  <v-card>
    <v-card-title class="d-flex align-center">
      <v-icon icon="mdi-family-tree" class="me-2" color="primary"></v-icon>
      Familienbeziehungen
      <v-spacer></v-spacer>
      <v-btn
        icon="mdi-plus"
        variant="text"
        @click="showCreateDialog = true"
        v-tooltip="'Neue Beziehung hinzufügen'"
        size="small"
      ></v-btn>
      <v-btn
        icon="mdi-open-in-new"
        variant="text"
        :to="`/family-relations?bird_ring=${ring}`"
        target="_blank"
        v-tooltip="'Alle Beziehungen anzeigen'"
        size="small"
      ></v-btn>
    </v-card-title>
    
    <v-card-text>
      <v-progress-circular
        v-if="loading"
        indeterminate
        color="primary"
        class="ma-4"
      ></v-progress-circular>

      <template v-else>
        <v-tabs v-model="activeTab" class="mb-4">
          <v-tab value="partners">
            <v-icon icon="mdi-heart" class="me-2"></v-icon>
            Partner ({{ partners.length }})
          </v-tab>
          <v-tab value="children">
            <v-icon icon="mdi-baby-face" class="me-2"></v-icon>
            Nachkommen ({{ children.length }})
          </v-tab>
          <v-tab value="parents">
            <v-icon icon="mdi-account-supervisor" class="me-2"></v-icon>
            Eltern ({{ parents.length }})
          </v-tab>
          <v-tab value="siblings">
            <v-icon icon="mdi-account-group" class="me-2"></v-icon>
            Geschwister ({{ siblings.length }})
          </v-tab>
        </v-tabs>

        <v-tabs-window v-model="activeTab">
          <!-- Partners Tab -->
          <v-tabs-window-item value="partners">
            <family-relationship-list
              :relationships="partnerRelationships"
              :bird-ring="ring"
              @edit="editRelationship"
              @delete="confirmDelete"
            />
          </v-tabs-window-item>

          <!-- Children Tab -->
          <v-tabs-window-item value="children">
            <family-relationship-list
              :relationships="childrenRelationships"
              :bird-ring="ring"
              @edit="editRelationship"
              @delete="confirmDelete"
            />
          </v-tabs-window-item>

          <!-- Parents Tab -->
          <v-tabs-window-item value="parents">
            <family-relationship-list
              :relationships="parentRelationships"
              :bird-ring="ring"
              @edit="editRelationship"
              @delete="confirmDelete"
            />
          </v-tabs-window-item>

          <!-- Siblings Tab -->
          <v-tabs-window-item value="siblings">
            <family-relationship-list
              :relationships="siblingRelationships"
              :bird-ring="ring"
              @edit="editRelationship"
              @delete="confirmDelete"
            />
          </v-tabs-window-item>
        </v-tabs-window>
      </template>
    </v-card-text>

    <!-- Create/Edit Dialog -->
    <family-relationship-editor
      v-model="showCreateDialog"
      :relationship="editingRelationship"
      :default-bird-ring="ring"
      @saved="handleRelationshipSaved"
      @cancelled="handleDialogCancelled"
    />

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="showDeleteDialog" max-width="500">
      <v-card>
        <v-card-title>Beziehung löschen</v-card-title>
        <v-card-text>
          <p>Möchten Sie diese Familienbeziehung wirklich löschen?</p>
          
          <v-checkbox
            v-if="isSymmetricRelationshipToDelete"
            v-model="deleteSymmetric"
            label="Auch die entsprechende Rückbeziehung löschen"
            class="mt-2"
            density="compact"
          ></v-checkbox>
          
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
  </v-card>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { 
  getBirdRelationships, 
  deleteRelationship as apiDeleteRelationship 
} from '@/api';
import FamilyRelationshipEditor from './FamilyRelationshipEditor.vue';
import FamilyRelationshipList from './FamilyRelationshipList.vue';

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

const props = defineProps<{
  ring: string;
}>();

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
const activeTab = ref('partners');
const deleteSymmetric = ref(true); // Default to true for symmetric deletion

// Computed properties to filter relationships by type
const partners = computed(() => 
  relationships.value.filter(rel => rel.relationship_type === 'breeding_partner')
);

const children = computed(() => 
  relationships.value.filter(rel => 
    rel.relationship_type === 'parent_of' && rel.bird1_ring === props.ring
  )
);

const parents = computed(() => 
  relationships.value.filter(rel => 
    rel.relationship_type === 'child_of' && rel.bird1_ring === props.ring
  )
);

const siblings = computed(() => 
  relationships.value.filter(rel => rel.relationship_type === 'sibling_of')
);

// Transform relationships for display components
const partnerRelationships = computed(() => 
  partners.value.map(rel => ({
    ...rel,
    otherBird: rel.bird1_ring === props.ring ? rel.bird2_ring : rel.bird1_ring,
    displayType: 'Brutpartner'
  }))
);

const childrenRelationships = computed(() => 
  children.value.map(rel => ({
    ...rel,
    otherBird: rel.bird2_ring,
    displayType: 'Nachkomme'
  }))
);

const parentRelationships = computed(() => 
  parents.value.map(rel => ({
    ...rel,
    otherBird: rel.bird2_ring,
    displayType: 'Elternteil'
  }))
);

const siblingRelationships = computed(() => 
  siblings.value.map(rel => ({
    ...rel,
    otherBird: rel.bird1_ring === props.ring ? rel.bird2_ring : rel.bird1_ring,
    displayType: 'Geschwister'
  }))
);

// Check if relationship to delete is symmetric
const isSymmetricRelationshipToDelete = computed(() => 
  relationshipToDelete.value && 
  ['breeding_partner', 'sibling_of'].includes(relationshipToDelete.value.relationship_type)
);

const loadRelationships = async () => {
  if (!props.ring) return;
  
  loading.value = true;
  try {
    relationships.value = await getBirdRelationships(props.ring);
  } catch (error) {
    console.error('Error loading relationships:', error);
    errorMessage.value = 'Fehler beim Laden der Familienbeziehungen';
    showErrorSnackbar.value = true;
  } finally {
    loading.value = false;
  }
};

const editRelationship = (relationship: any) => {
  editingRelationship.value = relationship;
  showCreateDialog.value = true;
};

const confirmDelete = (relationship: any) => {
  relationshipToDelete.value = relationship;
  showDeleteDialog.value = true;
};

const deleteRelationship = async () => {
  if (!relationshipToDelete.value) return;
  
  deleting.value = true;
  try {
    await apiDeleteRelationship(relationshipToDelete.value.id, deleteSymmetric.value);
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

onMounted(() => {
  loadRelationships();
});
</script>

<style scoped>
:deep(.v-tab) {
  font-size: 0.875rem;
}

:deep(.v-tabs-window-item) {
  padding: 0;
}
</style>
