<template>
  <v-dialog v-model="dialog" max-width="600" persistent>
    <v-card>
      <v-card-title>
        {{ isEditing ? 'Familienbeziehung bearbeiten' : 'Neue Familienbeziehung erstellen' }}
      </v-card-title>
      
      <v-card-text>
        <v-form ref="form" v-model="valid">
          <v-row>
            <!-- Bird 1 -->
            <v-col cols="12" md="6">
              <v-text-field
                v-model="localRelationship.bird1_ring"
                label="Vogel 1 Ring *"
                :rules="[rules.required]"
                variant="outlined"
                :readonly="isEditing"
                :hint="isEditing ? 'Kann bei bestehender Beziehung nicht geändert werden' : ''"
                persistent-hint
              ></v-text-field>
            </v-col>

            <!-- Bird 2 -->
            <v-col cols="12" md="6">
              <v-text-field
                v-model="localRelationship.bird2_ring"
                label="Vogel 2 Ring *"
                :rules="[rules.required]"
                variant="outlined"
                :readonly="isEditing"
                :hint="isEditing ? 'Kann bei bestehender Beziehung nicht geändert werden' : ''"
                persistent-hint
              ></v-text-field>
            </v-col>

            <!-- Relationship Type -->
            <v-col cols="12" md="6">
              <v-select
                v-model="localRelationship.relationship_type"
                :items="relationshipTypeOptions"
                label="Beziehungstyp *"
                :rules="[rules.required]"
                variant="outlined"
              ></v-select>
            </v-col>

            <!-- Year -->
            <v-col cols="12" md="6">
              <v-text-field
                v-model="localRelationship.year"
                label="Jahr *"
                type="number"
                :rules="[rules.required, rules.validYear]"
                variant="outlined"
                :min="1900"
                :max="2100"
              ></v-text-field>
            </v-col>


            <!-- Source -->
            <v-col cols="12" md="6">
              <v-text-field
                v-model="localRelationship.source"
                label="Quelle"
                variant="outlined"
                :rules="[rules.maxLength(100)]"
              ></v-text-field>
            </v-col>

            <!-- Notes -->
            <v-col cols="12">
              <v-textarea
                v-model="localRelationship.notes"
                label="Notizen"
                variant="outlined"
                :rules="[rules.maxLength(500)]"
                rows="3"
              ></v-textarea>
            </v-col>
          </v-row>

          <!-- Symmetric Relationship Options -->
          <v-alert
            v-if="isSymmetricRelationship"
            type="info"
            variant="tonal"
            class="mt-4"
          >
            <v-icon icon="mdi-information"></v-icon>
            <strong>Symmetrische Beziehung:</strong> 
            {{ getSymmetricWarning() }}
            
            <v-checkbox
              v-if="isEditing"
              v-model="updateSymmetric"
              label="Auch die entsprechende Rückbeziehung aktualisieren"
              class="mt-2"
              density="compact"
            ></v-checkbox>
          </v-alert>

          <!-- Validation Error -->
          <v-alert
            v-if="validationError"
            type="error"
            variant="tonal"
            class="mt-4"
          >
            {{ validationError }}
          </v-alert>
        </v-form>
      </v-card-text>
      
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="grey" variant="text" @click="cancel">
          Abbrechen
        </v-btn>
        <v-btn 
          color="primary" 
          @click="save"
          :loading="saving"
          :disabled="!valid"
        >
          {{ isEditing ? 'Aktualisieren' : 'Erstellen' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { 
  createRelationship, 
  updateRelationship, 
  createSymmetricRelationship 
} from '@/api';

interface Relationship {
  id?: string;
  bird1_ring: string;
  bird2_ring: string;
  relationship_type: string;
  year: number;
  confidence?: string;
  source?: string;
  notes?: string;
}

const props = defineProps<{
  modelValue: boolean;
  relationship?: Relationship | null;
  defaultBirdRing?: string;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: boolean];
  'saved': [];
  'cancelled': [];
}>();

const dialog = ref(props.modelValue);
const valid = ref(false);
const saving = ref(false);
const validationError = ref('');
const form = ref();
const updateSymmetric = ref(true); // Default to true for symmetric updates

const defaultRelationship: Relationship = {
  bird1_ring: '',
  bird2_ring: '',
  relationship_type: '',
  year: new Date().getFullYear(),
  confidence: '',
  source: '',
  notes: ''
};

const localRelationship = ref<Relationship>({ ...defaultRelationship });

const relationshipTypeOptions = [
  { value: 'breeding_partner', title: 'Brutpartner' },
  { value: 'parent_of', title: 'Elternteil von' },
  { value: 'child_of', title: 'Kind von' },
  { value: 'sibling_of', title: 'Geschwister von' }
];


const rules = {
  required: (value: any) => !!value || 'Dieses Feld ist erforderlich',
  validYear: (value: number) => {
    if (!value) return 'Jahr ist erforderlich';
    if (value < 1900 || value > 2100) return 'Jahr muss zwischen 1900 und 2100 liegen';
    return true;
  },
  maxLength: (max: number) => (value: string) => 
    !value || value.length <= max || `Maximal ${max} Zeichen erlaubt`
};

const isEditing = computed(() => !!props.relationship?.id);

const isSymmetricRelationship = computed(() => 
  ['breeding_partner', 'sibling_of'].includes(localRelationship.value.relationship_type)
);

const getSymmetricWarning = () => {
  if (localRelationship.value.relationship_type === 'breeding_partner') {
    return 'Es wird automatisch eine entsprechende Brutpartner-Beziehung in beide Richtungen erstellt.';
  }
  if (localRelationship.value.relationship_type === 'sibling_of') {
    return 'Es wird automatisch eine entsprechende Geschwister-Beziehung in beide Richtungen erstellt.';
  }
  return '';
};

const validateRelationship = () => {
  validationError.value = '';
  
  // Check if birds are different
  if (localRelationship.value.bird1_ring === localRelationship.value.bird2_ring) {
    validationError.value = 'Vogel 1 und Vogel 2 müssen unterschiedlich sein';
    return false;
  }

  // Check for logical consistency
  if (localRelationship.value.relationship_type === 'parent_of') {
    // Could add additional validation here
  }

  return true;
};

const save = async () => {
  if (!form.value.validate() || !validateRelationship()) {
    return;
  }

  saving.value = true;
  try {
    if (isEditing.value) {
      // Update existing relationship
      await updateRelationship(localRelationship.value.id!, {
        relationship_type: localRelationship.value.relationship_type as any,
        year: localRelationship.value.year,
        source: localRelationship.value.source || undefined,
        notes: localRelationship.value.notes || undefined
      }, updateSymmetric.value);
    } else {
      // Create new relationship
      if (isSymmetricRelationship.value) {
        await createSymmetricRelationship({
          bird1_ring: localRelationship.value.bird1_ring,
          bird2_ring: localRelationship.value.bird2_ring,
          relationship_type: localRelationship.value.relationship_type as any,
          year: localRelationship.value.year
        });
      } else {
        await createRelationship({
          bird1_ring: localRelationship.value.bird1_ring,
          bird2_ring: localRelationship.value.bird2_ring,
          relationship_type: localRelationship.value.relationship_type as any,
          year: localRelationship.value.year,
          source: localRelationship.value.source,
          notes: localRelationship.value.notes
        });
      }
    }
    
    emit('saved');
    dialog.value = false;
  } catch (error) {
    console.error('Error saving relationship:', error);
    validationError.value = 'Fehler beim Speichern der Beziehung';
  } finally {
    saving.value = false;
  }
};

const cancel = () => {
  emit('cancelled');
  dialog.value = false;
};

// Watch for dialog changes
watch(() => props.modelValue, (newValue) => {
  dialog.value = newValue;
  if (newValue) {
    // Reset form when opening
    if (props.relationship) {
      localRelationship.value = { ...props.relationship };
    } else {
      localRelationship.value = { 
        ...defaultRelationship,
        bird1_ring: props.defaultBirdRing || ''
      };
    }
    validationError.value = '';
    if (form.value) {
      form.value.resetValidation();
    }
  }
});

watch(dialog, (newValue) => {
  emit('update:modelValue', newValue);
});
</script>

<style scoped>
:deep(.v-text-field .v-field__input) {
  font-size: 0.875rem;
}

:deep(.v-select .v-field__input) {
  font-size: 0.875rem;
}

:deep(.v-textarea .v-field__input) {
  font-size: 0.875rem;
}
</style>
