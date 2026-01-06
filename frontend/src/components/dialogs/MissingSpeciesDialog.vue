<template>
  <v-dialog v-model="dialog" max-width="500" width="90%" persistent>
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon icon="mdi-alert-circle" color="warning" class="me-2"></v-icon>
        Spezies fehlt
      </v-card-title>
      <v-card-text>
        <p class="mb-4">
          Es wurde keine Spezies angegeben. Wie möchten Sie fortfahren?
        </p>
        
        <v-progress-circular
          v-if="isLoading"
          indeterminate
          color="primary"
          class="ma-2"
        ></v-progress-circular>
        
        <v-alert 
          v-else-if="suggestedSpecies" 
          type="success" 
          variant="tonal" 
          class="mb-4"
        >
          <div class="d-flex align-center">
            <v-icon icon="mdi-bird" class="me-2"></v-icon>
            <div>
              <strong>Bekannter Vogel gefunden:</strong><br>
              Ring {{ ring }} ist ein <strong>{{ suggestedSpecies }}</strong>
            </div>
          </div>
        </v-alert>
        
        <v-alert 
          v-else-if="ring && !isLoading" 
          type="info" 
          variant="tonal" 
          class="mb-4"
        >
          <div class="d-flex align-center">
            <v-icon icon="mdi-information" class="me-2"></v-icon>
            <div>
              Ring {{ ring }} ist nicht in der Datenbank bekannt.
            </div>
          </div>
        </v-alert>
      </v-card-text>
      
      <v-card-actions class="pa-4">
        <v-btn
          v-if="suggestedSpecies"
          color="primary"
          variant="elevated"
          @click="useSuggestedSpecies"
          class="flex-grow-1"
          :disabled="isLoading"
        >
          <v-icon icon="mdi-bird" class="me-2"></v-icon>
          {{ suggestedSpecies }} verwenden
        </v-btn>
        
        <v-btn
          color="warning"
          variant="outlined"
          @click="continueWithoutSpecies"
          :class="suggestedSpecies ? 'mt-2' : 'flex-grow-1'"
          :block="!!suggestedSpecies"
          :disabled="isLoading"
        >
          <v-icon icon="mdi-alert" class="me-2"></v-icon>
          Ohne Spezies speichern
        </v-btn>
        
        <v-btn
          color="grey"
          variant="text"
          @click="cancel"
          :class="suggestedSpecies ? 'mt-2' : ''"
          :block="!!suggestedSpecies"
          :disabled="isLoading"
        >
          <v-icon icon="mdi-close" class="me-2"></v-icon>
          Abbrechen
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import * as api from '@/api';

const props = defineProps<{
  modelValue: boolean;
  ring?: string;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: boolean];
  'use-suggested-species': [species: string];
  'continue-without-species': [];
  'cancel': [];
}>();

const dialog = ref(props.modelValue);
const suggestedSpecies = ref<string | null>(null);
const isLoading = ref(false);

watch(() => props.modelValue, (newValue) => {
  dialog.value = newValue;
  if (newValue && props.ring) {
    checkBirdSpecies();
  }
});

watch(dialog, (newValue) => {
  emit('update:modelValue', newValue);
});

const checkBirdSpecies = async () => {
  if (!props.ring) return;
  
  isLoading.value = true;
  suggestedSpecies.value = null;
  
  try {
    const bird = await api.getBirdByRing(props.ring);
    if (bird && bird.species) {
      suggestedSpecies.value = bird.species;
    }
  } catch (error) {
    console.error('Error checking bird species:', error);
  } finally {
    isLoading.value = false;
  }
};

const useSuggestedSpecies = () => {
  if (suggestedSpecies.value) {
    emit('use-suggested-species', suggestedSpecies.value);
    dialog.value = false;
  }
};

const continueWithoutSpecies = () => {
  emit('continue-without-species');
  dialog.value = false;
};

const cancel = () => {
  emit('cancel');
  dialog.value = false;
};

onMounted(() => {
  if (props.modelValue && props.ring) {
    checkBirdSpecies();
  }
});
</script>

<style scoped>
.v-card-actions {
  flex-direction: column;
  align-items: stretch;
}

.v-card-actions .v-btn {
  margin: 0;
}

.v-card-actions .v-btn + .v-btn {
  margin-top: 8px;
}

.v-card-actions .v-btn:not(.mt-2) + .v-btn:not(.mt-2) {
  margin-top: 0;
  margin-left: 8px;
}

.v-card-actions:not(:has(.flex-grow-1)) {
  flex-direction: row;
}
</style>