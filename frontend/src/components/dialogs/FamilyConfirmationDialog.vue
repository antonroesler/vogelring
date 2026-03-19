<template>
  <v-dialog v-model="dialog" max-width="600" width="95%" persistent>
    <v-card>
      <v-card-title>Sichtungen erstellen - Bestätigung</v-card-title>
      <v-card-text>
        <p class="mb-4">Folgende Sichtungen werden erstellt:</p>

        <v-list>
          <!-- Main sighting — always created, no toggle -->
          <v-list-item>
            <template v-slot:prepend>
              <v-icon icon="mdi-bird" color="primary" class="mr-2"></v-icon>
            </template>
            <v-list-item-title>Hauptsichtung <span class="text-caption text-medium-emphasis">(wird immer erstellt)</span></v-list-item-title>
            <v-list-item-subtitle>
              Ring: {{ mainSighting.ring || 'Nicht angegeben' }} |
              Ort: {{ mainSighting.place || 'Nicht angegeben' }} |
              Datum: {{ mainSighting.date || 'Nicht angegeben' }}
            </v-list-item-subtitle>
          </v-list-item>

          <!-- Partner sighting — optional checkbox -->
          <v-list-item v-if="partnerSighting">
            <template v-slot:prepend>
              <v-checkbox
                v-model="includePartner"
                color="red"
                density="comfortable"
                hide-details
                class="mr-1"
              ></v-checkbox>
            </template>
            <v-list-item-title>
              <v-icon icon="mdi-heart" color="red" size="small" class="mr-1"></v-icon>
              Partner-Sichtung
            </v-list-item-title>
            <v-list-item-subtitle>
              Ring: {{ partnerSighting.ring }} |
              Ort: {{ partnerSighting.place }} |
              Datum: {{ partnerSighting.date }}
            </v-list-item-subtitle>
          </v-list-item>

          <!-- Child sightings — optional checkboxes -->
          <v-list-item
            v-for="(child, index) in childSightings"
            :key="index"
          >
            <template v-slot:prepend>
              <v-checkbox
                v-model="includedChildren[index]"
                color="green"
                density="comfortable"
                hide-details
                class="mr-1"
              ></v-checkbox>
            </template>
            <v-list-item-title>
              <v-icon icon="mdi-baby-face" color="green" size="small" class="mr-1"></v-icon>
              Kind {{ index + 1 }} Sichtung
            </v-list-item-title>
            <v-list-item-subtitle>
              Ring: {{ child.ring }} |
              Alter: {{ child.age || 'Nicht angegeben' }} |
              Ort: {{ child.place }} |
              Datum: {{ child.date }}
            </v-list-item-subtitle>
          </v-list-item>
        </v-list>

        <v-alert type="info" variant="tonal" class="mt-4">
          Familienbeziehungen werden automatisch für die ausgewählten Sichtungen erstellt.
        </v-alert>
      </v-card-text>

      <v-card-actions>
        <v-btn color="grey" variant="text" @click="cancel">
          Abbrechen
        </v-btn>
        <v-spacer></v-spacer>
        <v-btn
          color="primary"
          @click="confirm"
          :loading="loading"
        >
          Speichern
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import type { Sighting } from '@/types';

export interface FamilySelections {
  includePartner: boolean;
  includedChildIndices: number[];
}

const props = defineProps<{
  modelValue: boolean;
  mainSighting: Partial<Sighting>;
  partnerSighting?: Partial<Sighting>;
  childSightings: Array<Partial<Sighting>>;
  loading?: boolean;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: boolean];
  'confirm': [selections: FamilySelections];
  'cancel': [];
}>();

const dialog = ref(props.modelValue);
const includePartner = ref(true);
const includedChildren = ref<boolean[]>([]);

// Reset checkbox state whenever the dialog opens
watch(() => props.modelValue, (newValue) => {
  dialog.value = newValue;
  if (newValue) {
    includePartner.value = true;
    includedChildren.value = props.childSightings.map(() => true);
  }
});

// Also initialise when childSightings prop changes while dialog is open
watch(() => props.childSightings, (newChildren) => {
  if (dialog.value) {
    includedChildren.value = newChildren.map(() => true);
  }
});

watch(dialog, (newValue) => {
  emit('update:modelValue', newValue);
});

const confirm = () => {
  const includedChildIndices = includedChildren.value
    .map((checked, index) => (checked ? index : -1))
    .filter((i) => i !== -1);

  emit('confirm', {
    includePartner: includePartner.value,
    includedChildIndices
  });
};

const cancel = () => {
  emit('cancel');
  dialog.value = false;
};
</script>
