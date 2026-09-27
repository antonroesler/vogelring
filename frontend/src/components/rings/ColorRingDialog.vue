<template>
  <v-dialog :model-value="modelValue" max-width="900" @update:model-value="emit('update:modelValue', $event)">
    <v-card>
      <v-card-title>{{ colorRing ? 'Farbring bearbeiten' : 'Farbring hinzufügen' }}</v-card-title>
      <v-card-text>
        <v-form ref="form">
          <color-ring-input v-model="value" extended />
          <v-row dense>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="metalRing"
                label="Metallring"
                :disabled="!!lockedRing"
                :hint="lockedRing ? undefined : 'Leer lassen, wenn der Metallring unbekannt ist'"
                persistent-hint
                density="comfortable"
              />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="comment" label="Bemerkung (optional)" density="comfortable" />
            </v-col>
          </v-row>
        </v-form>
        <v-alert v-if="error" type="error" variant="tonal" class="mt-2">{{ error }}</v-alert>
      </v-card-text>
      <v-card-actions>
        <v-btn v-if="colorRing" color="error" variant="text" :loading="deleting" @click="remove">
          Farbring entfernen
        </v-btn>
        <v-spacer />
        <v-btn variant="text" @click="emit('update:modelValue', false)">Abbrechen</v-btn>
        <v-btn color="primary" variant="elevated" :loading="saving" :disabled="!canSave" @click="save">
          Speichern
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import axios from 'axios';
import * as api from '@/api';
import { useColorRingsStore } from '@/stores/colorRings';
import type { ColorRing } from '@/types';
import ColorRingInput, { type ColorRingFormValue } from './ColorRingInput.vue';

const props = defineProps<{
  modelValue: boolean;
  colorRing?: ColorRing | null;
  // Metal ring of the bird being edited, if known
  lockedRing?: string | null;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
  (e: 'saved', value: ColorRing): void;
  (e: 'deleted'): void;
}>();

const store = useColorRingsStore();
const value = ref<ColorRingFormValue>({});
const metalRing = ref('');
const comment = ref('');
const saving = ref(false);
const deleting = ref(false);
const error = ref<string | null>(null);

watch(() => props.modelValue, (open) => {
  if (!open) return;
  const cr = props.colorRing;
  value.value = cr ? { ...cr } : {};
  metalRing.value = cr?.ring ?? props.lockedRing ?? '';
  comment.value = cr?.comment ?? '';
  error.value = null;
}, { immediate: true });

const canSave = computed(() => !!(value.value.ring_color && value.value.code));

const errorMessage = (e: unknown) =>
  axios.isAxiosError(e) ? e.response?.data?.detail ?? e.message : String(e);

const save = async () => {
  saving.value = true;
  error.value = null;
  const payload = {
    ring_color: value.value.ring_color!,
    text_color: value.value.text_color ?? null,
    code: value.value.code!,
    mark_type: (value.value.mark_type ?? null) as ColorRing['mark_type'],
    leg: (value.value.leg ?? null) as ColorRing['leg'],
    project: value.value.project ?? null,
    ring: metalRing.value.trim() || null,
    comment: comment.value.trim() || null,
  };
  try {
    const saved = props.colorRing
      ? await api.updateColorRing(props.colorRing.id, payload)
      : await api.createColorRing(payload);
    store.upsert(saved);
    emit('saved', saved);
    emit('update:modelValue', false);
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    saving.value = false;
  }
};

const remove = async () => {
  if (!props.colorRing) return;
  deleting.value = true;
  try {
    await api.deleteColorRing(props.colorRing.id);
    store.remove(props.colorRing.id);
    emit('deleted');
    emit('update:modelValue', false);
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    deleting.value = false;
  }
};
</script>
