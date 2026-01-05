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
              <v-combobox
                :model-value="localRelationship.bird1_ring"
                @update:model-value="onBird1Update"
                :items="bird1Suggestions"
                :loading="bird1Loading"
                item-title="ring"
                item-value="ring"
                label="Vogel 1 Ring *"
                :rules="[rules.required]"
                variant="outlined"
                :readonly="isEditing"
                :hint="isEditing ? 'Kann bei bestehender Beziehung nicht geändert werden' : ''"
                persistent-hint
                autocomplete="off"
                :filter="() => true"
                @update:search="searchBird1"
              >
                <template v-slot:item="{ item, props }">
                  <v-list-item v-bind="props" :title="undefined">
                    <div class="d-flex align-center">
                      <v-icon icon="mdi-bird" color="primary" size="small" class="mr-2"></v-icon>
                      <div>
                        <div><strong>{{ item.raw.ring }}</strong> - {{ item.raw.species || 'Unbekannt' }}</div>
                        <div class="text-caption text-medium-emphasis">
                          {{ item.raw.sighting_count }} Sichtung{{ item.raw.sighting_count !== 1 ? 'en' : '' }}
                          <span v-if="item.raw.last_seen"> | Letzte: {{ formatDate(item.raw.last_seen) }}</span>
                        </div>
                      </div>
                    </div>
                  </v-list-item>
                </template>
              </v-combobox>
            </v-col>

            <!-- Bird 2 -->
            <v-col cols="12" md="6">
              <v-combobox
                :model-value="localRelationship.bird2_ring"
                @update:model-value="onBird2Update"
                :items="bird2Suggestions"
                :loading="bird2Loading"
                item-title="ring"
                item-value="ring"
                label="Vogel 2 Ring *"
                :rules="[rules.required]"
                variant="outlined"
                :readonly="isEditing"
                :hint="isEditing ? 'Kann bei bestehender Beziehung nicht geändert werden' : ''"
                persistent-hint
                autocomplete="off"
                :filter="() => true"
                @update:search="searchBird2"
              >
                <template v-slot:item="{ item, props }">
                  <v-list-item v-bind="props" :title="undefined">
                    <div class="d-flex align-center">
                      <v-icon icon="mdi-bird" color="primary" size="small" class="mr-2"></v-icon>
                      <div>
                        <div><strong>{{ item.raw.ring }}</strong> - {{ item.raw.species || 'Unbekannt' }}</div>
                        <div class="text-caption text-medium-emphasis">
                          {{ item.raw.sighting_count }} Sichtung{{ item.raw.sighting_count !== 1 ? 'en' : '' }}
                          <span v-if="item.raw.last_seen"> | Letzte: {{ formatDate(item.raw.last_seen) }}</span>
                        </div>
                      </div>
                    </div>
                  </v-list-item>
                </template>
              </v-combobox>
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

          <!-- Symmetric Relationship Info (read-only) -->
          <v-alert
            v-if="isSymmetricRelationship"
            type="info"
            variant="tonal"
            class="mt-4"
          >
            <v-icon icon="mdi-information"></v-icon>
            <strong>Symmetrische Beziehung:</strong> 
            {{ getSymmetricWarning() }}
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
import debounce from 'lodash/debounce';
import { api } from '@/api';
import {
  createRelationship,
  updateRelationship,
  createSymmetricRelationship
} from '@/api';

interface BirdSuggestion {
  ring: string;
  species: string | null;
  sighting_count: number;
  last_seen: string | null;
}

interface Relationship {
  id?: string;
  bird1_ring: string;
  bird2_ring: string;
  relationship_type: string;
  year: number;
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

const defaultRelationship: Relationship = {
  bird1_ring: '',
  bird2_ring: '',
  relationship_type: '',
  year: new Date().getFullYear(),
  notes: ''
};

const localRelationship = ref<Relationship>({ ...defaultRelationship });

// Ring autocomplete
const bird1Suggestions = ref<BirdSuggestion[]>([]);
const bird2Suggestions = ref<BirdSuggestion[]>([]);
const bird1Loading = ref(false);
const bird2Loading = ref(false);

const searchBird1 = debounce(async (query: string) => {
  if (!query || query.length < 2) {
    bird1Suggestions.value = [];
    return;
  }
  bird1Loading.value = true;
  try {
    const response = await api.get<BirdSuggestion[]>(`/birds/suggestions/${query}`);
    bird1Suggestions.value = response.data.slice(0, 30);
  } catch (error) {
    console.error('Error fetching bird suggestions:', error);
    bird1Suggestions.value = [];
  } finally {
    bird1Loading.value = false;
  }
}, 300);

const searchBird2 = debounce(async (query: string) => {
  if (!query || query.length < 2) {
    bird2Suggestions.value = [];
    return;
  }
  bird2Loading.value = true;
  try {
    const response = await api.get<BirdSuggestion[]>(`/birds/suggestions/${query}`);
    bird2Suggestions.value = response.data.slice(0, 30);
  } catch (error) {
    console.error('Error fetching bird suggestions:', error);
    bird2Suggestions.value = [];
  } finally {
    bird2Loading.value = false;
  }
}, 300);

const formatDate = (date: string | null) => {
  if (!date) return '';
  return new Date(date).toLocaleDateString('de-DE');
};

// Normalize ring value (handle both string and object from combobox)
const normalizeRing = (value: string | BirdSuggestion | null): string => {
  if (!value) return '';
  if (typeof value === 'string') return value;
  return value.ring || '';
};

const onBird1Update = (value: string | BirdSuggestion | null) => {
  localRelationship.value.bird1_ring = normalizeRing(value);
};

const onBird2Update = (value: string | BirdSuggestion | null) => {
  localRelationship.value.bird2_ring = normalizeRing(value);
};

const relationshipTypeOptions = [
  { value: 'breeding_partner', title: 'Partner' },
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
    return 'Dies ist eine symmetrische Beziehung. Änderungen müssen für beide Richtungen separat vorgenommen werden.';
  }
  if (localRelationship.value.relationship_type === 'sibling_of') {
    return 'Dies ist eine symmetrische Beziehung. Änderungen müssen für beide Richtungen separat vorgenommen werden.';
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
        notes: localRelationship.value.notes || undefined
      });
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
:deep(.v-text-field .v-field__input),
:deep(.v-select .v-field__input),
:deep(.v-combobox .v-field__input),
:deep(.v-textarea .v-field__input) {
  font-size: 0.875rem;
}
</style>
