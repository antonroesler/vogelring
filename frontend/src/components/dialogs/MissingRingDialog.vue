<template>
  <v-dialog v-model="dialog" max-width="500" persistent>
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon icon="mdi-alert-circle" color="warning" class="me-2"></v-icon>
        Ring fehlt
      </v-card-title>
      <v-card-text>
        <p class="mb-4">
          Es wurde kein Ring angegeben. Wie möchten Sie fortfahren?
        </p>
        
        <v-alert 
          v-if="reading" 
          type="info" 
          variant="tonal" 
          class="mb-4"
        >
          <div class="d-flex align-center">
            <v-icon icon="mdi-information" class="me-2"></v-icon>
            <div>
              <strong>Ablesung verfügbar:</strong> {{ reading }}
            </div>
          </div>
        </v-alert>
      </v-card-text>
      
      <v-card-actions class="pa-4">
        <v-btn
          v-if="reading"
          color="primary"
          variant="elevated"
          @click="copyFromReading"
          class="flex-grow-1"
        >
          <v-icon icon="mdi-content-copy" class="me-2"></v-icon>
          Ring aus Ablesung übernehmen
        </v-btn>
        
        <v-btn
          color="warning"
          variant="outlined"
          @click="continueWithoutRing"
          :class="reading ? 'mt-2' : 'flex-grow-1'"
          :block="!!reading"
        >
          <v-icon icon="mdi-alert" class="me-2"></v-icon>
          Ohne Ring speichern
        </v-btn>
        
        <v-btn
          color="grey"
          variant="text"
          @click="cancel"
          :class="reading ? 'mt-2' : ''"
          :block="!!reading"
        >
          <v-icon icon="mdi-close" class="me-2"></v-icon>
          Abbrechen
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

const props = defineProps<{
  modelValue: boolean;
  reading?: string;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: boolean];
  'copy-from-reading': [];
  'continue-without-ring': [];
  'cancel': [];
}>();

const dialog = ref(props.modelValue);

watch(() => props.modelValue, (newValue) => {
  dialog.value = newValue;
});

watch(dialog, (newValue) => {
  emit('update:modelValue', newValue);
});

const copyFromReading = () => {
  emit('copy-from-reading');
  dialog.value = false;
};

const continueWithoutRing = () => {
  emit('continue-without-ring');
  dialog.value = false;
};

const cancel = () => {
  emit('cancel');
  dialog.value = false;
};
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