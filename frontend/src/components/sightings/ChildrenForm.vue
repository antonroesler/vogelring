<template>
  <div>
    <v-card-subtitle class="px-0 mt-4">Nachkommen</v-card-subtitle>
    <div v-for="(child, index) in children" :key="index" class="mb-3">
      <v-row>
        <v-col cols="6">
          <v-text-field
            v-model="child.ring"
            :label="`Kind ${index + 1} Ring`"
            density="comfortable"
          ></v-text-field>
        </v-col>
        <v-col cols="2">
          <v-select
            v-model="child.age"
            :items="ageOptions"
            label="Alter"
            density="comfortable"
          ></v-select>
        </v-col>
        <v-col cols="3">
          <v-select
            v-model="child.sex"
            :items="sexOptions"
            label="Geschlecht"
            density="comfortable"
          ></v-select>
        </v-col>
        <v-col cols="1">
          <v-btn
            icon="mdi-delete"
            variant="text"
            color="error"
            size="small"
            @click="removeChild(index)"
          ></v-btn>
        </v-col>
      </v-row>
    </div>
    
    <v-btn
      variant="outlined"
      prepend-icon="mdi-plus"
      @click="addChild"
      size="small"
    >
      Kind hinzufügen
    </v-btn>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { getSightingAgeOptions, getSightingSexOptions } from '@/utils/sightingCoding';

const emit = defineEmits<{
  'update:children': [children: Array<{ ring: string; age?: number; sex?: number }>];
}>();

// Children become Sightings, so they use the SIGHTING age/sex codes
// (previously this used the ringing age list — the source of the mixed-code bug).
const children = ref<Array<{ ring: string; age?: number; sex?: number }>>([]);
const ageOptions = getSightingAgeOptions();
const sexOptions = getSightingSexOptions();

const addChild = () => {
  children.value.push({ ring: '', age: undefined, sex: undefined });
  emit('update:children', children.value);
};

const removeChild = (index: number) => {
  children.value.splice(index, 1);
  emit('update:children', children.value);
};

watch(children, () => {
  emit('update:children', children.value);
}, { deep: true });
</script>
