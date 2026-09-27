<template>
  <div class="color-ring-input">
    <div class="d-flex align-center ga-3 mt-4">
      <v-card-subtitle class="px-0">Farbring (optional)</v-card-subtitle>
      <color-ring-badge v-if="preview" :color-ring="preview" size="small" />
    </div>
    <v-row dense>
      <v-col cols="12" sm="4">
        <v-select
          :model-value="modelValue.ring_color"
          :items="COLOR_PALETTE"
          item-title="label"
          item-value="key"
          label="Ringfarbe"
          density="comfortable"
          clearable
          @update:model-value="update('ring_color', $event)"
        >
          <template #selection="{ item }">
            <span class="swatch mr-2" :style="{ backgroundColor: item.raw.hex }"></span>{{ item.raw.label }}
          </template>
          <template #item="{ props: itemProps, item }">
            <v-list-item v-bind="itemProps">
              <template #prepend>
                <span class="swatch mr-3" :style="{ backgroundColor: item.raw.hex }"></span>
              </template>
            </v-list-item>
          </template>
        </v-select>
      </v-col>
      <v-col cols="12" sm="4">
        <v-select
          :model-value="modelValue.text_color"
          :items="COLOR_PALETTE"
          item-title="label"
          item-value="key"
          label="Schriftfarbe (optional)"
          density="comfortable"
          clearable
          @update:model-value="update('text_color', $event)"
        >
          <template #selection="{ item }">
            <span class="swatch mr-2" :style="{ backgroundColor: item.raw.hex }"></span>{{ item.raw.label }}
          </template>
          <template #item="{ props: itemProps, item }">
            <v-list-item v-bind="itemProps">
              <template #prepend>
                <span class="swatch mr-3" :style="{ backgroundColor: item.raw.hex }"></span>
              </template>
            </v-list-item>
          </template>
        </v-select>
      </v-col>
      <v-col cols="12" sm="4">
        <v-text-field
          :model-value="modelValue.code"
          label="Code"
          density="comfortable"
          :rules="[completeRule]"
          autocomplete="off"
          @update:model-value="update('code', $event)"
        >
          <template v-if="showSuggestions" #append-inner>
            <bird-suggestions :reading="suggestionQuery" @select="emit('select-suggestion', $event)" />
          </template>
        </v-text-field>
      </v-col>

      <template v-if="extended">
        <v-col cols="12" sm="4">
          <v-select
            :model-value="modelValue.mark_type"
            :items="MARK_TYPES"
            label="Markierungsart (optional)"
            density="comfortable"
            clearable
            @update:model-value="update('mark_type', $event)"
          />
        </v-col>
        <v-col cols="12" sm="4">
          <v-select
            :model-value="modelValue.leg"
            :items="LEGS"
            label="Bein (optional)"
            density="comfortable"
            clearable
            @update:model-value="update('leg', $event)"
          />
        </v-col>
        <v-col cols="12" sm="4">
          <v-text-field
            :model-value="modelValue.project"
            label="Projekt (optional)"
            placeholder="z.B. OAGSH Möwen"
            density="comfortable"
            @update:model-value="update('project', $event)"
          />
        </v-col>
      </template>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import BirdSuggestions from '@/components/birds/BirdSuggestions.vue';
import ColorRingBadge from './ColorRingBadge.vue';
import { COLOR_PALETTE, MARK_TYPES, LEGS, colorLabel, normalizeCode } from '@/utils/colorRings';
import type { SuggestionBird } from '@/types';

export interface ColorRingFormValue {
  ring_color?: string | null;
  text_color?: string | null;
  code?: string | null;
  mark_type?: string | null;
  leg?: string | null;
  project?: string | null;
}

const props = withDefaults(defineProps<{
  modelValue: ColorRingFormValue;
  // Also show mark type, leg and project (ringing form)
  extended?: boolean;
  showSuggestions?: boolean;
}>(), {
  extended: false,
  showSuggestions: false,
});

const emit = defineEmits<{
  (e: 'update:modelValue', value: ColorRingFormValue): void;
  (e: 'select-suggestion', value: SuggestionBird): void;
}>();

const update = (key: keyof ColorRingFormValue, value: string | null) => {
  const next = key === 'code' && value ? normalizeCode(value) : value || null;
  emit('update:modelValue', { ...props.modelValue, [key]: next });
};

const preview = computed(() =>
  props.modelValue.ring_color && props.modelValue.code ? props.modelValue : null
);

// A color ring is optional, but a started one must have color and code
const completeRule = () => {
  const { ring_color, code, text_color } = props.modelValue;
  if (!ring_color && !code && !text_color) return true;
  if (!ring_color) return 'Ringfarbe fehlt';
  if (!code) return 'Code fehlt';
  return true;
};

const suggestionQuery = computed(() =>
  [colorLabel(props.modelValue.ring_color), props.modelValue.code ?? '']
    .filter(Boolean)
    .join(' ')
);
</script>

<style scoped>
.swatch {
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  vertical-align: middle;
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.3);
  flex-shrink: 0;
}
</style>
