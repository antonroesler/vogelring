<template>
  <v-dialog v-model="dialog" max-width="600" persistent>
    <v-card>
      <v-card-title>Familie erstellen - Bestätigung</v-card-title>
      <v-card-text>
        <p class="mb-4">Folgende Sichtungen werden erstellt:</p>
        
        <v-list>
          <v-list-item>
            <template v-slot:prepend>
              <v-icon icon="mdi-bird" color="primary"></v-icon>
            </template>
            <v-list-item-title>Hauptsichtung</v-list-item-title>
            <v-list-item-subtitle>
              Ring: {{ mainSighting.ring || 'Nicht angegeben' }} | 
              Ort: {{ mainSighting.place || 'Nicht angegeben' }} |
              Datum: {{ mainSighting.date || 'Nicht angegeben' }}
            </v-list-item-subtitle>
          </v-list-item>

          <v-list-item v-if="partnerSighting">
            <template v-slot:prepend>
              <v-icon icon="mdi-heart" color="red"></v-icon>
            </template>
            <v-list-item-title>Partner-Sichtung</v-list-item-title>
            <v-list-item-subtitle>
              Ring: {{ partnerSighting.ring }} | 
              Ort: {{ partnerSighting.place }} |
              Datum: {{ partnerSighting.date }}
            </v-list-item-subtitle>
          </v-list-item>

          <v-list-item 
            v-for="(child, index) in childSightings" 
            :key="index"
          >
            <template v-slot:prepend>
              <v-icon icon="mdi-baby-face" color="green"></v-icon>
            </template>
            <v-list-item-title>Kind {{ index + 1 }} Sichtung</v-list-item-title>
            <v-list-item-subtitle>
              Ring: {{ child.ring }} | 
              Alter: {{ child.age || 'Nicht angegeben' }} |
              Ort: {{ child.place }} |
              Datum: {{ child.date }}
            </v-list-item-subtitle>
          </v-list-item>
        </v-list>

        <v-alert type="info" variant="tonal" class="mt-4">
          Zusätzlich werden automatisch die entsprechenden Familienbeziehungen erstellt.
        </v-alert>
      </v-card-text>
      
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="grey" variant="text" @click="cancel">
          Zurück zum Bearbeiten
        </v-btn>
        <v-btn 
          color="primary" 
          @click="confirm"
          :loading="loading"
        >
          Familie erstellen
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import type { Sighting } from '@/types';

const props = defineProps<{
  modelValue: boolean;
  mainSighting: Partial<Sighting>;
  partnerSighting?: Partial<Sighting>;
  childSightings: Array<Partial<Sighting>>;
  loading?: boolean;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: boolean];
  'confirm': [];
  'cancel': [];
}>();

const dialog = ref(props.modelValue);

watch(() => props.modelValue, (newValue) => {
  dialog.value = newValue;
});

watch(dialog, (newValue) => {
  emit('update:modelValue', newValue);
});

const confirm = () => {
  emit('confirm');
};

const cancel = () => {
  emit('cancel');
  dialog.value = false;
};
</script>
